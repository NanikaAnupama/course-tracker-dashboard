"""Synthesise a critical-analysis summary via the OpenRouter chat API.

The LLM is asked to return a strict JSON object so the result can be rendered
into a clean Adaptive Card. If the model returns prose instead of JSON we fall
back gracefully to a single free-text block, so a malformed response never
blocks the alert.
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import httpx

from .config import MonitorConfig
from .data_source import DataStatus

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = (
    "You are an operations analyst monitoring a content-production tracker. "
    "Your job is to flag critical issues, anomalies, and threshold breaches "
    "EARLY so the team can act before conditions deteriorate. Be concise, "
    "specific, and quantitative. Respond with ONLY a JSON object — no prose, "
    "no markdown fences."
)

_JSON_INSTRUCTIONS = (
    "Return a JSON object with exactly these keys:\n"
    '  "headline": a one-sentence summary of the single most important takeaway, '
    "with a concrete number from the data.\n"
    '  "highlights": array of short strings, each a noteworthy insight backed by a '
    "specific number (e.g. completion %, counts done vs target, recent output, top "
    "contributor). Aim for 3-5 highlights drawn from DIFFERENT sheets.\n"
    '  "critical_findings": array of short strings, each a critical issue or '
    "threshold breach (e.g. a content type far behind, a stalled sheet, a data error).\n"
    '  "anomalies": array of short strings describing genuinely unusual patterns '
    "(sudden output spikes or drops, mismatched totals between sheets).\n"
    '  "recommendation": a one-sentence, specific recommended action.\n'
    "Ground EVERY string in the numbers under workbook_digest.metrics — quote actual "
    "figures, never vague phrasing. Keep each string under 200 characters. Use empty "
    "arrays if nothing applies."
)

# Domain rules that tell the model which "issues" are actually expected workflow
# behaviour, so it stops raising false alarms the team has explicitly called out.
_DOMAIN_CONTEXT = (
    "IMPORTANT CONTEXT — do NOT flag the following as issues, anomalies, critical "
    "findings, or data errors; they are expected and normal:\n"
    "1. NotebookLM and WebTool are two SEQUENTIAL stages on different days: a person "
    "generates videos in NotebookLM on one day, and they are processed by the WebTool "
    "on a later day. So high recent NotebookLM output with zero/low WebTool output in "
    "the same window is NORMAL workflow lag, not a processing disconnect — never flag it.\n"
    "2. The sheets are intentionally pre-filled with rows carrying FUTURE dates so the "
    "team need not add a date every day. Therefore future-dated cells are expected. "
    "Never flag future dates, and never flag a sheet's latest date being older or newer "
    "than the workbook's last-modified time / last_update as 'stale' or 'delayed tracking'.\n"
    "Focus instead on genuine content-progress insights and real threshold breaches."
)


@dataclass
class AnalysisResult:
    """Normalised LLM output ready for rendering."""

    headline: str
    highlights: List[str] = field(default_factory=list)
    critical_findings: List[str] = field(default_factory=list)
    anomalies: List[str] = field(default_factory=list)
    recommendation: str = ""
    raw_text: str = ""
    model: str = ""


def _build_user_prompt(status: DataStatus, report_mode: bool = False) -> str:
    """Compose the user message from the freshness status and data digest."""
    last_update = (
        status.last_update.isoformat() if status.last_update else "unknown"
    )
    payload = {
        "last_update": last_update,
        "last_update_source": status.last_update_source,
        "days_since_last_update": status.days_inactive,
        "checked_at": status.checked_at.isoformat(),
        "workbook_digest": status.digest,
    }
    if report_mode:
        intro = (
            "Produce a daily status summary of the content-production tracker. "
            "Lead with what is actually happening inside the sheets: how much "
            "content (AI videos, podcasts, study guides) is done vs target, "
            "chapter-wise video progress, recent NotebookLM/WebTool output and who "
            "is driving it, and course-page upload throughput. Then call out any "
            "critical aspects, anomalies, or threshold breaches."
        )
    else:
        intro = (
            "The tracker data appears stale. Summarise what the sheets currently "
            "show — content completion vs target, chapter progress, recent per-person "
            "output, upload throughput — then identify critical aspects, anomalies, or "
            "threshold breaches that need attention before they worsen."
        )
    return (
        f"{intro}\n\n"
        f"{_DOMAIN_CONTEXT}\n\n"
        f"DATA:\n{json.dumps(payload, indent=2)}\n\n"
        f"{_JSON_INSTRUCTIONS}"
    )


def _extract_json(text: str) -> Optional[Dict[str, Any]]:
    """Pull a JSON object out of an LLM response, tolerating code fences."""
    if not text:
        return None
    candidate = text.strip()
    # Strip ```json ... ``` fences if present.
    fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", candidate, re.DOTALL)
    if fence:
        candidate = fence.group(1)
    else:
        brace = re.search(r"\{.*\}", candidate, re.DOTALL)
        if brace:
            candidate = brace.group(0)
    try:
        parsed = json.loads(candidate)
        return parsed if isinstance(parsed, dict) else None
    except json.JSONDecodeError:
        return None


# Findings that are really just date-freshness commentary. The in-sheet date
# cells are intentionally pre-filled (often with future dates), so any "stale",
# "future-dated", or "behind the workbook" observation is a false positive the
# team has asked us to suppress — regardless of how the model phrases it.
_DATE_NOISE_RE = re.compile(
    r"in the future|future[- ]?dated?|days? (?:in the future|behind|ahead)"
    r"|behind the (?:workbook|last update|update)|delayed tracking|\bstale\b"
    r"|no activity (?:for|in)|latest (?:tracked )?date|weeks? (?:ago|of (?:in)?activity)",
    re.IGNORECASE,
)


def _drop_date_noise(items: List[str]) -> List[str]:
    """Remove findings that are merely date-freshness/future-date false alarms."""
    return [item for item in items if not _DATE_NOISE_RE.search(item)]


def _normalise(parsed: Optional[Dict[str, Any]], raw_text: str, model: str) -> AnalysisResult:
    """Coerce parsed JSON (or raw text) into an AnalysisResult."""
    if not parsed:
        return AnalysisResult(
            headline="Data inactivity detected — see details below.",
            critical_findings=[raw_text.strip()] if raw_text.strip() else [],
            raw_text=raw_text,
            model=model,
        )

    def _as_list(value: Any) -> List[str]:
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        if isinstance(value, str) and value.strip():
            return [value.strip()]
        return []

    return AnalysisResult(
        headline=str(parsed.get("headline", "")).strip()
        or "Data inactivity detected.",
        highlights=_drop_date_noise(_as_list(parsed.get("highlights"))),
        critical_findings=_drop_date_noise(_as_list(parsed.get("critical_findings"))),
        anomalies=_drop_date_noise(_as_list(parsed.get("anomalies"))),
        recommendation=str(parsed.get("recommendation", "")).strip(),
        raw_text=raw_text,
        model=model,
    )


async def synthesise_analysis(
    config: MonitorConfig, status: DataStatus, report_mode: bool = False
) -> AnalysisResult:
    """Call OpenRouter and return a normalised analysis.

    On any API/network error a safe fallback result is returned (the alert
    should still fire even if the LLM is unavailable).
    """
    headers = {
        "Authorization": f"Bearer {config.openrouter_api_key}",
        "Content-Type": "application/json",
    }
    # Optional attribution headers recommended by OpenRouter.
    if config.openrouter_site_url:
        headers["HTTP-Referer"] = config.openrouter_site_url
    if config.openrouter_app_name:
        headers["X-Title"] = config.openrouter_app_name

    body = {
        "model": config.openrouter_model,
        "messages": [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": _build_user_prompt(status, report_mode)},
        ],
        "temperature": 0.2,
        "max_tokens": 800,
    }

    try:
        async with httpx.AsyncClient(timeout=config.http_timeout_seconds) as client:
            response = await client.post(
                config.openrouter_base_url, headers=headers, json=body
            )
            response.raise_for_status()
            data = response.json()
    except httpx.HTTPStatusError as exc:
        logger.error(
            "OpenRouter returned %s: %s",
            exc.response.status_code,
            exc.response.text[:500],
        )
        return _fallback_result(status, config.openrouter_model)
    except (httpx.HTTPError, json.JSONDecodeError) as exc:
        logger.error("OpenRouter request failed: %s", exc)
        return _fallback_result(status, config.openrouter_model)

    try:
        content = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError):
        logger.error("Unexpected OpenRouter response shape: %s", str(data)[:500])
        return _fallback_result(status, config.openrouter_model)

    return _normalise(_extract_json(content), content, config.openrouter_model)


def _fallback_result(status: DataStatus, model: str) -> AnalysisResult:
    """Deterministic analysis used when the LLM is unreachable."""
    days = status.days_inactive
    return AnalysisResult(
        headline=(
            f"Tracker data has not updated in {days} day(s) — "
            "automated analysis unavailable."
        ),
        critical_findings=[
            "LLM analysis could not be generated; raw freshness check only.",
            f"Last update: {status.last_update.isoformat() if status.last_update else 'unknown'} "
            f"(source: {status.last_update_source}).",
        ],
        recommendation="Verify the data pipeline and check the OpenRouter API key/quota.",
        model=model,
    )
