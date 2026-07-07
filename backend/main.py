"""FastAPI backend for the Course Content Production Dashboard.

Serves the same statistics as the original Streamlit app as JSON, and hosts
the inactivity monitor scheduler in-process (unchanged package) so the
Railway deployment keeps its existing Teams-alert behaviour.
"""

from __future__ import annotations

import os
from contextlib import asynccontextmanager

import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from backend import data

try:  # optional, mirrors python -m inactivity_monitor
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass


def _monitor_enabled() -> bool:
    return os.getenv("ENABLE_INACTIVITY_MONITOR", "1").lower() not in ("0", "false", "no")


@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler = None
    if _monitor_enabled():
        try:
            import asyncio

            from inactivity_monitor.config import MonitorConfig
            from inactivity_monitor.scheduler import create_scheduler, run_inactivity_check

            config = MonitorConfig.from_env()
            scheduler = create_scheduler(config)
            scheduler.start()
            app.state.inactivity_scheduler = scheduler

            # Match `python -m inactivity_monitor`: kick off one check at boot
            # (it only alerts when the data is stale).
            async def _initial_check():
                try:
                    await run_inactivity_check(config)
                except Exception:
                    pass

            asyncio.create_task(_initial_check())
        except Exception as exc:  # missing env vars must not take the API down
            print(f"[inactivity_monitor] not started: {exc}")
    try:
        yield
    finally:
        if scheduler is not None and scheduler.running:
            scheduler.shutdown(wait=False)


