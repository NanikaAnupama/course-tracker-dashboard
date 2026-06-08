"""Compute rich, real-time content-production metrics from the tracker workbook.

The freshness check in :mod:`data_source` only knows *when* the workbook last
changed. This module answers *what is actually inside it* — how many AI videos,
podcasts and study guides are done versus their targets, chapter-wise progress,
per-person daily output, course-page upload throughput, and so on.

Everything is recomputed from the freshly downloaded bytes on every run, so the
numbers in the Teams alert always reflect the latest state of the sheet. Each
sheet is parsed defensively: a malformed or missing sheet yields ``None`` for
that section rather than blowing up the whole report.

Sheet/column layouts mirror the dashboard parsers in ``app.py`` so the two stay
in agreement.
"""

from __future__ import annotations

import logging
import warnings
from datetime import datetime
from io import BytesIO
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

logger = logging.getLogger(__name__)

# Window used for "recent activity" callouts.
_RECENT_DAYS = 7


def _pct(done: float, total: float) -> float:
    """Safe percentage, rounded to one decimal."""
    return round((done / total) * 100, 1) if total else 0.0


def _num(series: "pd.Series") -> "pd.Series":
    """Coerce a column to numeric, treating junk ('N/A', blanks) as NaN."""
    return pd.to_numeric(series, errors="coerce")


def _find_sheet(xls: "pd.ExcelFile", *needles: str) -> Optional[str]:
    """Return the first sheet whose lower-cased name contains all needles."""
    for name in xls.sheet_names:
        low = name.lower()
        if all(n in low for n in needles):
            return name
    return None


# Rows whose first column holds these markers are pre-computed totals/summaries
# baked into the sheet (e.g. "The Status of the Project", "Total Number of
# Chapters"). They must be dropped before summing, or every figure doubles.
_SUMMARY_ROW_RE = r"status of the project|total"


def _drop_summary_rows(df: "pd.DataFrame", name_col: str) -> "pd.DataFrame":
    """Remove blank and pre-aggregated summary rows from a course-keyed sheet."""
    names = df[name_col].astype(str)
    is_summary = names.str.contains(_SUMMARY_ROW_RE, case=False, na=False)
    return df[df[name_col].notna() & ~is_summary].copy()


# --------------------------------------------------------------------------- #
# Per-sheet metric builders
# --------------------------------------------------------------------------- #

def _content_production(xls: "pd.ExcelFile") -> Optional[Dict[str, Any]]:
    """Main 'Original' sheet — AI videos / podcasts / study guides vs targets.

    Each unit requires one AI Video, one Podcast and one Study Guide, so the
    per-type target is the total number of units.
    """
    sheet = xls.sheet_names[0] if xls.sheet_names else None
    if sheet is None:
        return None
    df = pd.read_excel(xls, sheet_name=sheet, header=0)
    df.columns = df.columns.astype(str).str.strip()
    if "Number of Units" not in df.columns or "Course Name" not in df.columns:
        return None

    # Drop the baked-in "Status of the Project" totals rows before summing.
    df = _drop_summary_rows(df, "Course Name")

    for col in (
        "Number of Units",
        "Number of AI Videos",
        "Number of Podcasts",
        "Number of Study Guides",
        "Number of H5P Quizzes",
    ):
        if col in df.columns:
            df[col] = _num(df[col])

    active = df[df["Number of Units"].fillna(0) > 0].copy()
    if active.empty:
        return None

    units = int(active["Number of Units"].sum())
    videos = int(active.get("Number of AI Videos", 0).fillna(0).sum())
    podcasts = int(active.get("Number of Podcasts", 0).fillna(0).sum())
    guides = int(active.get("Number of Study Guides", 0).fillna(0).sum())
    quizzes = (
        int(active["Number of H5P Quizzes"].fillna(0).sum())
        if "Number of H5P Quizzes" in active.columns
        else None
    )

    total_required = units * 3
    total_done = videos + podcasts + guides
    # Courses that have produced nothing yet.
    not_started = int(
        (
            active.get("Number of AI Videos", 0).fillna(0)
            + active.get("Number of Podcasts", 0).fillna(0)
            + active.get("Number of Study Guides", 0).fillna(0)
        ).eq(0).sum()
    )

    result: Dict[str, Any] = {
        "active_courses": int(len(active)),
        "courses_not_started": not_started,
        "total_units": units,
        "ai_videos": {"done": videos, "total": units, "pct": _pct(videos, units)},
        "podcasts": {"done": podcasts, "total": units, "pct": _pct(podcasts, units)},
        "study_guides": {"done": guides, "total": units, "pct": _pct(guides, units)},
        "overall": {
            "done": total_done,
            "total": total_required,
            "pct": _pct(total_done, total_required),
        },
    }
    if quizzes is not None:
        result["h5p_quizzes_done"] = quizzes
    return result


