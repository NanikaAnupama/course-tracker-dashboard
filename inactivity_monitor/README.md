# Inactivity Monitor

A self-contained background worker that watches the SharePoint **Course
Tracker** workbook and raises a Microsoft Teams **Inactivity Warning** when the
data goes stale. It is fully independent of the existing Streamlit dashboard
(`app.py` / `textbook_progress.py`) — nothing in those files is imported or
modified.

## What it does

Two independent jobs run inside one scheduler (either can be disabled):

```
INACTIVITY ALARM  (every CHECK_INTERVAL_MINUTES, default 60)
  download workbook (?download=1)
  ─▶ determine "last update":  1. HTTP Last-Modified  2. newest date cell (fallback)
  ─▶ ONLY IF older than INACTIVITY_THRESHOLD_DAYS:
       OpenRouter LLM → Adaptive Card "⚠️ Inactivity Warning" → Teams

DAILY REPORT  (every day at DAILY_REPORT_TIME, default 12:45 Asia/Kolkata)
  download workbook
  ─▶ ALWAYS: OpenRouter LLM → Adaptive Card "📊 Daily Analytics Report" → Teams
```

## Module layout

| File | Responsibility |
|------|----------------|
| `config.py`      | Loads & validates all env vars into a `MonitorConfig`. |
| `data_source.py` | Downloads the workbook, computes freshness + data digest. |
| `analytics.py`   | Calls OpenRouter, normalises the JSON analysis. |
| `teams.py`       | Builds the Adaptive Card and POSTs it (256 KB-safe). |
| `scheduler.py`   | Pipeline orchestration + APScheduler + FastAPI hooks. |
| `__main__.py`    | Standalone CLI runner (`python -m inactivity_monitor`). |

## 1. Install

```bash
pip install -r inactivity_monitor/requirements-monitor.txt
```

## 2. Configure environment variables

Copy `.env.example` to `.env` and fill in the two required secrets:

| Variable | Required | Default | Purpose |
|----------|:--------:|---------|---------|
| `OPENROUTER_API_KEY`        | ✅ | — | OpenRouter API key. |
| `TEAMS_WEBHOOK_URL`         | ✅ | — | Teams Workflows inbound webhook. |
| `SHAREPOINT_FILE_URL`       |    | shared tracker URL | Workbook download link (`?download=1`). |
| `OPENROUTER_MODEL`          |    | `deepseek/deepseek-v3.2-exp` | LLM model id. |
| `OPENROUTER_BASE_URL`       |    | OpenRouter chat endpoint | Override for proxies. |
| `OPENROUTER_SITE_URL`       |    | — | Optional OpenRouter `HTTP-Referer`. |
| `OPENROUTER_APP_NAME`       |    | `Course Tracker Inactivity Monitor` | OpenRouter `X-Title`. |
| `ENABLE_INACTIVITY_ALARM`   |    | `true` | Turn the stale-data alarm on/off. |
| `INACTIVITY_THRESHOLD_DAYS` |    | `2` | Alarm when data is older than this. |
| `CHECK_INTERVAL_MINUTES`    |    | `60` | How often the alarm re-checks. |
| `ENABLE_DAILY_REPORT`       |    | `true` | Turn the daily digest on/off. |
| `DAILY_REPORT_TIME`         |    | `12:45` | Daily send time, 24h `HH:MM`. |
| `DAILY_REPORT_TIMEZONE`     |    | `Asia/Kolkata` | IANA tz for the daily time. |
| `HTTP_TIMEOUT_SECONDS`      |    | `30` | Timeout for all HTTP calls. |

Set them in your shell instead of a file if you prefer:

```powershell
# Windows PowerShell
$env:OPENROUTER_API_KEY = "sk-or-v1-..."
$env:TEAMS_WEBHOOK_URL  = "https://prod-..."
```

## 3. Run

**Standalone worker** (long-lived, runs every interval):

```bash
python -m inactivity_monitor
```

**One-off tests** (fetch → analyse → send once, then exit):

```bash
python -m inactivity_monitor --once     # run the inactivity alarm once (sends only if stale)
python -m inactivity_monitor --report   # send the daily analytics report now (always sends)
```

## 4. (Optional) Run inside a FastAPI app

The worker was built to drop straight into a FastAPI init file. Two styles:

```python
# Style A — startup/shutdown events (works on all FastAPI versions)
from fastapi import FastAPI
from inactivity_monitor import register_with_fastapi

app = FastAPI()
register_with_fastapi(app)   # reads config from environment
```

```python
# Style B — modern lifespan
from fastapi import FastAPI
from inactivity_monitor import build_lifespan

app = FastAPI(lifespan=build_lifespan())
```

You can also expose a manual trigger endpoint:

```python
from inactivity_monitor import run_inactivity_check

@app.post("/internal/check-inactivity")
async def check_now():
    status = await run_inactivity_check(app.state.inactivity_config)
    return {"is_stale": status.is_stale, "days_inactive": status.days_inactive}
```

> **Note:** the existing dashboard is **Streamlit**, not FastAPI. If you don't
> have a FastAPI process, just run the standalone worker (step 3) — e.g. as a
> Windows Task Scheduler task, a systemd service, or a container sidecar.

## Teams payload format

The Teams *Workflows* webhook only accepts **POST** with a max **256 KB** body,
and expects an attachment-wrapped Adaptive Card. `teams.py` emits exactly:

```json
{
  "type": "message",
  "attachments": [
    {
      "contentType": "application/vnd.microsoft.card.adaptive",
      "content": { "type": "AdaptiveCard", "version": "1.5", "body": [ ... ] }
    }
  ]
}
```

The card leads with the **⚠️ Inactivity Warning** header, a FactSet of
freshness details, then the LLM's critical findings, anomalies, and
recommendation. Oversized payloads are automatically trimmed to stay under
256 KB.
```
