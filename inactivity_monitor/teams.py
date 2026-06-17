"""Build and send the Microsoft Teams Adaptive Card alert.

The Teams *Workflows* (Power Automate) inbound webhook accepts only HTTP POST
and caps the payload at 256 KB. It expects the body to be an attachment
wrapper containing an Adaptive Card (``application/vnd.microsoft.card.adaptive``).
This module builds that exact structure and posts it asynchronously.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

import httpx

from .analytics import AnalysisResult
from .config import MonitorConfig
from .data_source import DataStatus
from .metrics import card_sections
from .snapshot import ReportComparison, format_change

logger = logging.getLogger(__name__)

# Teams Workflows hard limit.
_MAX_PAYLOAD_BYTES = 256 * 1024
_ADAPTIVE_CARD_VERSION = "1.5"


def _fact(title: str, value: str) -> Dict[str, str]:
    return {"title": title, "value": value}


def _metrics_blocks(status: DataStatus) -> List[Dict[str, Any]]:
    """Render the live sheet-by-sheet metrics as headed FactSets.

    Pulls the precomputed numbers from ``status.digest['metrics']`` so the card
    always shows concrete figures (content done vs target, per-person output,
    upload throughput) even when the LLM narrative is thin.
    """
    metrics = (status.digest or {}).get("metrics") or {}
    sections = card_sections(metrics)
    if not sections:
        return []

    blocks: List[Dict[str, Any]] = [
        {
            "type": "TextBlock",
            "text": "📈 Live metrics",
            "weight": "Bolder",
            "size": "Medium",
            "color": "Accent",
            "spacing": "Medium",
            "wrap": True,
        }
    ]
    for heading, rows in sections:
        blocks.append(
            {
                "type": "TextBlock",
                "text": heading,
                "weight": "Bolder",
                "spacing": "Medium",
                "wrap": True,
            }
        )
        blocks.append(
            {
                "type": "FactSet",
                "facts": [_fact(label, value) for label, value in rows],
            }
        )
    return blocks


def _comparison_blocks(comparison: ReportComparison) -> List[Dict[str, Any]]:
    """Render the % change since the last report, with a note on how it's measured."""
    if comparison.changes:
        rows = [(change.label, format_change(change)) for change in comparison.changes]
    else:
        rows = []

    baseline = (
        f"since the last report (sent {comparison.previous_label})"
        if comparison.previous_label
        else "since the last report"
    )

    if comparison.has_baseline:
        note = (
            f"Figures show the change {baseline}. Reports go out Mon & Fri at "
            "12:45 IST — so Friday is measured against Monday, and Monday against "
            "the previous Friday. Counts show the change as +/- value and %; "
            "completion shows the change in percentage points (pts)."
        )
    else:
        note = (
            "This is the first report on record, so there is nothing to compare "
            "against yet. From the next report (Mon & Fri, 12:45 IST) this section "
            "will show the % change since the previous one."
        )

    blocks: List[Dict[str, Any]] = [
        {
            "type": "TextBlock",
            "text": "🔼 Change since last report",
            "weight": "Bolder",
            "size": "Medium",
            "color": "Accent",
            "spacing": "Medium",
            "wrap": True,
        },
        {
            "type": "TextBlock",
            "text": note,
            "wrap": True,
            "isSubtle": True,
            "size": "Small",
            "spacing": "None",
        },
    ]
    if rows:
        blocks.append(
            {"type": "FactSet", "facts": [_fact(label, value) for label, value in rows]}
        )
    return blocks


def _bullet_block(items: List[str], color: str) -> List[Dict[str, Any]]:
    """Render a list of strings as compact, wrapping TextBlocks with a bullet."""
    blocks: List[Dict[str, Any]] = []
    for item in items:
        blocks.append(
            {
                "type": "TextBlock",
                "text": f"• {item}",
                "wrap": True,
                "spacing": "Small",
                "color": color,
            }
        )
    return blocks


