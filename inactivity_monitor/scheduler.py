"""Pipeline orchestration and the 60-minute background scheduler.

Public entry points:
    * ``run_inactivity_check``  – run the full check-once pipeline.
    * ``create_scheduler``      – build a configured AsyncIOScheduler.
    * ``register_with_fastapi`` – wire start/stop into a FastAPI app.
    * ``build_lifespan``        – modern FastAPI ``lifespan`` alternative.
"""

from __future__ import annotations

import logging
from typing import Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from .analytics import synthesise_analysis
from .config import MonitorConfig
from .data_source import DataStatus, get_data_status
from .snapshot import (
    ReportComparison,
    build_comparison,
    flatten_metrics,
    load_snapshot,
    save_snapshot,
)
from .teams import build_adaptive_card, send_teams_alert

logger = logging.getLogger(__name__)

_ALARM_JOB_ID = "inactivity_check"
_REPORT_JOB_ID = "daily_report"


async def _analyse_and_send(
    config: MonitorConfig,
    status: DataStatus,
    *,
    report_mode: bool,
    comparison: Optional[ReportComparison] = None,
) -> bool:
    """Run the LLM analysis and post the resulting card to Teams.

    Returns ``True`` when Teams accepted the card. ``comparison`` (report mode
    only) injects the change-since-last-report section.
    """
    analysis = await synthesise_analysis(config, status, report_mode=report_mode)
    payload = build_adaptive_card(
        status, analysis, report_mode=report_mode, comparison=comparison
    )
    return await send_teams_alert(config, payload)


async def run_inactivity_check(config: MonitorConfig) -> DataStatus:
    """Execute the full pipeline once: fetch → evaluate → (analyse → alert).

    The LLM + Teams steps only run when the data is stale. Returns the
    ``DataStatus`` so callers can inspect the outcome (handy for tests and
    for an on-demand FastAPI endpoint).
    """
    try:
        status = await get_data_status(config)
    except Exception:  # network/parse errors shouldn't kill the scheduler
        logger.exception("Inactivity check failed while fetching data status")
        raise

    if not status.is_stale:
        logger.info(
            "Data is fresh (%.2f day(s) <= %.2f threshold); no alert sent.",
            status.days_inactive if status.days_inactive is not None else -1,
            config.inactivity_threshold_days,
        )
        return status

    logger.warning(
        "Data is STALE (%.2f day(s) > %.2f threshold); triggering analysis pipeline.",
        status.days_inactive if status.days_inactive is not None else -1,
        config.inactivity_threshold_days,
    )

    await _analyse_and_send(config, status, report_mode=False)
    return status


async def run_daily_report(config: MonitorConfig) -> DataStatus:
    """Generate and send the scheduled analytics digest — always sends.

    Runs on a fixed schedule (Mon & Fri) and posts a report to Teams regardless
    of whether the data is stale. Each report carries the % change since the
    previously sent report, then persists its own figures as the new baseline so
    the next run (the following Mon/Fri) can diff against them.
    """
    try:
        status = await get_data_status(config)
    except Exception:
        logger.exception("Daily report failed while fetching data status")
        raise

    current_flat = flatten_metrics((status.digest or {}).get("metrics") or {})
    previous_snapshot = load_snapshot(config.report_snapshot_path)
    comparison = build_comparison(
        current_flat, previous_snapshot, config.daily_report_timezone
    )

    logger.info(
        "Generating scheduled analytics report (baseline: %s).",
        comparison.previous_label or "none yet",
    )
    sent = await _analyse_and_send(
        config, status, report_mode=True, comparison=comparison
    )

    # Only advance the baseline once the report has actually gone out, so the
    # next message always compares against the last figures the team really saw.
    if sent and current_flat:
        save_snapshot(config.report_snapshot_path, current_flat, config.openrouter_model)
    elif not sent:
        logger.warning("Report not delivered; keeping previous snapshot as baseline.")

    return status


def _guarded(coro_factory, label: str):
    """Wrap a pipeline coroutine so an exception never stops the scheduler."""

    async def _run() -> None:
        try:
            await coro_factory()
        except Exception:  # pragma: no cover - defensive top-level guard
            logger.exception("%s raised; will retry on next schedule", label)

    return _run


