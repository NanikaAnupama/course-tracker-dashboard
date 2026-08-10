"""Remember which inactivity alert has already been sent, so it is sent once.

The alarm re-checks every hour, but a tracker that is stale at 09:00 is still
stale at 10:00 — re-posting the same warning every hour just trains the team to
ignore the channel. So each *stale episode* gets exactly one message.

An episode is identified by the workbook's ``last_update`` timestamp: as long as
that value does not move, it is the same silence being reported and no further
message goes out. When somebody finally updates the tracker, ``last_update``
changes and the stored state is cleared — the next time the data goes stale it
is a genuinely new episode and warrants a fresh warning.

Like the report snapshot, the state is a small JSON file, because the monitor
runs on ephemeral GitHub Actions runners with no memory between runs; the
workflow commits it back to the repo after each alarm run.

``ALERT_REPEAT_AFTER_DAYS`` (default 0 = never) can re-arm a still-unresolved
episode after N days if the team ever wants a reminder.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger(__name__)


def episode_key(last_update: Optional[datetime]) -> str:
    """Stable identifier for the current stale episode.

    Two checks belong to the same episode when the workbook has not been
    touched in between. A workbook whose ``last_update`` cannot be determined
    collapses to a single "unknown" episode rather than alerting every hour.
    """
    return last_update.astimezone(timezone.utc).isoformat() if last_update else "unknown"


def load_state(path: str) -> Optional[Dict[str, Any]]:
    """Load the last-alert record, or ``None`` when absent/unreadable."""
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
        return data if isinstance(data, dict) else None
    except (OSError, json.JSONDecodeError):
        logger.warning("Could not read alert state at %s", path, exc_info=True)
        return None


def save_state(path: str, key: str, days_inactive: Optional[float]) -> None:
    """Record that an alert has just gone out for episode ``key``."""
    payload = {
        "alerted_episode": key,
        "alerted_at": datetime.now(timezone.utc).isoformat(),
        "days_inactive_at_alert": days_inactive,
    }
    try:
        directory = os.path.dirname(path)
        if directory:
            os.makedirs(directory, exist_ok=True)
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True)
        logger.info("Recorded inactivity alert for episode %s", key)
    except OSError:
        logger.warning("Could not write alert state to %s", path, exc_info=True)


def clear_state(path: str) -> None:
    """Forget the last alert — called once the data is fresh again.

    This is what re-arms the alarm: the next stale episode is a new problem and
    deserves its own single message.
    """
    if not os.path.exists(path):
        return
    try:
        os.remove(path)
        logger.info("Data is fresh again; inactivity alarm re-armed.")
    except OSError:
        logger.warning("Could not clear alert state at %s", path, exc_info=True)


def _hours_since(raw: Optional[str]) -> Optional[float]:
    """Hours elapsed since a stored ISO timestamp, or ``None`` if unparseable."""
    if not raw:
        return None
    try:
        sent = datetime.fromisoformat(raw)
    except ValueError:
        return None
    if sent.tzinfo is None:
        sent = sent.replace(tzinfo=timezone.utc)
    return (datetime.now(timezone.utc) - sent).total_seconds() / 3600.0


def should_alert(
    path: str,
    key: str,
    repeat_after_days: float = 0.0,
) -> Tuple[bool, str]:
    """Decide whether to send a warning for episode ``key``.

    Returns ``(send, reason)``; ``reason`` explains the decision for the log.
    """
    state = load_state(path)
    if not state or state.get("alerted_episode") != key:
        return True, "first alert for this stale episode"

    if repeat_after_days and repeat_after_days > 0:
        hours = _hours_since(state.get("alerted_at"))
        if hours is not None and hours >= repeat_after_days * 24:
            return True, (
                f"still unresolved {hours / 24:.1f} day(s) after the last "
                f"warning (ALERT_REPEAT_AFTER_DAYS={repeat_after_days})"
            )

    return False, f"already alerted for this episode at {state.get('alerted_at')}"
