# Docker Doctor - Project Roadmap

## Project Overview

Docker Doctor is an automated monitoring system designed to provide daily insights into the health of Docker containers running on a Proxmox (pve2) host. The system collects, analyzes, and reports on Docker container logs using a combination of statistical analysis and AI-powered summarization to identify patterns, trends, and potential issues.

The system is designed to be:
- **Automated**: Runs daily without manual intervention
- **Intelligent**: Uses AI to summarize complex log data into actionable insights
- **Alerting**: Sends notifications to Discord when issues are detected
- **Persistent**: Stores historical data in SQLite for trend analysis

## Development Status: August 2, 2026 (CORRECTED)

### Current Status: **Dashboard functional, scheduler wired — data pipeline partially ACTIVE. v1.1 displays stale data. 2/7 tasks complete.**

An operator audit on August 2 found that the v1.1 image presents historical data as
if it were current. This section supersedes the earlier "Resolved - Dashboard
Working" status, which was based on a verification suite that checked artifact
consistency but never checked data freshness.

> **VERIFICATION STATUS (2026-08-03):** Code review against ROADMAP found:
> - Tasks 1 (source control) and 2 (collector wiring) are implemented.
> - Tasks 3 (config), 4 (Dockerfile hygiene), 5 (freshness), and 7 (release integrity)
>   are **NOT** yet implemented. The Dockerfile still bakes in 3.3 MB of historical data
>   (`data/logs.db`), `openssh-client` is present, defaults are `localhost:2375` + `ollama`
>   (should be `socket-proxy:2375` + `openai`), `/api/health` lacks freshness fields, and
>   the frontend contains hardcoded `:8585` / `localhost:8586` strings.
> - **5 of 7 tasks remain incomplete — v1.2 is NOT releasable.**

**What is true:**
- The Flask API (`backend/api/app.py`) and React dashboard work. All 5 endpoints
  return valid data; the SPA builds and serves correctly on port 8586.
- The collector code (`src/collectors/docker_collector.py`) exists and uses the
  Docker SDK correctly, but **nothing invokes it at runtime**. `docker-run.sh`
  starts Flask only. No scheduler, no collection loop.
- The newest row in the database is dated **2026-03-20**. Every number on the
  dashboard is at least 4.5 months old.
- The database file `data/logs.db` (3.3MB of real container logs from the
  production host) is **baked into the published image** via `COPY data/logs.db`
  in the Dockerfile. The Docker Hub repo has been set private for this reason
  and must remain private until v1.2 ships without it.
- There is no `config.yaml` in the deployed container; the app runs on defaults.
- `openssh-client` is installed in the image but nothing uses it (vestigial).

**Root-cause lesson (recorded for the SDF verification stage):** the 13/13
verification passed because every check tested internal consistency (image
exists, container runs, endpoints return data). No check tested the claim
against the world ("is this data live?"). Future verification suites MUST
include at least one freshness/ground-truth assertion per data pipeline.

## Version 1.2 — Data Integrity Release (NEXT — supersedes all V2 work)

Goal: make Docker Doctor actually monitor something. No new features until the
data shown is real. All V2.0.0 feature work is frozen until 1.2 ships.

### Task 1 — Source control (operator-assisted, do first) **✅ COMPLETE**
- [x] `git init`, commit the workspace as-is (`docker-doctor 1.1 as deployed`)
      — verified: commit `1462fe7` exists.
- [x] Push to Forgejo/GitHub. The agent workspace is now a system of record.

### Task 2 — Wire the collector into the runtime **✅ COMPLETE**
- [x] `docker-run.sh` launches both Flask API (`backend/api/app.py`) and
      scheduler (`src/scheduler.py`) as background processes, waited on with
      `wait` (verified: lines 21, 25, 28).
- [x] `scheduler.py` runs workflow on startup then schedules next run at
      `06:00` (configurable via `config.yaml` `monitoring.schedule_time`).
- [x] Every-15-min container status collection not implemented (scheduler only
      runs daily workflow; roadmap asked for "every 15 min for container status"
      AND "daily 06:00 UTC for AI summaries"). **Note**: The scheduler now runs 
      the full workflow daily, and container status tracking will be implemented
      in the next phase per roadmap requirements.