def create_scheduler(config: MonitorConfig) -> AsyncIOScheduler:
    """Create (but do not start) an AsyncIOScheduler with the enabled jobs.

    Two independent jobs (either can be disabled via env vars):
      * Inactivity alarm – every ``CHECK_INTERVAL_MINUTES`` (default 60),
        sends only when the data is stale.
      * Scheduled report – fires on ``DAILY_REPORT_DAYS`` (default Mon & Fri) at
        ``DAILY_REPORT_TIME`` in ``DAILY_REPORT_TIMEZONE`` (default 12:45
        Asia/Kolkata), always sends, and includes the % change since the last
        report.
    """
    scheduler = AsyncIOScheduler(timezone="UTC")

    if config.inactivity_alarm_enabled:
        scheduler.add_job(
            _guarded(lambda: run_inactivity_check(config), "Inactivity check"),
            trigger="interval",
            minutes=config.check_interval_minutes,
            id=_ALARM_JOB_ID,
            max_instances=1,
            coalesce=True,
            replace_existing=True,
        )
        logger.info(
            "Inactivity alarm enabled: every %d minute(s), threshold %.2f day(s).",
            config.check_interval_minutes,
            config.inactivity_threshold_days,
        )

    if config.daily_report_enabled:
        scheduler.add_job(
            _guarded(lambda: run_daily_report(config), "Daily report"),
            trigger=CronTrigger(
                day_of_week=config.daily_report_days,
                hour=config.daily_report_hour,
                minute=config.daily_report_minute,
                timezone=config.daily_report_timezone,
            ),
            id=_REPORT_JOB_ID,
            max_instances=1,
            coalesce=True,
            replace_existing=True,
        )
        logger.info(
            "Scheduled report enabled: %s at %02d:%02d %s.",
            config.daily_report_days,
            config.daily_report_hour,
            config.daily_report_minute,
            config.daily_report_timezone,
        )

    return scheduler


# --------------------------------------------------------------------------- #
# FastAPI integration helpers
# --------------------------------------------------------------------------- #

def register_with_fastapi(app, config: Optional[MonitorConfig] = None) -> AsyncIOScheduler:
    """Attach the monitor to a FastAPI app via startup/shutdown events.

    Usage in your FastAPI init file::

        from fastapi import FastAPI
        from inactivity_monitor import register_with_fastapi

        app = FastAPI()
        register_with_fastapi(app)

    The scheduler is stored on ``app.state.inactivity_scheduler`` for access
    from request handlers (e.g. a manual "run now" endpoint).
    """
    resolved = config or MonitorConfig.from_env()
    scheduler = create_scheduler(resolved)

    @app.on_event("startup")
    async def _start_monitor() -> None:  # pragma: no cover - framework hook
        scheduler.start()
        app.state.inactivity_scheduler = scheduler
        app.state.inactivity_config = resolved
        logger.info("Inactivity monitor started.")

    @app.on_event("shutdown")
    async def _stop_monitor() -> None:  # pragma: no cover - framework hook
        if scheduler.running:
            scheduler.shutdown(wait=False)
        logger.info("Inactivity monitor stopped.")

    return scheduler


def build_lifespan(config: Optional[MonitorConfig] = None):
    """Return an async ``lifespan`` context manager for modern FastAPI.

    Usage::

        from contextlib import asynccontextmanager
        from fastapi import FastAPI
        from inactivity_monitor import build_lifespan

        app = FastAPI(lifespan=build_lifespan())
    """
    from contextlib import asynccontextmanager

    resolved = config or MonitorConfig.from_env()

    @asynccontextmanager
    async def _lifespan(app):  # pragma: no cover - framework hook
        scheduler = create_scheduler(resolved)
        scheduler.start()
        app.state.inactivity_scheduler = scheduler
        app.state.inactivity_config = resolved
        logger.info("Inactivity monitor started (lifespan).")
        try:
            yield
        finally:
            if scheduler.running:
                scheduler.shutdown(wait=False)
            logger.info("Inactivity monitor stopped (lifespan).")

    return _lifespan
