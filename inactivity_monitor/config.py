"""Environment-driven configuration for the inactivity monitor.

Every tunable value is read from an environment variable so that no secret
(OpenRouter key, Teams webhook) ever lives in source control. See README in
this package for the full list of variables and example values.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional

# The shared tracker workbook. `?download=1` makes SharePoint return the raw
# .xlsx bytes instead of the web viewer — the same trick the dashboard uses.
DEFAULT_SHAREPOINT_URL = (
    "https://globaledulinkuk-my.sharepoint.com/:x:/g/personal/"
    "sadeev_imperiallearning_co_uk/"
    "IQCgqczvPccERK5x-3fcBFPdAUsHzB0rMIahy7kRMz39xtU?download=1"
)

DEFAULT_OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_OPENROUTER_MODEL = "deepseek/deepseek-v3.2-exp"

# Where each report's headline figures are persisted so the next run can compute
# the change since the last message. Lives inside the package so the GitHub
# Actions workflow can commit it back to the repo between runs.
DEFAULT_SNAPSHOT_PATH = os.path.join(os.path.dirname(__file__), "last_report_snapshot.json")

# Days the scheduled report goes out (APScheduler/cron day-of-week tokens).
DEFAULT_REPORT_DAYS = "mon,fri"


class ConfigError(RuntimeError):
    """Raised when required environment variables are missing or invalid."""


def _get_float(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        return float(raw)
    except ValueError as exc:  # pragma: no cover - defensive
        raise ConfigError(f"{name} must be a number, got {raw!r}") from exc


def _get_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        return int(raw)
    except ValueError as exc:  # pragma: no cover - defensive
        raise ConfigError(f"{name} must be an integer, got {raw!r}") from exc


def _get_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _parse_hhmm(name: str, default: str) -> tuple[int, int]:
    """Parse an "HH:MM" string into (hour, minute)."""
    raw = (os.getenv(name) or default).strip()
    try:
        hour_str, minute_str = raw.split(":", 1)
        hour, minute = int(hour_str), int(minute_str)
        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            raise ValueError
        return hour, minute
    except ValueError as exc:
        raise ConfigError(f"{name} must be in HH:MM 24h format, got {raw!r}") from exc


@dataclass(frozen=True)
class MonitorConfig:
    """Immutable configuration snapshot loaded from the environment."""

    sharepoint_url: str
    openrouter_api_key: str
    openrouter_model: str
    openrouter_base_url: str
    teams_webhook_url: str
    inactivity_threshold_days: float
    check_interval_minutes: int
    http_timeout_seconds: float
    # Optional OpenRouter attribution headers (recommended by OpenRouter).
    openrouter_site_url: Optional[str]
    openrouter_app_name: Optional[str]
    # Inactivity alarm: fires when data is stale (interval check).
    inactivity_alarm_enabled: bool
    # Daily scheduled report: always sends at a fixed local time.
    daily_report_enabled: bool
    daily_report_hour: int
    daily_report_minute: int
    daily_report_timezone: str
    daily_report_days: str
    report_snapshot_path: str

    @classmethod
    def from_env(cls) -> "MonitorConfig":
        """Build a config from environment variables, validating required keys.

        Raises:
            ConfigError: if OPENROUTER_API_KEY or TEAMS_WEBHOOK_URL are absent.
        """
        api_key = (os.getenv("OPENROUTER_API_KEY") or "").strip()
        webhook = (os.getenv("TEAMS_WEBHOOK_URL") or "").strip()
        report_hour, report_minute = _parse_hhmm("DAILY_REPORT_TIME", "12:45")

        missing = []
        if not api_key:
            missing.append("OPENROUTER_API_KEY")
        if not webhook:
            missing.append("TEAMS_WEBHOOK_URL")
        if missing:
            raise ConfigError(
                "Missing required environment variable(s): "
                + ", ".join(missing)
                + ". See inactivity_monitor/README.md for setup."
            )

        return cls(
            sharepoint_url=(os.getenv("SHAREPOINT_FILE_URL") or DEFAULT_SHAREPOINT_URL).strip(),
            openrouter_api_key=api_key,
            openrouter_model=(os.getenv("OPENROUTER_MODEL") or DEFAULT_OPENROUTER_MODEL).strip(),
            openrouter_base_url=(os.getenv("OPENROUTER_BASE_URL") or DEFAULT_OPENROUTER_BASE_URL).strip(),
            teams_webhook_url=webhook,
            inactivity_threshold_days=_get_float("INACTIVITY_THRESHOLD_DAYS", 2.0),
            check_interval_minutes=_get_int("CHECK_INTERVAL_MINUTES", 60),
            http_timeout_seconds=_get_float("HTTP_TIMEOUT_SECONDS", 30.0),
            openrouter_site_url=(os.getenv("OPENROUTER_SITE_URL") or None),
            openrouter_app_name=(os.getenv("OPENROUTER_APP_NAME") or "Course Tracker Inactivity Monitor"),
            inactivity_alarm_enabled=_get_bool("ENABLE_INACTIVITY_ALARM", True),
            daily_report_enabled=_get_bool("ENABLE_DAILY_REPORT", True),
            daily_report_hour=report_hour,
            daily_report_minute=report_minute,
            daily_report_timezone=(os.getenv("DAILY_REPORT_TIMEZONE") or "Asia/Kolkata").strip(),
            daily_report_days=(os.getenv("DAILY_REPORT_DAYS") or DEFAULT_REPORT_DAYS).strip(),
            report_snapshot_path=(os.getenv("REPORT_SNAPSHOT_PATH") or DEFAULT_SNAPSHOT_PATH).strip(),
        )