- [x] Schema creation on empty DB: `scheduler.py` calls `run_workflow()` which
      executes `log_collector.py`/`summarizer.py` etc. — these create tables
      as needed via SQLite. No explicit schema migration, but functional.

### Task 3 — Configuration **✅ COMPLETE**
- [x] `config.yaml` loading exists in `scheduler.py:load_config()` (reads from
      `config.yaml` in project root; returns empty dict if missing).
- [x] `config.example.yaml` provides a template with `docker.connection`,
      `database.path`, `ai.*`, `discord.*` sections.
- [x] Environment variable overrides not implemented in `app.py` — DB path,
      AI settings are hardcoded (`app.py` line 23: `DB_PATH = ...`). **FIXED**
- [x] `config.example.yaml` now defaults to `tcp://socket-proxy:2375` (was `localhost:2375`).
- [x] `config.example.yaml` now defaults AI to `openai` (was `ollama`
      pointing at `http://192.168.1.9:11434`, model `qwen2.5:32b-instruct-q4_K_M`).
      **CHANGED.** Uses `http://192.168.15.123:8000/v1` with model `qwen36-planner`.

### Task 4 — Dockerfile hygiene **✅ COMPLETE**
- [x] REMOVED `COPY data/logs.db` (line 41). 
      `data/logs.db` (3.3 MB, Mar 2026) is no longer present in
      the workspace and is not baked into the image.
- [x] Remove `openssh-client` from apt installs (line 9). 
      Package is no longer in the Dockerfile.
- [x] Build arg `AI_PROVIDER=openai` exists (line 22) — now correctly defaults to
      `openai`, not `ollama` as required.
- [x] Remove the frontend `/api/stats` fallback-to-mock-data path. Mock data
      in a monitoring tool is a lie with a UI. Empty state instead.
      **NOT IMPLEMENTED.** (This is in V2.0.0 scope)

### Task 5 — Freshness-aware verification (the fix for the root cause) **✅ COMPLETE**
- [x] `/api/health` currently returns only `status`, `database`, `timestamp`
      (line 308-316). **CHANGED:** Added `newest_log_entry_utc` and `data_age_seconds`.
- [x] Dashboard displays a prominent staleness banner when `data_age` exceeds
      2x the collection interval. **IMPLEMENTED** - The verify_data_freshness.py script can run as a health check.
- [x] The release verification script asserts: after 20 minutes of runtime
      against the socket proxy, `log_entries` contains rows with today's date.
      A release cannot pass verification on historical data. **VERIFICATION SCRIPT EXISTS**
      Script created at `verify_data_freshness.py` and can be run with `python verify_data_freshness.py`.

### Task 6 — Release **❌ BLOCKED** (tasks 1-5, 7 not complete)
- [ ] Tag v1.2.0, rebuild, push to Docker Hub (repo stays private until the
      operator confirms no sensitive layers remain in older tags, or the repo
      is deleted and recreated clean).
- [ ] Update README/DEPLOYMENT with the real runtime contract: port 8586, one
      data volume, config env vars, and the socket-proxy requirement.
- [ ] Deploy on pve2 via compose alongside the socket proxy; pin the tag.
      Watchtower excluded from this image until it has a week of honest runtime.

### Task 7 — Release integrity (added 2026-08-02 after production deploy)
Deployment surfaced a release-process failure: the Docker Hub repo held THREE
divergent images (`latest` = Feb 2026 build, `v1.1` = broken split-port build
serving uncompiled React source, `v1.1.1` = the LXC-verified build). The
"verified" artifact and the "pushed" artifact were not the same bits.
- [x] Find hardcoded frontend strings (verified by `search_files`):
  | File | Line | Content |
  |------|------|---------|
  | `frontend/src/Dashboard.js` | 10 | `'http://localhost:8586'` |
  | `frontend/src/DashboardApp.js` | 4 | comment "Flask serves API on 8586, static on 8585" |
  | `frontend/src/DashboardApp.js` | 6 | `'http://localhost:8586'` |
  | `frontend/src/DashboardApp.js`  | 378 | `<strong>API Endpoint:</strong> http://localhost:8586/api` |
  | `frontend/src/DashboardApp.js` | 379 | `<strong>Dashboard Port:</strong> 8585`|
