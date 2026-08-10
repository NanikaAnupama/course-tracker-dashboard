"""Data loading & feature engineering for the course tracker API.

All parsing logic is ported unchanged from the original Streamlit app
(app.py / textbook_progress.py) so every statistic stays identical —
only the presentation layer moved to React.
"""

from __future__ import annotations

import io
import logging
import re
import time
import threading

import numpy as np
import pandas as pd
import requests

TRACKER_URL = "https://globaledulinkuk-my.sharepoint.com/:x:/g/personal/sadeev_imperiallearning_co_uk/IQCgqczvPccERK5x-3fcBFPdAUsHzB0rMIahy7kRMz39xtU?download=1"
TEXTBOOK_URL = "https://globaledulinkuk-my.sharepoint.com/:x:/g/personal/sadeev_imperiallearning_co_uk/IQC_Trx-ci8SSozWqvstwuKwATXY7Xl96n-kik3FIVmhdRo?download=1"

CACHE_TTL_SECONDS = 300

log = logging.getLogger(__name__)

_cache: dict[str, tuple[float, object]] = {}
_cache_lock = threading.Lock()


def _cached(key: str, loader):
    now = time.time()
    with _cache_lock:
        hit = _cache.get(key)
        if hit and now - hit[0] < CACHE_TTL_SECONDS:
            return hit[1]
    value = loader()
    with _cache_lock:
        _cache[key] = (time.time(), value)
    return value


def clear_cache() -> None:
    with _cache_lock:
        _cache.clear()


def _download(url: str) -> bytes | None:
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code == 200:
            return response.content
        log.warning("download of %s returned HTTP %s", url, response.status_code)
        return None
    except Exception:
        log.exception("download of %s failed", url)
        return None


def get_tracker_bytes() -> bytes | None:
    return _cached("tracker_bytes", lambda: _download(TRACKER_URL))


def get_textbook_bytes() -> bytes | None:
    return _cached("textbook_bytes", lambda: _download(TEXTBOOK_URL))


# ── Main tracker sheet ──────────────────────────────────────────────

NUMERIC_COLS = ["Number of Units", "Number of AI Videos", "Number of Podcasts",
                "Number of Study Guides", "Number of H5P Quizzes"]
CONTENT_COLS = ["Number of AI Videos", "Number of Podcasts",
                "Number of Study Guides", "Number of H5P Quizzes"]


def _derive_name_from_link(link) -> str | None:
    """Best-effort course name from a southlondoncollege course URL slug."""
    if link is None or (isinstance(link, float) and np.isnan(link)):
        return None
    text = str(link).strip()
    m = re.search(r"/course/([^/?#]+)", text)
    if m is None:
        return None
    name = m.group(1).strip("-/").replace("-", " ").strip()
    return name.title() if name else None