def build_adaptive_card(
    status: DataStatus,
    analysis: AnalysisResult,
    *,
    report_mode: bool = False,
    comparison: Optional[ReportComparison] = None,
) -> Dict[str, Any]:
    """Assemble the full Teams message payload (attachment wrapper + card).

    Args:
        report_mode: when True, frame the card as a scheduled analytics digest
            (blue accent). When False (default), frame it as an urgent
            ⚠️ Inactivity Warning (red accent).
        comparison: when supplied (report mode), adds the "change since last
            report" section with the % change vs the previously sent message.
    """
    last_update = (
        status.last_update.strftime("%Y-%m-%d %H:%M UTC")
        if status.last_update
        else "Unknown"
    )
    days_inactive = (
        f"{status.days_inactive} day(s)" if status.days_inactive is not None else "Unknown"
    )

    if report_mode:
        header_text = "📊 Daily Analytics Report"
        header_color = "Accent"
        subtitle = "Scheduled daily summary of the Course Tracker."
    else:
        header_text = "⚠️ Inactivity Warning"
        header_color = "Attention"
        subtitle = "Course Tracker data has not been updated within the expected window."

    body: List[Dict[str, Any]] = [
        # --- Header: prominent at the top ---
        {
            "type": "TextBlock",
            "text": header_text,
            "weight": "Bolder",
            "size": "ExtraLarge",
            "color": header_color,
            "wrap": True,
        },
        {
            "type": "TextBlock",
            "text": subtitle,
            "wrap": True,
            "spacing": "None",
            "isSubtle": True,
        },
        # --- Freshness facts ---
        {
            "type": "FactSet",
            "facts": [
                _fact("Last update", last_update),
                _fact("Source", status.last_update_source),
                _fact("Inactive for", days_inactive),
                _fact("Checked at", status.checked_at.strftime("%Y-%m-%d %H:%M UTC")),
            ],
        },
        # --- LLM headline ---
        {
            "type": "TextBlock",
            "text": analysis.headline,
            "weight": "Bolder",
            "size": "Medium",
            "wrap": True,
            "spacing": "Medium",
        },
    ]

    # --- Live metrics: deterministic, sheet-by-sheet figures ---
    body.extend(_metrics_blocks(status))

    # --- Change vs the previously sent report (report mode only) ---
    if comparison is not None:
        body.extend(_comparison_blocks(comparison))

    if analysis.highlights:
        body.append(
            {
                "type": "TextBlock",
                "text": "Key insights",
                "weight": "Bolder",
                "color": "Accent",
                "spacing": "Medium",
                "wrap": True,
            }
        )
        body.extend(_bullet_block(analysis.highlights, "Default"))

    if analysis.critical_findings:
        body.append(
            {
                "type": "TextBlock",
                "text": "Critical findings",
                "weight": "Bolder",
                "color": "Attention",
                "spacing": "Medium",
                "wrap": True,
            }
        )
        body.extend(_bullet_block(analysis.critical_findings, "Attention"))

    if analysis.anomalies:
        body.append(
            {
                "type": "TextBlock",
                "text": "Anomalies",
                "weight": "Bolder",
                "color": "Warning",
                "spacing": "Medium",
                "wrap": True,
            }
        )
        body.extend(_bullet_block(analysis.anomalies, "Warning"))

    if analysis.recommendation:
        body.append(
            {
                "type": "TextBlock",
                "text": "Recommended action",
                "weight": "Bolder",
                "color": "Good",
                "spacing": "Medium",
                "wrap": True,
            }
        )
        body.append(
            {
                "type": "TextBlock",
                "text": analysis.recommendation,
                "wrap": True,
                "spacing": "Small",
            }
        )

    # Footer attribution.
    body.append(
        {
            "type": "TextBlock",
            "text": f"Generated by the inactivity monitor · model: {analysis.model}",
            "isSubtle": True,
            "size": "Small",
            "spacing": "Medium",
            "wrap": True,
        }
    )

    card = {
        "type": "AdaptiveCard",
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "version": _ADAPTIVE_CARD_VERSION,
        "body": body,
    }

    return {
        "type": "message",
        "attachments": [
            {
                "contentType": "application/vnd.microsoft.card.adaptive",
                "content": card,
            }
        ],
    }


def _enforce_payload_limit(payload: Dict[str, Any]) -> bytes:
    """Serialise the payload and guarantee it fits within Teams' 256 KB cap.

    If the card is somehow too large (e.g. a very chatty LLM), trim the card
    body down to the essential header/facts so the alert still delivers.
    """
    encoded = json.dumps(payload).encode("utf-8")
    if len(encoded) <= _MAX_PAYLOAD_BYTES:
        return encoded

    logger.warning(
        "Adaptive Card payload %d bytes exceeds 256 KB; trimming.", len(encoded)
    )
    card = payload["attachments"][0]["content"]
    # Keep only header + first FactSet (the must-have context).
    trimmed_body = card["body"][:3] + [
        {
            "type": "TextBlock",
            "text": "(Analysis truncated to fit the 256 KB Teams limit.)",
            "wrap": True,
            "isSubtle": True,
        }
    ]
    card["body"] = trimmed_body
    return json.dumps(payload).encode("utf-8")


async def send_teams_alert(config: MonitorConfig, payload: Dict[str, Any]) -> bool:
    """POST the Adaptive Card to the Teams Workflows webhook.

    Returns ``True`` on success, ``False`` on any handled failure.
    """
    body = _enforce_payload_limit(payload)
    try:
        async with httpx.AsyncClient(timeout=config.http_timeout_seconds) as client:
            response = await client.post(
                config.teams_webhook_url,
                content=body,
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        logger.error(
            "Teams webhook rejected payload (%s): %s",
            exc.response.status_code,
            exc.response.text[:500],
        )
        return False
    except httpx.HTTPError as exc:
        logger.error("Teams webhook request failed: %s", exc)
        return False

    logger.info("Card posted to Teams (%d bytes).", len(body))
    return True