def _chapters(xls: "pd.ExcelFile") -> Optional[Dict[str, Any]]:
    """'Chapter-count' sheet — chapters and chapter-wise AI videos done."""
    sheet = _find_sheet(xls, "chapter", "count")
    if sheet is None:
        return None
    df = pd.read_excel(xls, sheet_name=sheet, header=0)
    df.columns = df.columns.astype(str).str.strip()

    chap_col = next((c for c in df.columns if c.lower() == "number of chapters"), None)
    done_col = next(
        (c for c in df.columns if "chapter-wise ai video" in c.lower()), None
    )
    if chap_col is None or done_col is None:
        return None

    # Drop the baked-in "Total Number of Chapters" summary row before summing.
    name_col = next((c for c in df.columns if "course name" in c.lower()), None)
    if name_col is not None:
        df = _drop_summary_rows(df, name_col)

    chapters = int(_num(df[chap_col]).fillna(0).sum())
    videos_done = int(_num(df[done_col]).fillna(0).sum())

    result: Dict[str, Any] = {
        "total_chapters": chapters,
        "chapter_videos_done": videos_done,
        "pct": _pct(videos_done, chapters),
    }

    status_col = next(
        (c for c in df.columns if "course page" in c.lower() and "status" in c.lower()),
        None,
    )
    if status_col is not None:
        cleaned = df[status_col].dropna().astype(str).str.strip().str.lower()
        uploaded = int(cleaned.eq("uploaded").sum())
        pending = int(cleaned.str.contains("pend").sum())
        result["course_pages_uploaded"] = uploaded
        result["course_pages_pending"] = pending
    return result


def _video_log(xls: "pd.ExcelFile", now: "pd.Timestamp") -> Optional[Dict[str, Any]]:
    """'Chapter-wise AI video log' — per-event NotebookLM & WebTool throughput."""
    sheet = _find_sheet(xls, "chapter", "video", "log")
    if sheet is None:
        return None
    raw = pd.read_excel(xls, sheet_name=sheet, header=None)
    if raw.shape[0] <= 2:
        return None
    data = raw.iloc[2:].copy()

    cols = [
        "Date", "AwardingBody", "CourseName", "UnitNo", "ChapterNo",
        "NB_Person", "URL", "WT_Person", "AddedToFolder", "VimeoLink",
        "AddedToCoursePage",
    ]
    data = data.iloc[:, : len(cols)]
    data.columns = cols[: data.shape[1]]
    data["Date"] = pd.to_datetime(data["Date"], errors="coerce")
    data = data[data["Date"].notna()].copy()
    if data.empty:
        return None

    def _present(series: "pd.Series") -> "pd.Series":
        s = series.astype(str).str.strip().str.lower()
        return ~s.isin(("", "nan", "none"))

    nb = data[_present(data["URL"])].copy()
    wt = data[data["AddedToFolder"].astype(str).str.strip().str.lower().eq("yes")].copy()

    recent_cut = now - pd.Timedelta(days=_RECENT_DAYS)
    upper = now + pd.Timedelta(days=1)

    def _recent(frame: "pd.DataFrame") -> int:
        d = frame["Date"]
        return int(((d >= recent_cut) & (d <= upper)).sum())

    nb_people = (
        nb["NB_Person"].astype(str).str.strip().replace({"nan": None, "": None}).dropna()
    )
    # Only the single leading contributor is surfaced (team preference).
    top = [
        (str(name), int(count))
        for name, count in nb_people.value_counts().head(1).items()
    ]

    return {
        "notebooklm_done": int(len(nb)),
        "webtool_processed": int(len(wt)),
        "notebooklm_last_7_days": _recent(nb),
        "webtool_last_7_days": _recent(wt),
        "latest_date": data["Date"].max().strftime("%Y-%m-%d"),
        "top_contributors": top,
    }


