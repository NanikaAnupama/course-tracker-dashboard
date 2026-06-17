"""Persist each report's key figures and compute change vs the previous report.

Because the monitor runs on ephemeral GitHub Actions runners, the only way to
say "how much did this change since the last message?" is to durably store a
snapshot of the numbers we sent last time. After every report we flatten the
headline metrics into a small JSON file (``last_report_snapshot.json``); the
GitHub Actions workflow then commits that file back to the repo so the *next*
scheduled run (the following Monday or Friday) can read it and diff against it.

The comparison therefore always measures the current figures against the last
report that was actually sent — Friday vs Monday, Monday vs the previous Friday.
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Ordered, human-labelled set of headline figures we track over time. Each entry
# is (flat_key, label, is_pct). ``is_pct`` metrics are already percentages, so a
# change between reports is expressed in percentage *points* rather than a "% of
# a %". Everything else is a cumulative count, shown with a true % change.
KEY_METRICS: List[Tuple[str, str, bool]] = [
    ("content_overall_done", "Overall content done", False),
    ("content_overall_pct", "Overall completion", True),
    ("content_ai_videos_done", "AI videos done", False),
    ("content_podcasts_done", "Podcasts done", False),
    ("content_study_guides_done", "Study guides done", False),
    ("chapter_videos_done", "Chapter-wise videos done", False),
    ("course_pages_uploaded", "Course pages uploaded", False),
    ("notebooklm_done", "NotebookLM videos", False),
    ("webtool_processed", "WebTool processed", False),
    ("webtool_uploads_total", "WebTool uploads (total)", False),
    ("course_page_uploads_total", "Course-page video uploads", False),
]


@dataclass
class MetricChange:
    """One headline figure compared against the previous report."""

    key: str
    label: str
    current: float
    previous: Optional[float]
    is_pct: bool


@dataclass
class ReportComparison:
    """All headline changes plus a label for when the baseline was captured."""

    changes: List[MetricChange] = field(default_factory=list)
    previous_label: Optional[str] = None  # e.g. "Mon 15 Jun, 12:45 IST"
    has_baseline: bool = False


def flatten_metrics(metrics: Dict[str, Any]) -> Dict[str, float]:
    """Reduce the nested metrics dict to the flat number-only set we track.

    Sections or fields that a given workbook does not provide are simply left
    out, so callers must treat every key as optional.
    """
    flat: Dict[str, Optional[float]] = {}

    cp = metrics.get("content_production") or {}
    if cp:
        overall = cp.get("overall") or {}
        flat["content_overall_done"] = overall.get("done")
        flat["content_overall_pct"] = overall.get("pct")
        flat["content_ai_videos_done"] = (cp.get("ai_videos") or {}).get("done")
        flat["content_podcasts_done"] = (cp.get("podcasts") or {}).get("done")
        flat["content_study_guides_done"] = (cp.get("study_guides") or {}).get("done")

    ch = metrics.get("chapters") or {}
    if ch:
        flat["chapter_videos_done"] = ch.get("chapter_videos_done")
        flat["course_pages_uploaded"] = ch.get("course_pages_uploaded")

    vl = metrics.get("video_log") or {}
    if vl:
        flat["notebooklm_done"] = vl.get("notebooklm_done")
        flat["webtool_processed"] = vl.get("webtool_processed")

    ws = metrics.get("webtool_status") or {}
    if ws:
        flat["webtool_uploads_total"] = ws.get("total")

    cpg = metrics.get("course_page") or {}
    if cpg:
        flat["course_page_uploads_total"] = cpg.get("total")

    return {k: float(v) for k, v in flat.items() if v is not None}


def load_snapshot(path: str) -> Optional[Dict[str, Any]]:
    """Load the previous report snapshot, or ``None`` if absent/unreadable."""
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
        return data if isinstance(data, dict) else None
    except (OSError, json.JSONDecodeError):
        logger.warning("Could not read report snapshot at %s", path, exc_info=True)
        return None


def save_snapshot(path: str, flat_metrics: Dict[str, float], model: str) -> None:
    """Write the current report's figures so the next run can diff against them."""
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "metrics": flat_metrics,
        "model": model,
    }
    try:
        directory = os.path.dirname(path)
        if directory:
            os.makedirs(directory, exist_ok=True)
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True)
        logger.info("Saved report snapshot to %s", path)
    except OSError:
        logger.warning("Could not write report snapshot to %s", path, exc_info=True)


def _format_previous_label(raw: Optional[str], timezone_name: str) -> Optional[str]:
    """Render a stored UTC timestamp in the report timezone, e.g. 'Mon 15 Jun, 12:45'."""
    if not raw:
        return None
    try:
        dt = datetime.fromisoformat(raw)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    label_tz = ""
    try:
        from zoneinfo import ZoneInfo

        dt = dt.astimezone(ZoneInfo(timezone_name))
        # Short, recognisable suffix for the few timezones we actually use.
        label_tz = {"Asia/Kolkata": " IST", "UTC": " UTC"}.get(timezone_name, "")
    except Exception:  # pragma: no cover - missing tzdata, bad name
        pass
    return dt.strftime("%a %d %b, %H:%M") + label_tz


def build_comparison(
    current_flat: Dict[str, float],
    previous_snapshot: Optional[Dict[str, Any]],
    timezone_name: str = "UTC",
) -> ReportComparison:
    """Compare the current figures against the previous report's snapshot."""
    snapshot = previous_snapshot or {}
    previous_metrics = snapshot.get("metrics") or {}
    has_baseline = bool(previous_metrics)

    changes: List[MetricChange] = []
    for key, label, is_pct in KEY_METRICS:
        if key not in current_flat:
            continue
        previous = previous_metrics.get(key)
        changes.append(
            MetricChange(
                key=key,
                label=label,
                current=current_flat[key],
                previous=float(previous) if isinstance(previous, (int, float)) else None,
                is_pct=is_pct,
            )
        )

    return ReportComparison(
        changes=changes,
        previous_label=_format_previous_label(snapshot.get("generated_at"), timezone_name),
        has_baseline=has_baseline,
    )


def _fmt_num(value: float) -> str:
    """Drop a trailing '.0' so counts read as integers but ratios keep a decimal."""
    if float(value).is_integer():
        return str(int(value))
    return f"{value:.1f}"


def format_change(change: MetricChange) -> str:
    """Build the display string for one metric, e.g. '120 → 135 (+15, +12.5%)'."""
    current = _fmt_num(change.current)

    if change.previous is None:
        # No comparable figure last time (new metric or first report).
        suffix = "%" if change.is_pct else ""
        return f"{current}{suffix} (no prior value)"

    previous = _fmt_num(change.previous)
    delta = change.current - change.previous
    sign = "▲" if delta > 0 else ("▼" if delta < 0 else "▬")

    if change.is_pct:
        # Percentage metric: report the change in percentage points.
        return f"{previous}% → {current}% ({sign} {delta:+.1f} pts)"

    if change.previous == 0:
        # Can't take a % change from zero; show the absolute jump only.
        return f"{previous} → {current} ({sign} {delta:+.0f})"

    pct = (delta / change.previous) * 100
    return f"{previous} → {current} ({sign} {delta:+.0f}, {pct:+.1f}%)"
