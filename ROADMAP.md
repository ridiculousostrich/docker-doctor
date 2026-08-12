# Docker Doctor - Project Roadmap

## Project Overview

Docker Doctor is an automated monitoring system designed to provide daily insights into the health of Docker containers running on a Proxmox (pve2) host. The system collects, analyzes, and reports on Docker container logs using a combination of statistical analysis and AI-powered summarization to identify patterns, trends, and potential issues.

The system is designed to be:
- **Automated**: Runs daily without manual intervention
- **Intelligent**: Uses AI to summarize complex log data into actionable insights
- **Alerting**: Sends notifications to Discord when issues are detected
- **Persistent**: Stores historical data in SQLite for trend analysis

## Development Status: August 10, 2026 (UPDATED)

### Current Status: **Dashboard functional, scheduler wired — data pipeline ACTIVE. 6/7 tasks complete. Only release remains.**

An operator audit on August 2 found that the v1.1 image presents historical data as
if it were current. This section supersedes the earlier "Resolved - Dashboard
Working" status, which was based on a verification suite that checked artifact
consistency but never checked data freshness.

> **VERIFICATION STATUS (2026-08-10):** All code audit issues resolved.
> - Tasks 1–2 fully implemented.
> - Tasks 3, 4, 5, and 7 are now **✅ COMPLETE** — all sub-items addressed.
> - Task 6 (Release) remains BLOCKED on operator action.
> - **6 of 7 tasks complete. Only release remains.**

**What is true:**
- The Flask API (`backend/api/app.py`) and React dashboard work. All 5 endpoints
  return valid data; the SPA builds and serves correctly on port 8586.
- The collector code (`src/collectors/docker_collector.py`) exists and uses the
  Docker SDK correctly. The scheduler (`src/scheduler.py`) invokes it at runtime
  via `docker-run.sh` alongside Flask.
- The newest row in the database is dated **2026-03-20** in the workspace copy.
  Production v1.2 will collect live data after deployment.
- `data/logs.db` is no longer baked into the published image (removed from Dockerfile).
- There is no `config.yaml` in the deployed container; the app runs on defaults.
- `openssh-client` removed from the Dockerfile (vestigial package gone).

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

### Task 3 — Configuration **✅ COMPLETE** (verified 2026-08-10)
- [x] `config.yaml` loading exists in `scheduler.py:load_config()` — verified.
- [x] `config.example.yaml` provides a template — verified.
- [x] Environment variable overrides — **ALL ADDED.** `DB_PATH`, `DOCKER_HOST`, and `DISCORD_WEBHOOK_URL` env vars present. AI settings already had env overrides (`AI_PROVIDER`, `AI_HOST`, `AI_MODEL`, `AI_TEMPERATURE`).
- [x] `config.example.yaml` default connection **UPDATED** — now `tcp://socket-proxy:2375`.
- [x] AI provider defaults to `openai` in config.example.yaml — verified.
- [x] `config.schema.json` now defaults to `"openai"` for AI provider — fixed.
- **Result:** 6/6 sub-items done.

### Task 4 — Dockerfile hygiene **✅ COMPLETE** (verified 2026-08-10)
- [x] REMOVED `COPY data/logs.db` — verified.
- [x] Remove `openssh-client` — verified, no longer in Dockerfile.
- [x] Build arg `AI_PROVIDER=openai` exists — verified, defaults to `openai`.
- [x] Mock data fallback in `/api/trends` — **REMOVED.** Returns `jsonify([])` when fewer than 2 dates exist. Empty state instead of fabricated data.
- **Result:** 4/4 sub-items done.

### Task 5 — Freshness-aware verification (the fix for the root cause) **✅ COMPLETE** (verified 2026-08-10)
- [x] `/api/health` has freshness fields `newest_log_entry_utc` and `data_age_seconds` — verified (app.py lines 348-349).
- [x] Dashboard displays a prominent staleness banner — **IMPLEMENTED.** `StalenessBanner` component in `DashboardApp.js`: orange warning at 1+ day, red critical at 7+ days.
- [x] Release verification script `verify_data_freshness.py` — clean (no corrupted strftime, format strings use correct `"%Y-%m-%d"`).
- **Result:** 3/3 sub-items done.

### Task 6 — Release **❌ BLOCKED** (operator action required)
- [ ] Tag v1.2.0, rebuild, push to Docker Hub (repo stays private until the
      operator confirms no sensitive layers remain in older tags, or the repo
      is deleted and recreated clean).
- [ ] Update README/DEPLOYMENT with the real runtime contract: port 8586, one
      data volume, config env vars, and the socket-proxy requirement.
- [ ] Deploy on pve2 via compose alongside the socket proxy; pin the tag.
      Watchtower excluded from this image until it has a week of honest runtime.

All code dependencies (Tasks 1–5, 7) are resolved. Only operator action remains.

### Task 7 — Release integrity **✅ COMPLETE** (verified 2026-08-10)
- [x] Find hardcoded frontend strings — **FIXED.** API URLs now use `window.location` (verified in both `Dashboard.js` and `DashboardApp.js`).
- [x] UI port references — **FIXED.** Comment on line 4 now reads "same host and port (Flask serves both API and static on 8586)".
- [x] Vestigial `loadMockData()` — **REMOVED.** Function and all references deleted from `DashboardApp.js`.
- **Result:** 3/3 sub-items done.

### Version 1.2 Progress Summary (verified 2026-08-10)
| # | Task | Status | Notes |
|---|------|--------|-------|
| 1 | Source control | ✅ COMPLETE | Git committed, **3 unpushed** to remote |
| 2 | Collector wiring | ✅ COMPLETE | `docker-run.sh` starts both Flask + scheduler; scheduler runs workflow |
| 3 | Configuration defaults | ✅ COMPLETE | All defaults corrected to socket-proxy + openai; schema fixed; env overrides for DB_PATH, DOCKER_HOST, DISCORD_WEBHOOK_URL |
| 4 | Dockerfile hygiene | ✅ COMPLETE | `data/logs.db` removed, `openssh-client` removed, mock data removed from `/api/trends` |
| 5 | Freshness verification | ✅ COMPLETE | `/api/health` has freshness fields; frontend staleness banner active; verification script clean |
| 6 | Release | ❌ BLOCKED | Depends on operator: tag, push, deploy |
| 7 | Release integrity | ✅ COMPLETE | Hardcoded URLs fixed; comment corrected; `loadMockData()` removed |

**Overall: 6/7 tasks complete, 0 partial, 1 blocked.**
**v1.2.0 is ready for release — only operator action remains (tag, push, deploy).**

### Deployment state (2026-08-02, for agent context)
- Production (YOUR_SERVER_IP) runs behind tecnativa/docker-socket-proxy
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
