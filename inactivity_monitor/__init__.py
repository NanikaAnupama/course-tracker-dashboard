"""Inactivity monitor for the Course Tracker dashboard.

A self-contained background worker that:
  1. Polls the SharePoint tracker workbook every 60 minutes.
  2. Detects when the data has gone stale (no update within N days).
  3. Asks OpenRouter to synthesise a critical-analysis summary.
  4. Posts an Adaptive Card "Inactivity Warning" to Microsoft Teams.

This package does not import or modify the existing Streamlit dashboard.
Import the helpers you need from here::

    from inactivity_monitor import register_with_fastapi, run_inactivity_check
"""

from .config import ConfigError, MonitorConfig
from .data_source import DataStatus, get_data_status
from .analytics import AnalysisResult, synthesise_analysis
from .teams import build_adaptive_card, send_teams_alert
from .scheduler import (
    build_lifespan,
    create_scheduler,
    register_with_fastapi,
    run_daily_report,
    run_inactivity_check,
)

__all__ = [
    "ConfigError",
    "MonitorConfig",
    "DataStatus",
    "get_data_status",
    "AnalysisResult",
    "synthesise_analysis",
    "build_adaptive_card",
    "send_teams_alert",
    "build_lifespan",
    "create_scheduler",
    "register_with_fastapi",
    "run_daily_report",
    "run_inactivity_check",
]