def clean_and_preprocess(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = df.columns.str.strip()
    names = df["Course Name"].astype(str)
    df = df[~names.str.contains("Status of the Project", case=False, na=False)].copy()

    numeric_cols = [c for c in NUMERIC_COLS if c in df.columns]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # A row "carries data" when any production column holds a positive number.
    # Such rows must never be dropped, whatever else is wrong with them —
    # dropping one silently undercounts every total on the dashboard.
    carries_data = df[numeric_cols].fillna(0).sum(axis=1) > 0

    df["Data Issue"] = ""

    name_blank = df["Course Name"].isna() | (df["Course Name"].astype(str).str.strip() == "")
    for idx in df.index[name_blank & carries_data]:
        link = df.at[idx, "Course Link"] if "Course Link" in df.columns else None
        derived = _derive_name_from_link(link)
        df.at[idx, "Course Name"] = derived or f"Unnamed course (sheet row {idx + 2})"
        df.at[idx, "Data Issue"] = "Course name is blank in the tracker sheet"
    df = df[~name_blank | carries_data].copy()

    df["Course Name"] = df["Course Name"].astype(str).str.strip()
    df["Course Name"] = df["Course Name"].str.replace(r"^\n+", "", regex=True)
    df["Course Name"] = df["Course Name"].str.replace(r"\n+", " ", regex=True)
    df["Course Name"] = df["Course Name"].str.replace(r"\s+", " ", regex=True)

    # Rows with content counts but no unit count also survive (units become 0
    # so the completion maths stays defined) instead of vanishing.
    content_cols = [c for c in CONTENT_COLS if c in df.columns]
    units_ok = df["Number of Units"].notna() & (df["Number of Units"] > 0)
    has_content = df[content_cols].fillna(0).sum(axis=1) > 0
    broken_units = ~units_ok & has_content
    prior = df.loc[broken_units, "Data Issue"]
    df.loc[broken_units, "Data Issue"] = np.where(
        prior == "", "Number of Units is blank in the tracker sheet",
        prior + "; Number of Units is blank in the tracker sheet")
    df = df[units_ok | broken_units].copy()

    for col in content_cols:
        df[col] = df[col].fillna(0).astype(int)
    df["Number of Units"] = df["Number of Units"].fillna(0).clip(lower=0).astype(int)
    return df


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    df["Videos Completed"] = df["Number of AI Videos"]
    df["Podcasts Completed"] = df["Number of Podcasts"]
    df["Guides Completed"] = df["Number of Study Guides"]
    df["Total Required"] = df["Number of Units"] * 3
    df["Total Completed"] = df["Videos Completed"] + df["Podcasts Completed"] + df["Guides Completed"]
    df["Still Pending"] = (df["Total Required"] - df["Total Completed"]).clip(lower=0)
    df["Completion %"] = np.where(df["Total Required"] > 0, (df["Total Completed"] / df["Total Required"]) * 100, 0)
    df["Video %"] = np.where(df["Number of Units"] > 0, (df["Videos Completed"] / df["Number of Units"]) * 100, 0)
    df["Podcast %"] = np.where(df["Number of Units"] > 0, (df["Podcasts Completed"] / df["Number of Units"]) * 100, 0)
    df["Guide %"] = np.where(df["Number of Units"] > 0, (df["Guides Completed"] / df["Number of Units"]) * 100, 0)

    def get_status(row):
        pct = row["Completion %"]
        if row["Total Required"] == 0 and row["Total Completed"] > 0:
            return "In Progress"  # units unknown in the sheet, but work exists
        if pct == 0:
            return "Not Started"
        elif pct < 50:
            return "Early Stage"
        elif pct < 75:
            return "In Progress"
        elif pct < 100:
            return "Almost Done"
        return "Complete"

    df["Status"] = df.apply(get_status, axis=1)
    df["Priority Score"] = df["Number of Units"] * (100 - df["Completion %"])
    df["Course Level"] = df["Course Name"].str.extract(r"(Level \d+)", expand=False)
    df["Course Level"] = df["Course Level"].fillna("Other")

    def categorise_subject(title):
        title = str(title).lower()
        if any(w in title for w in ["business", "management", "accounting", "finance", "administration", "customer service"]):
            return "Business & Management"
        elif any(w in title for w in ["computing", "cyber", "web", "software", "data", "ai", "artificial", "digital", "networking"]):
            return "Computing & IT"
        elif any(w in title for w in ["health", "care", "nutrition", "dementia", "safeguarding", "diabetes", "autism", "mental health", "counselling", "adult care"]):
            return "Health & Social Care"
        elif any(w in title for w in ["teaching", "education", "child", "assessing", "learning", "early years", "playwork", "residential childcare"]):
            return "Education & Childcare"
        elif "law" in title:
            return "Law"
        elif any(w in title for w in ["sports", "fitness", "gym", "personal training", "leisure"]):
            return "Sports & Fitness"
        elif any(w in title for w in ["hospitality", "tourism"]):
            return "Hospitality & Tourism"
        return "Other Specialisations"

    df["Subject Area"] = df["Course Name"].apply(categorise_subject)

    def size_category(units):
        if units <= 3:
            return "Small (1-3 units)"
        elif units <= 7:
            return "Medium (4-7 units)"
        elif units <= 12:
            return "Large (8-12 units)"
        return "Very Large (13+ units)"

    df["Course Size"] = df["Number of Units"].apply(size_category)
    df["Videos Pending"] = (df["Number of Units"] - df["Videos Completed"]).clip(lower=0)
    df["Podcasts Pending"] = (df["Number of Units"] - df["Podcasts Completed"]).clip(lower=0)
    df["Guides Pending"] = (df["Number of Units"] - df["Guides Completed"]).clip(lower=0)
    return df


def get_courses_df() -> pd.DataFrame | None:
    def loader():
        raw = get_tracker_bytes()
        if raw is None:
            return None
        try:
            df = pd.read_excel(io.BytesIO(raw), engine="openpyxl")
            df = clean_and_preprocess(df)
            return engineer_features(df)
        except Exception:
            log.exception("failed to parse sheet")
            return None

    return _cached("courses_df", loader)


# ── Data-quality self-check ─────────────────────────────────────────
# The tracker sheet carries its own totals row ("The Status of the Project",
# a SUM over every data row). Comparing our computed totals against it every
# load catches any row the parser mishandles — and any formula drift in the
# sheet itself — the moment it happens, instead of silently showing wrong
# numbers.

_SUMMARY_LABELS = {
    "Number of Units": "Units",
    "Number of AI Videos": "AI Videos",
    "Number of Podcasts": "Podcasts",
    "Number of Study Guides": "Study Guides",
    "Number of H5P Quizzes": "H5P Quizzes",
}


def get_sheet_summary() -> dict | None:
    """The baked 'The Status of the Project' totals from the sheet itself."""

    def loader():
        raw = get_tracker_bytes()
        if raw is None:
            return None
        try:
            df = pd.read_excel(io.BytesIO(raw), engine="openpyxl")
            df.columns = df.columns.str.strip()
            names = df["Course Name"].astype(str)
            mask = names.str.contains("Status of the Project", case=False, na=False)
            mask &= ~names.str.contains("%", regex=False)
            if not mask.any():
                return None
            row = df[mask].iloc[0]
            out = {}
            for col in _SUMMARY_LABELS:
                if col in df.columns:
                    val = pd.to_numeric(row[col], errors="coerce")
                    if pd.notna(val):
                        out[col] = int(val)
            return out or None
        except Exception:
            log.exception("failed to parse sheet")
            return None

    return _cached("sheet_summary", loader)


def get_data_quality() -> dict:
    """Row-level issues plus a totals cross-check against the sheet's own SUM row."""
    issues: list[dict] = []
    mismatches: list[dict] = []

    df = get_courses_df()
    if df is not None and "Data Issue" in df.columns:
        flagged = df[df["Data Issue"] != ""]
        issues = [{"course": str(r["Course Name"]), "issue": str(r["Data Issue"])}
                  for _, r in flagged.iterrows()]

    summary = get_sheet_summary()
    if df is not None and summary:
        for col, label in _SUMMARY_LABELS.items():
            if col not in summary or col not in df.columns:
                continue
            computed = int(df[col].sum())
            if computed != summary[col]:
                mismatches.append({"metric": label, "dashboard": computed, "sheet": summary[col]})

    return {"issues": issues, "totalsMismatches": mismatches,
            "ok": not issues and not mismatches}

def get_video_log_daily() -> pd.DataFrame | None:
    """Daily NotebookLM video counts per person (URL present = complete)."""

    def loader():
        raw = get_tracker_bytes()
        if raw is None:
            return None
        try:
            xls = pd.ExcelFile(io.BytesIO(raw), engine="openpyxl")
            sheet_name = None
            for s in xls.sheet_names:
                if "chapter" in s.lower() and "video" in s.lower() and "log" in s.lower():
                    sheet_name = s
                    break
            if sheet_name is None:
                return None

            data = pd.read_excel(xls, sheet_name=sheet_name, header=None).iloc[2:].copy()
            col_names = ["Date", "AwardingBody", "CourseName", "UnitNo", "ChapterNo",
                         "NB_Person", "URL", "WT_Person", "AddedToFolder", "VimeoLink", "AddedToCoursePage"]
            if len(data.columns) >= len(col_names):
                data = data.iloc[:, :len(col_names)]
                data.columns = col_names
            else:
                for i in range(len(data.columns), len(col_names)):
                    data[col_names[i]] = np.nan
                data.columns = col_names[:len(data.columns)] + col_names[len(data.columns):]

            data["Date"] = pd.to_datetime(data["Date"], errors="coerce")
            data = data[data["Date"].notna()].copy()
            if data.empty:
                return pd.DataFrame(columns=["Date", "Person", "Videos"])

            # Fix wrong year (entries typed as 2025 belong to 2026)
            mask_2025 = data["Date"].dt.year == 2025
            if mask_2025.any():
                data.loc[mask_2025, "Date"] = data.loc[mask_2025, "Date"].apply(lambda d: d.replace(year=2026))

            data["NB_Person"] = data["NB_Person"].astype(str).str.strip().replace("nan", np.nan)
            nb = data[(data["NB_Person"].notna())
                      & (data["URL"].notna())
                      & (data["URL"].astype(str).str.strip() != "")
                      & (data["URL"].astype(str).str.strip().str.lower() != "nan")].copy()
            daily = nb.groupby(["Date", "NB_Person"]).size().reset_index(name="Videos")
            daily.rename(columns={"NB_Person": "Person"}, inplace=True)
            return daily
        except Exception:
            log.exception("failed to parse sheet")
            return None

    return _cached("nb_daily", loader)


# ── WebtoolStatus sheet ─────────────────────────────────────────────

def get_webtool_daily() -> pd.DataFrame | None:
    def loader():
        raw = get_tracker_bytes()
        if raw is None:
            return None
        try:
            xls = pd.ExcelFile(io.BytesIO(raw), engine="openpyxl")
            sheet_name = None
            for s in xls.sheet_names:
                if "webtool" in s.lower() and "status" in s.lower():
                    sheet_name = s
                    break
            if sheet_name is None:
                return None

            df = pd.read_excel(xls, sheet_name=sheet_name, header=1)
            df.columns = df.columns.astype(str).str.strip()
            if "Date" not in df.columns:
                return None
            df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
            df = df[df["Date"].notna()].copy()

            person_cols = [c for c in df.columns if c != "Date"]
            for col in person_cols:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

            long_df = df.melt(id_vars=["Date"], value_vars=person_cols,
                              var_name="Person", value_name="Videos")

            active_dates = long_df.groupby("Date")["Videos"].sum()
            active_dates = active_dates[active_dates > 0].index
            long_df = long_df[long_df["Date"].isin(active_dates)].copy()

            person_totals = long_df.groupby("Person")["Videos"].sum()
            active_persons = person_totals[person_totals > 0].index
            long_df = long_df[long_df["Person"].isin(active_persons)].copy()
            return long_df
        except Exception:
            log.exception("failed to parse sheet")
            return None

    return _cached("wt_daily", loader)


# ── Course Page Uploading Status sheet ─────────────────────────────
# Layout (since Jul 2026): a header row with "Date" followed by one column
# per person (e.g. Date | Piyumi | Rukaiya), daily counts underneath.

def get_course_page_daily() -> pd.DataFrame | None:
    def loader():
        raw = get_tracker_bytes()
        if raw is None:
            return None
        try:
            xls = pd.ExcelFile(io.BytesIO(raw), engine="openpyxl")
            sheet_name = None
            for s in xls.sheet_names:
                sl = s.lower()
                if "course" in sl and "page" in sl and ("upload" in sl or "uploading" in sl):
                    sheet_name = s
                    break
            if sheet_name is None:
                return None

            # Find the header row containing "Date" (sheet has a blank first row).
            probe = pd.read_excel(xls, sheet_name=sheet_name, header=None, nrows=5)
            header_row = None
            for i in range(len(probe)):
                if any(str(v).strip().lower() == "date" for v in probe.iloc[i]):
                    header_row = i
                    break
            if header_row is None:
                return None

            df = pd.read_excel(xls, sheet_name=sheet_name, header=header_row)
            df.columns = df.columns.astype(str).str.strip()
            if "Date" not in df.columns:
                return None
            df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
            df = df[df["Date"].notna()].copy()

            person_cols = [c for c in df.columns
                           if c != "Date" and not c.lower().startswith("unnamed")]
            if not person_cols:
                return None
            for col in person_cols:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

            long_df = df.melt(id_vars=["Date"], value_vars=person_cols,
                              var_name="Person", value_name="Count")

            # Keep only days where at least one person uploaded something,
            # but keep every named person (a new starter with 0 total still shows).
            active_dates = long_df.groupby("Date")["Count"].sum()
            active_dates = active_dates[active_dates > 0].index
            long_df = long_df[long_df["Date"].isin(active_dates)].copy()
            return long_df.sort_values("Date").reset_index(drop=True)
        except Exception:
            log.exception("failed to parse sheet")
            return None

    return _cached("cp_daily", loader)


# ── Content Production sheet (Production Workstreams) ──────────────
# Layout: Date | "<Workstream> Completed" | "Done By" | ... repeated per
# workstream. Multiple people on one date appear as extra rows with the
# date cell merged (blank on continuation rows) → forward-fill the date.

def get_content_production() -> pd.DataFrame | None:
    def loader():
        raw = get_tracker_bytes()
        if raw is None:
            return None
        try:
            xls = pd.ExcelFile(io.BytesIO(raw), engine="openpyxl")
            sheet_name = None
            for s in xls.sheet_names:
                if "content" in s.lower() and "production" in s.lower():
                    sheet_name = s
                    break
            if sheet_name is None:
                return None

            df = pd.read_excel(xls, sheet_name=sheet_name, header=0)
            df.columns = df.columns.astype(str).str.strip()
            if "Date" not in df.columns:
                return None

            # Merged date cells come through as NaN on continuation rows.
            df["Date"] = pd.to_datetime(df["Date"], errors="coerce").ffill()
            df = df[df["Date"].notna()].copy()

            # Pair each "<Workstream> Completed" column with the "Done By"
            # column immediately to its right.
            cols = list(df.columns)
            records = []
            column_order = []
            for i, col in enumerate(cols):
                if not col.lower().endswith("completed"):
                    continue
                name = re.sub(r"\s*completed\s*$", "", col, flags=re.I).strip()
                name = re.sub(r"\bquizes\b", "Quizzes", name, flags=re.I)
                column_order.append(name)
                person_col = None
                if i + 1 < len(cols) and cols[i + 1].lower().startswith("done by"):
                    person_col = cols[i + 1]

                counts = pd.to_numeric(df[col], errors="coerce")
                # pandas 2 turns a blank cell into the string "nan" here while
                # pandas 3 keeps it as NA — fill first so both give "".
                persons = (df[person_col].astype(str).str.strip().fillna("")
                           if person_col is not None else pd.Series("", index=df.index))
                for date, count, person in zip(df["Date"], counts, persons):
                    if pd.isna(count) or count <= 0:
                        continue
                    person = "" if pd.isna(person) else str(person).strip()
                    p = person if person.lower() not in ("nan", "none", "") else "Unassigned"
                    records.append({"Date": date, "Workstream": name, "Person": p, "Count": int(count)})

            long_df = (pd.DataFrame(records)
                       .groupby(["Date", "Workstream", "Person"], as_index=False)["Count"].sum()
                       .sort_values("Date").reset_index(drop=True)
                       if records else
                       pd.DataFrame(columns=["Date", "Workstream", "Person", "Count"]))
            long_df.attrs["workstream_order"] = column_order
            return long_df
        except Exception:
            log.exception("failed to parse sheet")
            return None

    return _cached("content_production", loader)


# ── Textbook tracker ────────────────────────────────────────────────

def get_textbook_df() -> pd.DataFrame | None:
    def loader():
        raw = get_textbook_bytes()
        if raw is None:
            return None
        try:
            df = pd.read_excel(io.BytesIO(raw), sheet_name="DashboardSheet")
        except Exception:
            log.exception("failed to parse sheet")
            return None
        try:
            df.columns = ["Course Name", "Course Link", "Units", "Pages",
                          "Estimation", "Cost to Print", "Price", "Status"]
            df.drop(columns=["Estimation"], inplace=True)

            df["Cost to Print"] = (
                df["Cost to Print"].astype(str)
                .str.replace("£", "", regex=False)
                .str.replace(",", "", regex=False)
                .str.strip()
            )
            df["Cost to Print"] = pd.to_numeric(df["Cost to Print"], errors="coerce")

            def map_status(s):
                if pd.isna(s) or str(s).strip() in ("", "None"):
                    return "No Textbook"
                s = str(s).strip()
                if s in ("Completed", "Done"):
                    return "Textbook Ready"
                return "In Progress"

            df["Textbook Status"] = df["Status"].apply(map_status)
            df["Level"] = df["Course Name"].apply(
                lambda x: int(m.group(1)) if (m := re.search(r"Level (\d+)", str(x))) else None
            )

            def get_type(name):
                name = str(name)
                for t in ["Extended Diploma", "Diploma", "Certificate", "Award"]:
                    if t in name:
                        return t
                return "Other"

            df["Qualification"] = df["Course Name"].apply(get_type)
            return df
        except Exception:
            log.exception("failed to parse sheet")
            return None

    return _cached("textbook_df", loader)
