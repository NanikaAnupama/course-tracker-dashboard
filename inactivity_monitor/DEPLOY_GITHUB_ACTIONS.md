# Cloud deployment (GitHub Actions)

The inactivity monitor now runs on **GitHub's cloud runners** via
[`.github/workflows/inactivity-monitor.yml`](../.github/workflows/inactivity-monitor.yml),
not on the laptop. This is what makes reports send **regardless of whether the
laptop is on, asleep, or out of battery** — the schedule no longer depends on
the machine being awake.

| Trigger | Cron (UTC) | Local (IST) | Action |
|---------|-----------|-------------|--------|
| Daily report  | `15 7 * * *` | 12:45 | `--report` (always sends 📊) |
| Inactivity alarm | `0 * * * *` | hourly | `--once` (sends ⚠️ only if data >2 days stale) |
| Manual test | — | — | "Run workflow" button → pick `report` or `once` |

## One-time setup: add the two secrets (web UI — keys never leave your hands)

`gh` CLI isn't installed, so add them in the browser. This is the most secure
path: your keys are typed straight into GitHub's encrypted store and never pass
through any local tool.

1. Go to **https://github.com/NanikaAnupama/course-tracker-dashboard/settings/secrets/actions**
2. Click **New repository secret** and add each of these (names must match exactly):

   | Secret name | Value (from your local `.env`) |
   |-------------|--------------------------------|
   | `OPENROUTER_API_KEY` | your `sk-or-v1-…` key |
   | `TEAMS_WEBHOOK_URL`  | your `https://…powerplatform.com/…` webhook URL |

   Optional (only if you ever want to override the defaults):
   - Secret `SHAREPOINT_FILE_URL` — a different workbook download URL.
   - Variable (not secret) `OPENROUTER_MODEL` — a different model id.

3. Push this branch to GitHub. Schedules only run from the **default branch
   (`main`)**, so the workflow must be merged to `main` to start firing.

## Verify it works

1. After pushing, open the **Actions** tab → **Inactivity Monitor** →
   **Run workflow** → choose `report` → **Run workflow**.
2. Watch the run go green and confirm the 📊 card lands in Teams.
3. Then leave the cron triggers to fire on their own (12:45 IST + hourly).

## After cloud is confirmed: retire the local tasks (avoid duplicate messages)

The laptop still has two Task Scheduler jobs. Once the cloud run is verified,
**disable them** or you'll get every report twice:

```powershell
Disable-ScheduledTask -TaskName "ImperialTracker-DailyReport"
Disable-ScheduledTask -TaskName "ImperialTracker-InactivityAlarm"
# To remove entirely instead:
# Unregister-ScheduledTask -TaskName "ImperialTracker-DailyReport" -Confirm:$false
# Unregister-ScheduledTask -TaskName "ImperialTracker-InactivityAlarm" -Confirm:$false
```

## Security model

- **Secrets** live only in GitHub Actions' encrypted secret store; they're
  injected as env vars into the run step and auto-masked in logs. The workflow
  never echoes them.
- **`.env` is gitignored** (see repo-root `.gitignore`) so the real keys can
  never be committed by accident. It has never been in git history.
- **Least privilege:** the workflow declares `permissions: contents: read` —
  it can only read the repo, nothing else.
- **No overlap:** a `concurrency` group + `timeout-minutes: 10` stop runs from
  piling up or hanging.

### Optional hardening

- **Pin actions to commit SHAs** instead of `@v4`/`@v5` tags to fully defeat
  tag-moving supply-chain attacks (e.g. `actions/checkout@<40-char-sha>`).
- **Rotate the OpenRouter key** periodically; update the GitHub secret only.

## Caveats of cloud cron

- GitHub's scheduler is **best-effort** — runs can be delayed several minutes
  under load. Fine for a daily digest; not for second-precise timing.
- Scheduled workflows are **auto-disabled after 60 days with no repo commits**.
  Re-enable from the Actions tab if it ever goes dormant.
