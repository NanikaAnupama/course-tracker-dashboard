"""Fetch the SharePoint workbook and determine data freshness.

Freshness strategy (as configured):
    1. Primary  -> the HTTP ``Last-Modified`` header of the downloaded file.
    2. Fallback -> the newest date cell found anywhere across the workbook sheets.

The module also builds a compact ``digest`` of recent activity that is later
handed to the LLM for analysis. Everything here is read-only and side-effect
free apart from the network GET.
"""

from __future__ import annotations

import logging
import warnings
from dataclasses import dataclass, field
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from io import BytesIO
from typing import Any, Dict, List, Optional

import httpx
import pandas as pd

from .config import MonitorConfig

logger = logging.getLogger(__name__)

# Sanity window for date cells — guards against garbage values (e.g. 1899
# Excel epoch artefacts or far-future typos) polluting the "latest update".
_MIN_VALID_YEAR = 2020
_MAX_VALID_YEAR = 2100


def _coerce_dates(column: "pd.Series") -> "pd.Series":
    """Parse a column to datetimes, returning only valid in-window values.

    We scan arbitrary columns whose format is unknown, so pandas emits a
    "Could not infer format" warning for each. That fallback is intentional —
    suppress the noise rather than spam the logs once per column.
    """
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        parsed = pd.to_datetime(column, errors="coerce").dropna()
    if parsed.empty:
        return parsed
    return parsed[(parsed.dt.year >= _MIN_VALID_YEAR) & (parsed.dt.year <= _MAX_VALID_YEAR)]


@dataclass
class DataStatus:
    """Result of a freshness check against the tracker workbook."""

    last_update: Optional[datetime]
    last_update_source: str  # "http-header" | "workbook-dates" | "unknown"
    days_inactive: Optional[float]
    is_stale: bool
    digest: Dict[str, Any] = field(default_factory=dict)
    checked_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


async def fetch_workbook(config: MonitorConfig) -> tuple[bytes, Optional[datetime]]:
    """Download the raw .xlsx bytes and parse the ``Last-Modified`` header.

    Returns:
        (file_bytes, last_modified_utc). ``last_modified_utc`` is ``None`` when
        SharePoint/CDN does not return a usable header.

    Raises:
        httpx.HTTPError: for network failures or non-2xx responses.
    """
    async with httpx.AsyncClient(
        timeout=config.http_timeout_seconds, follow_redirects=True
    ) as client:
        response = await client.get(config.sharepoint_url)
        response.raise_for_status()
        file_bytes = response.content

    last_modified = _parse_last_modified(response.headers.get("Last-Modified"))
    logger.info(
        "Fetched workbook: %d bytes, Last-Modified=%s",
        len(file_bytes),
        last_modified.isoformat() if last_modified else "n/a",
    )
    return file_bytes, last_modified


def _parse_last_modified(raw_header: Optional[str]) -> Optional[datetime]:
    """Parse an RFC 7231 ``Last-Modified`` header into a UTC datetime."""
    if not raw_header:
        return None
    try:
        parsed = parsedate_to_datetime(raw_header)
    except (TypeError, ValueError):
        return None
    if parsed is None:
        return None
    # Normalise naive datetimes to UTC.
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _latest_date_in_workbook(file_bytes: bytes) -> Optional[datetime]:
    """Scan every sheet for the newest plausible date cell.

    Header layouts vary between sheets, so we read each sheet without a header
    and coerce all columns to datetimes — robust to schema drift.
    """
    try:
        excel = pd.ExcelFile(BytesIO(file_bytes), engine="openpyxl")
    except Exception:  # pragma: no cover - corrupt/locked file
        logger.exception("Could not open workbook for date scanning")
        return None

    now = datetime.now(timezone.utc)
    latest: Optional[pd.Timestamp] = None

    for sheet_name in excel.sheet_names:
        try:
            frame = pd.read_excel(excel, sheet_name=sheet_name, header=None)
        except Exception:
            logger.warning("Skipping unreadable sheet %r", sheet_name)
            continue

        for column in frame.columns:
            valid = _coerce_dates(frame[column])
            if valid.empty:
                continue
            # Ignore future-dated rows (data-entry typos) beyond a day's grace.
            valid = valid[valid <= pd.Timestamp(now.replace(tzinfo=None)) + pd.Timedelta(days=1)]
            if valid.empty:
                continue
            sheet_max = valid.max()
            if latest is None or sheet_max > latest:
                latest = sheet_max

    if latest is None:
        return None
    return latest.to_pydatetime().replace(tzinfo=timezone.utc)


def build_data_digest(file_bytes: bytes) -> Dict[str, Any]:
    """Produce a compact, LLM-friendly summary of recent workbook activity.

    For each sheet we report row count, newest date, and how many rows landed
    in the last 7 days. Kept generic so it survives column renames.
    """
    digest: Dict[str, Any] = {"sheets": []}
    try:
        excel = pd.ExcelFile(BytesIO(file_bytes), engine="openpyxl")
    except Exception:  # pragma: no cover
        logger.exception("Could not open workbook for digest")
        return digest

    now = pd.Timestamp(datetime.now(timezone.utc).replace(tzinfo=None))
    seven_days_ago = now - pd.Timedelta(days=7)

    for sheet_name in excel.sheet_names:
        try:
            frame = pd.read_excel(excel, sheet_name=sheet_name, header=None)
        except Exception:
            continue

        # Best-effort: find the column with the most parseable dates.
        best_dates: Optional[pd.Series] = None
        for column in frame.columns:
            parsed = _coerce_dates(frame[column])
            if best_dates is None or len(parsed) > len(best_dates):
                best_dates = parsed

        sheet_summary: Dict[str, Any] = {
            "name": sheet_name,
            "rows": int(frame.shape[0]),
            "columns": int(frame.shape[1]),
        }
        if best_dates is not None and not best_dates.empty:
            recent = best_dates[best_dates >= seven_days_ago]
            sheet_summary["latest_date"] = best_dates.max().strftime("%Y-%m-%d")
            sheet_summary["rows_last_7_days"] = int(len(recent))
        else:
            sheet_summary["latest_date"] = None
            sheet_summary["rows_last_7_days"] = 0

        digest["sheets"].append(sheet_summary)

    return digest


async def get_data_status(config: MonitorConfig) -> DataStatus:
    """Fetch the workbook and compute a full freshness/inactivity status."""
    file_bytes, header_last_modified = await fetch_workbook(config)

    last_update = header_last_modified
    source = "http-header"
    if last_update is None:
        last_update = _latest_date_in_workbook(file_bytes)
        source = "workbook-dates" if last_update else "unknown"

    digest = build_data_digest(file_bytes)

    days_inactive: Optional[float] = None
    is_stale = False
    if last_update is not None:
        delta = datetime.now(timezone.utc) - last_update
        days_inactive = round(delta.total_seconds() / 86400.0, 2)
        is_stale = days_inactive > config.inactivity_threshold_days

    status = DataStatus(
        last_update=last_update,
        last_update_source=source,
        days_inactive=days_inactive,
        is_stale=is_stale,
        digest=digest,
    )
    logger.info(
        "Freshness: last_update=%s (%s), days_inactive=%s, stale=%s",
        last_update.isoformat() if last_update else "unknown",
        source,
        days_inactive,
        is_stale,
    )
    return status