def _daily_counts_metrics(
    df: "pd.DataFrame", value_cols: List[str], now: "pd.Timestamp"
) -> Dict[str, Any]:
    """Shared summariser for date-indexed daily-count sheets."""
    df = df.copy()
    for col in value_cols:
        df[col] = _num(df[col]).fillna(0)
    df["_total"] = df[value_cols].sum(axis=1)

    recent_cut = now - pd.Timedelta(days=_RECENT_DAYS)
    upper = now + pd.Timedelta(days=1)
    in_window = df[(df["Date"] >= recent_cut) & (df["Date"] <= upper)]

    busiest_idx = df["_total"].idxmax() if not df.empty else None
    busiest: Optional[Tuple[str, int]] = None
    if busiest_idx is not None and df.loc[busiest_idx, "_total"] > 0:
        busiest = (
            df.loc[busiest_idx, "Date"].strftime("%Y-%m-%d"),
            int(df.loc[busiest_idx, "_total"]),
        )

    return {
        "total": int(df["_total"].sum()),
        "last_7_days": int(in_window["_total"].sum()),
        "active_days": int((df["_total"] > 0).sum()),
        "latest_date": df["Date"].max().strftime("%Y-%m-%d") if not df.empty else None,
        "busiest_day": busiest,
    }


def _webtool_status(xls: "pd.ExcelFile", now: "pd.Timestamp") -> Optional[Dict[str, Any]]:
    """'WebtoolStatus' — daily WebTool upload counts per person."""
    sheet = _find_sheet(xls, "webtool", "status")
    if sheet is None:
        return None
    df = pd.read_excel(xls, sheet_name=sheet, header=1)
    df.columns = df.columns.astype(str).str.strip()
    if "Date" not in df.columns:
        return None
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df = df[df["Date"].notna()].copy()
    if df.empty:
        return None

    person_cols = [c for c in df.columns if c != "Date"]
    summary = _daily_counts_metrics(df, person_cols, now)
    per_person = {
        c: int(_num(df[c]).fillna(0).sum())
        for c in person_cols
        if int(_num(df[c]).fillna(0).sum()) > 0
    }
    summary["per_person"] = dict(
        sorted(per_person.items(), key=lambda kv: kv[1], reverse=True)
    )
    return summary


def _course_page(xls: "pd.ExcelFile", now: "pd.Timestamp") -> Optional[Dict[str, Any]]:
    """'Course Page Uploading Status' — daily chapter-wise videos uploaded."""
    sheet = _find_sheet(xls, "course", "page", "upload")
    if sheet is None:
        return None
    df = pd.read_excel(xls, sheet_name=sheet, header=1)
    df.columns = df.columns.astype(str).str.strip()
    if "Date" not in df.columns:
        return None
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df = df[df["Date"].notna()].copy()
    if df.empty:
        return None

    value_cols = [c for c in df.columns if c != "Date"]
    if not value_cols:
        return None
    return _daily_counts_metrics(df, value_cols[:1], now)


# --------------------------------------------------------------------------- #
# Public API
# --------------------------------------------------------------------------- #

def build_metrics(file_bytes: bytes) -> Dict[str, Any]:
    """Compute every sheet-specific metric block from the workbook bytes.

    Returns a JSON-serialisable dict. Sections that cannot be parsed are simply
    omitted, so callers should treat every key as optional.
    """
    metrics: Dict[str, Any] = {}
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            xls = pd.ExcelFile(BytesIO(file_bytes), engine="openpyxl")
    except Exception:  # pragma: no cover - corrupt/locked file
        logger.exception("Could not open workbook for metrics")
        return metrics

    now = pd.Timestamp(datetime.now())
    builders = {
        "content_production": lambda: _content_production(xls),
        "chapters": lambda: _chapters(xls),
        "video_log": lambda: _video_log(xls, now),
        "webtool_status": lambda: _webtool_status(xls, now),
        "course_page": lambda: _course_page(xls, now),
    }
    for key, builder in builders.items():
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                value = builder()
            if value:
                metrics[key] = value
        except Exception:
            logger.exception("Metric block %r failed; skipping", key)
    return metrics