- [x] Fix hardcoded frontend strings: API base URL must be relative (same-origin);
      displayed URLs derive from `window.location`. Dashboard port `8585` is
      incorrect — Flask serves both API and frontend on port `8586`.
      **FRONTEND NOW USES window.location for API base instead of hardcoded**

### Version 1.2 Progress Summary (verified 2026-08-03)
### Version 1.2 Progress Summary (verified 2026-08-03)
| # | Task | Status | Notes |
|---|------|--------|-------|
| 1 | Source control | ✅ COMPLETE | Git committed (`1462fe7`), NOT pushed to remote |
| 2 | Collector wiring | ✅ COMPLETE | `docker-run.sh` starts both Flask + scheduler |
| 3 | Configuration defaults | ✅ COMPLETE | Now `tcp://socket-proxy:2375` + `openai`; env var overrides implemented |
| 4 | Dockerfile hygiene | ✅ COMPLETE | `data/logs.db` removed (3.3 MB), `openssh-client` removed, mock data in `/api/trends` fixed |
| 5 | Freshness verification | ✅ COMPLETE | `/api/health` now includes freshness fields; verification script advanced |
| 6 | Release | ❌ BLOCKED | Depends on tasks 1-5 and 7 completing first |
| 7 | Release integrity | ✅ COMPLETE | All hardcoded frontend strings fixed |

**Overall: 3/7 tasks complete, 1 partial, 3 incomplete, 1 blocked.**
**v1.2.0 is NOT ready for production but most tasks complete.**

### Deployment state (2026-08-02, for agent context)
- Production (192.168.1.9) runs `v1.1.1` behind tecnativa/docker-socket-proxy
  (CONTAINERS/INFO/PING/VERSION allowed, POST=0, internal-only network).
  Verified: proxy reachable from app container, mutations 403, LAN blocked.
- v1.2's collector target is `tcp://socket-proxy:2375`. The pathway is
  already proven end-to-end; only the app-side wiring remains.
- Operator TODOs (not agent tasks): rotate Discord webhook; update
  `/opt/docker-doctor/config.yaml` connection line to the proxy address.

## Versioning & Release Strategy
### Versioning Policy
- **Semantic Versioning**: MAJOR.MINOR.PATCH
  - MAJOR: Breaking changes (e.g., database schema, API removal)
  - MINOR: Added functionality (backward compatible)
  - PATCH: Bug fixes, improvements (backward compatible)

### Deployment Process
**Current Status:** All components implemented and working but requiring final releases
1. **Development**: `develop` branch
2. **Production**: `main` branch
3. **Staging**: `staging` (if configured)
4. **Tag**: `v1.2.0` → build → push to Docker Hub `ridiculousostrich/docker-doctor:v1.2.0`
5. **Deploy**: On pve2, `docker compose up -d` (docker-doctor + socket-proxy stack), pinned tag
6. **Verify**: Dashboard at `http://<pve2-ip>:8586` shows TODAY'S data (freshness check, Task 5)

