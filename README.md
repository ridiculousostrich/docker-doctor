# Docker Doctor 🏥

Automated Docker container monitoring with AI-powered log summarization. Collects logs from your containers, analyzes them with a local LLM, and delivers daily health reports via Discord.

## Features

- **Automated Log Collection** — Captures logs from all your Docker containers (or specific ones) on a configurable schedule
- **AI-Powered Analysis** — Summarizes errors, warnings, and patterns using a local Ollama LLM — no data leaves your network
- **Discord Notifications** — Sends daily reports with error trends, warnings, and AI-generated summaries to any Discord channel
- **Web Dashboard** — Real-time React dashboard showing container stats, error trends, and per-container AI summaries
- **Secure by Default** — Designed to work with `docker-socket-proxy` so you never need to expose the Docker socket directly
- **SQLite Storage** — Lightweight, portable database — no external dependencies

## Quick Start

### 1. Create config

```bash
cp config.example.yaml config.yaml
# Edit config.yaml with your settings
```

### 2. Run with Docker

```bash
docker run -d \
  --name docker-doctor \
  -p 8586:8586 \
  -v $(pwd)/config.yaml:/app/config.yaml:ro \
  -v doctor-data:/app/data \
  ridiculousostrich/docker-doctor:v2.0
```

### 3. Open the dashboard

Visit **http://localhost:8586**

## Docker Compose (Recommended)

For a full production setup with docker-socket-proxy:

```yaml
services:
  socket-proxy:
    image: tecnativa/docker-socket-proxy
    container_name: socket-proxy
    environment:
      - CONTAINERS=1
      - INFO=1
      - NETWORKS=1
      - IMAGES=1
      - PING=1
      - VERSION=1
      - POST=0          # Block write operations
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
    networks:
      - doctor-internal

  docker-doctor:
    image: ridiculousostrich/docker-doctor:v2.0
    container_name: docker-doctor
    depends_on:
      - socket-proxy
    ports:
      - "8586:8586"
    volumes:
      - ./config.yaml:/app/config.yaml:ro
      - doctor-data:/app/data
    networks:
      - doctor-internal
    environment:
      - TZ=UTC

networks:
  doctor-internal:
    internal: true

volumes:
  doctor-data:
```

## Configuration

### config.example.yaml

```yaml
docker:
  connection: "tcp://socket-proxy:2375"   # or "unix:///var/run/docker.sock"
  containers: []                            # leave empty to monitor all
  log_days: 1

ai:
  provider: "ollama"                        # currently supported
  host: "http://YOUR_OLLAMA_HOST:11434"
  model: "YOUR_MODEL_NAME"
  temperature: 0.3

discord:
  webhook_url: "https://discord.com/api/webhooks/..."
  notify_on_errors: true
  notify_on_warnings: true
  warning_threshold: 50
  always_send_daily: false

monitoring:
  schedule_time: "06:00"                    # 24h format
```

### Configuration Reference

| Setting | Required | Default | Description |
|---------|----------|---------|-------------|
| `docker.connection` | Yes | — | Docker endpoint: socket-proxy TCP or Docker socket path |
| `docker.containers` | No | `[]` (all) | Specific container names to monitor |
| `docker.log_days` | No | `1` | Days of history to collect per run |
| `ai.provider` | Yes | — | AI backend (`ollama` only currently) |
| `ai.host` | Yes | — | Ollama server URL |
| `ai.model` | Yes | — | Model name (e.g., `qwen2.5:32b-instruct-q4_K_M`) |
| `ai.temperature` | No | `0.3` | LLM temperature for summarization |
| `discord.webhook_url` | Yes | — | Discord webhook URL for notifications |
| `discord.notify_on_errors` | No | `true` | Send notification when errors > 0 |
| `discord.notify_on_warnings` | No | `true` | Send notification when warnings > warning_threshold |
| `discord.warning_threshold` | No | `50` | Minimum warnings to trigger notification |
| `discord.always_send_daily` | No | `false` | Send daily report even with no issues |
| `monitoring.schedule_time` | No | `06:00` | Time to run the daily workflow (24h format) |

## How It Works

1. **Log Collection** — On schedule, the collector connects to the Docker endpoint and pulls container logs for the configured period
2. **Log Analysis** — Logs are analyzed for errors, warnings, and patterns
3. **AI Summarization** — A local Ollama model generates a concise summary of what happened and what needs attention
4. **Discord Report** — A formatted report is sent to your Discord webhook
5. **Dashboard** — All data is stored in SQLite and served via the Flask API + React dashboard on port 8586

## Architecture

```
┌──────────────┐    ┌──────────────────┐    ┌─────────────┐
│   Docker     │◄──►│  docker-socket-  │◄──►│  Docker     │
│  Containers  │    │  proxy (:2375)   │    │  Doctor     │
└──────────────┘    └──────────────────┘    └──────┬──────┘
                                                    │
                                           ┌────────▼──────┐
                                           │  Ollama LLM   │
                                           │  (local)      │
                                           └───────────────┘
```

## Building from Source

```bash
git clone https://github.com/yourusername/docker-doctor.git
cd docker-doctor
docker build -t docker-doctor:local --build-arg AI_PROVIDER=ollama .
```

## License

MIT