app = FastAPI(title="Course Tracker API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _require_courses() -> pd.DataFrame:
    df = data.get_courses_df()
    if df is None:
        raise HTTPException(status_code=503, detail="Tracker sheet could not be downloaded from SharePoint.")
    return df


def _round(v, nd=1):
    return round(float(v), nd)


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/refresh")
def refresh():
    data.clear_cache()
    return {"status": "cache cleared"}


@app.get("/api/overview")
def overview():
    df = _require_courses()
    total_units = int(df["Number of Units"].sum())
    total_required = int(df["Total Required"].sum())
    total_completed = int(df["Total Completed"].sum())
    videos_done = int(df["Videos Completed"].sum())
    podcasts_done = int(df["Podcasts Completed"].sum())
    guides_done = int(df["Guides Completed"].sum())
    h5p_done = int(df["Number of H5P Quizzes"].sum()) if "Number of H5P Quizzes" in df.columns else 0
    complete_courses = int((df["Completion %"] == 100).sum())
    not_started = int((df["Completion %"] == 0).sum())

    status_order = ["Not Started", "Early Stage", "In Progress", "Almost Done", "Complete"]
    counts = df["Status"].value_counts()
    status_breakdown = [{"status": s, "count": int(counts.get(s, 0))} for s in status_order if counts.get(s, 0) > 0]

    content_types = [
        {"name": "AI Videos", "done": videos_done, "pending": total_units - videos_done, "required": total_units},
        {"name": "Podcasts", "done": podcasts_done, "pending": total_units - podcasts_done, "required": total_units},
        {"name": "Study Guides", "done": guides_done, "pending": total_units - guides_done, "required": total_units},
    ]
    for ct in content_types:
        ct["pct"] = _round(ct["done"] / ct["required"] * 100) if ct["required"] else 0

    return {
        "totalCourses": int(len(df)),
        "totalUnits": total_units,
        "totalRequired": total_required,
        "totalCompleted": total_completed,
        "totalPending": total_required - total_completed,
        "overallCompletion": _round(total_completed / total_required * 100) if total_required else 0,
        "videosDone": videos_done,
        "podcastsDone": podcasts_done,
        "guidesDone": guides_done,
        "h5pDone": h5p_done,
        "completeCourses": complete_courses,
        "notStartedCourses": not_started,
        "inProgressCourses": int(len(df)) - complete_courses - not_started,
        "statusBreakdown": status_breakdown,
        "contentTypes": content_types,
    }


@app.get("/api/courses")
def courses():
    df = _require_courses()
    out = []
    for _, r in df.iterrows():
        out.append({
            "name": r["Course Name"],
            "level": r["Course Level"],
            "subject": r["Subject Area"],
            "size": r["Course Size"],
            "units": int(r["Number of Units"]),
            "status": r["Status"],
            "pct": _round(r["Completion %"]),
            "videosDone": int(r["Videos Completed"]),
            "podcastsDone": int(r["Podcasts Completed"]),
            "guidesDone": int(r["Guides Completed"]),
            "videosPending": int(r["Videos Pending"]),
            "podcastsPending": int(r["Podcasts Pending"]),
            "guidesPending": int(r["Guides Pending"]),
            "pending": int(r["Still Pending"]),
            "required": int(r["Total Required"]),
            "priorityScore": _round(r["Priority Score"]),
        })
    return out


@app.get("/api/subjects")
def subjects():
    df = _require_courses()
    agg = df.groupby("Subject Area").agg(
        courses=("Course Name", "count"),
        units=("Number of Units", "sum"),
        completed=("Total Completed", "sum"),
        required=("Total Required", "sum"),
        avgPct=("Completion %", "mean"),
        videosPending=("Videos Pending", "sum"),
        podcastsPending=("Podcasts Pending", "sum"),
        guidesPending=("Guides Pending", "sum"),
    ).reset_index()
    out = []
    for _, r in agg.iterrows():
        out.append({
            "name": r["Subject Area"],
            "courses": int(r["courses"]),
            "units": int(r["units"]),
            "completed": int(r["completed"]),
            "required": int(r["required"]),
            "pending": int(r["required"] - r["completed"]),
            "avgPct": _round(r["avgPct"]),
            "videosPending": int(r["videosPending"]),
            "podcastsPending": int(r["podcastsPending"]),
            "guidesPending": int(r["guidesPending"]),
        })
    return out


@app.get("/api/levels")
def levels():
    df = _require_courses()
    agg = df.groupby("Course Level").agg(
        courses=("Course Name", "count"),
        units=("Number of Units", "sum"),
        completed=("Total Completed", "sum"),
        required=("Total Required", "sum"),
        avgPct=("Completion %", "mean"),
        videosPending=("Videos Pending", "sum"),
        podcastsPending=("Podcasts Pending", "sum"),
        guidesPending=("Guides Pending", "sum"),
    ).reset_index()
    order = ["Level 1", "Level 2", "Level 3", "Level 4", "Level 5", "Level 6", "Level 7", "Other"]
    agg["__o"] = agg["Course Level"].apply(lambda x: order.index(x) if x in order else 99)
    agg = agg.sort_values("__o")
    out = []
    for _, r in agg.iterrows():
        out.append({
            "name": r["Course Level"],
            "courses": int(r["courses"]),
            "units": int(r["units"]),
            "completed": int(r["completed"]),
            "required": int(r["required"]),
            "pending": int(r["required"] - r["completed"]),
            "avgPct": _round(r["avgPct"]),
            "videosPending": int(r["videosPending"]),
            "podcastsPending": int(r["podcastsPending"]),
            "guidesPending": int(r["guidesPending"]),
        })
    return out


@app.get("/api/video-log")
def video_log():
    def serialize_person_daily(df):
        if df is None or df.empty:
            return []
        return [
            {"date": d.strftime("%Y-%m-%d"), "person": p, "videos": int(v)}
            for d, p, v in zip(df["Date"], df["Person"], df["Videos"])
        ]

    nb = data.get_video_log_daily()
    wt = data.get_webtool_daily()
    cp = data.get_course_page_daily()

    cp_rows = []
    if cp is not None and not cp.empty:
        cp_rows = [
            {"date": d.strftime("%Y-%m-%d"), "person": p, "count": int(c)}
            for d, p, c in zip(cp["Date"], cp["Person"], cp["Count"])
        ]

    return {
        "notebooklm": serialize_person_daily(nb),
        "webtool": serialize_person_daily(wt),
        "coursePage": cp_rows,
    }


@app.get("/api/workstreams")
def workstreams():
    df = data.get_content_production()
    if df is None:
        raise HTTPException(status_code=503, detail="Content Production sheet could not be downloaded from SharePoint.")
    rows = [
        {"date": d.strftime("%Y-%m-%d"), "workstream": w, "person": p, "count": int(c)}
        for d, w, p, c in zip(df["Date"], df["Workstream"], df["Person"], df["Count"])
    ]
    # Sheet column order (falls back to appearance order for old cached frames).
    order = df.attrs.get("workstream_order") or []
    for r in rows:
        if r["workstream"] not in order:
            order.append(r["workstream"])
    return {"workstreams": order, "daily": rows}


@app.get("/api/textbooks")
def textbooks():
    df = data.get_textbook_df()
    if df is None:
        raise HTTPException(status_code=503, detail="Textbook sheet could not be downloaded from SharePoint.")
    out = []
    for _, r in df.iterrows():
        out.append({
            "name": r["Course Name"],
            "link": None if pd.isna(r["Course Link"]) else str(r["Course Link"]),
            "units": None if pd.isna(r["Units"]) else int(r["Units"]),
            "pages": None if pd.isna(r["Pages"]) else int(r["Pages"]),
            "costToPrint": None if pd.isna(r["Cost to Print"]) else float(r["Cost to Print"]),
            "price": None if pd.isna(r["Price"]) else float(r["Price"]),
            "status": r["Textbook Status"],
            "level": None if pd.isna(r["Level"]) else int(r["Level"]),
            "qualification": r["Qualification"],
        })
    return out