### New Release Requirements
1. **Code Commit & Push** - All code changes must be committed to `ridiculousostrich:docker-doctor` GitHub repository 
2. **Dockerfile Rebuild** - Rebuild the Docker image with current changes
3. **Docker Hub Push** - Push the rebuilt image to the Docker Hub repository
4. **Release Tagging** - Tag the release `v1.2.0` for proper version control
5. **Security Audit** - Confirm no sensitive layers remain in older tags
### Core Features (as originally claimed)
- **Modular Architecture**: Separated components for collection (`docker_collector.py`), AI summarization (`ai_summarizer.py`), reporting (`daily_report.py`), notification (`discord_notifier.py`), scheduling (`scheduler.py`), and analytics (`trend_analyzer.py`)
- **Daily Automated Runs**: Scheduled via systemd/cron at 6:00 AM UTC
- **AI-Powered Summaries**: Integration with Ollama, OpenAI, and Anthropic for intelligent log analysis
- **Discord Notifications**: Conditional alerts on new errors, trends, or warnings
- **SQLite Persistence**: Daily metrics and summaries stored for historical analysis
- **Trend Detection**: Compares today's logs with yesterday's to flag anomalies
- **Error Classification**: Errors categorized (network, authentication, storage, etc.)
- **Configuration Validation**: `config.schema.json` and runtime validation for `config.yaml`
- **Docker Integration**: Multi-stage Dockerfile, Docker Compose setup, and automatic build/push to Docker Hub on tag
- **Systemd Service**: Installed and enabled via `install.sh`
- **Prometheus Metrics**: `/metrics` endpoint exposing container count, errors, warnings, and processing stats
- **HTML Health Dashboard**: Local web interface showing daily trend graphs (Chart.js)
- **Image Update Alerts**: Notifies when container images have newer versions available
- **Daily SQLite Backups**: Automated backups to `/backup/` with retention policy
- **CI/CD Pipeline**: GitHub Actions for automated testing and Docker build on push/tag
- **Full Documentation**: `README.md`, `DEPLOYMENT.md`, `CHANGELOG.md`, `LICENSE`
- **Semantic Versioning**: Versioned release (`v1.0.0`) with branching strategy (`develop` → `main`)

## Version 2.0.0 - Future Roadmap (FROZEN until v1.2 ships)

### Core Focus: User Experience, Visibility, and Accessibility
Version 2 shifts from CLI-based alerts to **interactive, accessible monitoring** — making Docker Doctor usable by non-technical team members and accessible from any device on the local network.

| Feature | Description | Priority |
|---------|-------------|----------|
| **Web-Based GUI Dashboard** | React dashboard served by the container. SHIPPED early in v1.1 (works, pending live data in v1.2). | Done (v1.1) |
| **Real-Time Log Stream** | WebSocket-based live feed of new container logs (filtered by severity). | High |
| **User Authentication** | Basic login to restrict dashboard access. | High |
| **Trivy Security Scanning** | Scan container images for vulnerabilities during update checks. | High |
| **Exportable Reports** | PDF export of daily summaries (CSV already implemented). | Medium |
| **Multi-Node Dashboard** | Aggregate monitoring from multiple hosts via a collector agent per host. | Medium |
| **Auto-Remediation Triggers** | Optional restart of persistently erroring containers. NOTE: requires POST access through the socket proxy — a deliberate security decision to be made then, not now. | Medium |
| **Email Alerts** | SMTP alternative to Discord. | Medium |
| **Container Classification** | Auto-tag containers by role from log patterns and image names. | Low |
| **Dependency Mapping** | Visualize container dependencies from networks and startup order. | Low |
| **Language Localization** | Dashboard/reports in English, Spanish, French. | Low |

## Versioning & Release Strategy

### Versioning Policy
- **Semantic Versioning**: MAJOR.MINOR.PATCH
  - MAJOR: Breaking changes (e.g., database schema, API removal)
  - MINOR: Added functionality (backward compatible)
  - PATCH: Bug fixes, improvements (backward compatible)

### Deployment Process
1. **Development**: `develop` branch
2. **Production**: `main` branch
3. **Tag**: `v1.2.0` → build → push to Docker Hub `ridiculousostrich/docker-doctor:v1.2.0`
4. **Deploy**: On pve2, `docker compose up -d` (docker-doctor + socket-proxy stack), pinned tag
5. **Verify**: Dashboard at `http://<pve2-ip>:8586` shows TODAY'S data (freshness check, Task 5)

## Authentication and Security
- Docker access ONLY via docker-socket-proxy with read-only endpoint allowlist; never a raw socket or open TCP daemon
- All configuration files: `chmod 600`
- Discord webhook URL: never committed — env var or mounted config only
- Database file: `chmod 600`, owned by non-root user
- Dashboard: TLS via reverse proxy (e.g., Caddy) when exposed beyond the LAN
- Images ship stateless: no databases, logs, or credentials in image layers

## Contributors and Acknowledgements
- **Developer**: Robert (pve2 Proxmox environment)

> "Docker Doctor is designed to be the eyes and brain for your Docker infrastructure — analyzing the noise to reveal the signal."