# --------------------------------------------------------------------------- #
# Presentation helpers (used by the Teams card)
# --------------------------------------------------------------------------- #

def card_sections(metrics: Dict[str, Any]) -> List[Tuple[str, List[Tuple[str, str]]]]:
    """Turn the metrics dict into ordered (heading, [(label, value)]) sections.

    Only sections with data are returned, so the card stays compact when a
    sheet is missing.
    """
    sections: List[Tuple[str, List[Tuple[str, str]]]] = []

    cp = metrics.get("content_production")
    if cp:
        rows = [
            (
                "AI Videos",
                f"{cp['ai_videos']['done']}/{cp['ai_videos']['total']} ({cp['ai_videos']['pct']}%)",
            ),
            (
                "Podcasts",
                f"{cp['podcasts']['done']}/{cp['podcasts']['total']} ({cp['podcasts']['pct']}%)",
            ),
            (
                "Study Guides",
                f"{cp['study_guides']['done']}/{cp['study_guides']['total']} ({cp['study_guides']['pct']}%)",
            ),
            (
                "Overall content",
                f"{cp['overall']['done']}/{cp['overall']['total']} ({cp['overall']['pct']}%)",
            ),
            (
                "Courses",
                f"{cp['active_courses']} active · {cp['courses_not_started']} not started",
            ),
        ]
        if "h5p_quizzes_done" in cp:
            rows.append(("H5P quizzes", str(cp["h5p_quizzes_done"])))
        sections.append(("📦 Content production (Original)", rows))

    ch = metrics.get("chapters")
    if ch:
        rows = [
            (
                "Chapter-wise videos",
                f"{ch['chapter_videos_done']}/{ch['total_chapters']} ({ch['pct']}%)",
            ),
        ]
        if "course_pages_uploaded" in ch:
            rows.append(
                (
                    "Course pages",
                    f"{ch['course_pages_uploaded']} uploaded · {ch['course_pages_pending']} pending",
                )
            )
        sections.append(("📚 Chapter progress (Chapter-count)", rows))

    vl = metrics.get("video_log")
    if vl:
        rows = [
            (
                "NotebookLM videos",
                f"{vl['notebooklm_done']} total · {vl['notebooklm_last_7_days']} in 7d",
            ),
            (
                "WebTool processed",
                f"{vl['webtool_processed']} total · {vl['webtool_last_7_days']} in 7d",
            ),
            ("Latest entry", vl["latest_date"]),
        ]
        if vl.get("top_contributors"):
            name, count = vl["top_contributors"][0]
            rows.append(("Top contributor", f"{name} ({count})"))
        sections.append(("🎬 AI video log (live)", rows))

    ws = metrics.get("webtool_status")
    if ws:
        rows = [
            ("Total uploads", str(ws["total"])),
            ("Last 7 days", str(ws["last_7_days"])),
            ("Latest entry", str(ws.get("latest_date"))),
        ]
        if ws.get("per_person"):
            people = ", ".join(f"{n} ({c})" for n, c in list(ws["per_person"].items())[:3])
            rows.append(("By person", people))
        if ws.get("busiest_day"):
            rows.append(("Busiest day", f"{ws['busiest_day'][0]} ({ws['busiest_day'][1]})"))
        sections.append(("🌐 WebTool uploads (WebtoolStatus)", rows))

    cpg = metrics.get("course_page")
    if cpg:
        rows = [
            ("Videos uploaded", str(cpg["total"])),
            ("Last 7 days", str(cpg["last_7_days"])),
            ("Upload days", str(cpg["active_days"])),
            ("Latest entry", str(cpg.get("latest_date"))),
        ]
        if cpg.get("busiest_day"):
            rows.append(("Busiest day", f"{cpg['busiest_day'][0]} ({cpg['busiest_day'][1]})"))
        sections.append(("📤 Course page uploads", rows))

    return sections
