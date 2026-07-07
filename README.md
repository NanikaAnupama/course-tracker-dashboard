# Course Content Production Dashboard

Production tracker for course content (AI Videos, Podcasts, Study Guides, H5P
Quizzes, Textbooks). Data comes live from the SharePoint tracker workbooks —
nothing is stored in this repo.

**Architecture**

| Piece | Tech | Hosted on |
|---|---|---|
| `backend/` | FastAPI + pandas (parses the SharePoint Excel files, serves JSON) | Railway |
| `frontend/` | React (Vite) + Recharts | Vercel |
| `inactivity_monitor/` | Teams alerts (hourly staleness alarm + Mon/Fri report) | GitHub Actions cron, and in-process inside the Railway API |
| `app.py` | Legacy Streamlit dashboard (kept for reference) | — |

## Run locally

Backend (terminal 1):

```powershell
pip install -r backend/requirements.txt
uvicorn backend.main:app --reload --port 8000
```

Frontend (terminal 2):

```powershell
cd frontend
npm install
npm run dev
```

Open http://localhost:5173 — the Vite dev server proxies `/api/*` to
http://localhost:8000 automatically.

Set `ENABLE_INACTIVITY_MONITOR=0` before starting uvicorn if you do NOT want
the local backend to run the Teams-alert scheduler (recommended locally, so
you don't fire real alerts while developing).

## Deploy

### Backend → Railway

`railway.json` already builds `backend/requirements.txt` and starts
`uvicorn backend.main:app`. Push to the connected repo (or `railway up`).

Required service variables (same ones the monitor already uses):
`TEAMS_WEBHOOK_URL`, `OPENROUTER_API_KEY`, optionally `SHAREPOINT_FILE_URL`.
Optional: `CORS_ORIGINS` (comma-separated, defaults to `*`),
`ENABLE_INACTIVITY_MONITOR` (defaults to on — keeps the Teams alert behaviour
that previously ran via `python -m inactivity_monitor` on Railway).

### Frontend → Vercel

Import the repo in Vercel and set **Root Directory = `frontend`**
(framework preset: Vite). Add one environment variable:

```
VITE_API_URL = https://<your-railway-app>.up.railway.app
```

CLI alternative:

```powershell
cd frontend
npx vercel --prod
```

## API endpoints

`/api/health`, `/api/overview`, `/api/courses`, `/api/subjects`,
`/api/levels`, `/api/video-log`, `/api/textbooks`, `POST /api/refresh`
(clears the 5-minute SharePoint cache).
