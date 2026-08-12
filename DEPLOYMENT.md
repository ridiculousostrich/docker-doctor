# Docker Doctor Deployment Guide

## Deployment to Production

### Prerequisites

- Docker and Docker Compose installed on your server
- (Optional) A Discord webhook URL for notifications
- (Optional) A running Ollama server (or compatible OpenAI-compatible endpoint)

### Deployment Steps

1. Clone the Docker Doctor repository:
   ```bash
   git clone https://github.com/yourusername/docker-doctor.git
   cd docker-doctor
   ```

2. Create a configuration file based on the example:
   ```bash
   cp config.example.yaml config.yaml
   # Edit config.yaml with your actual configuration values
   ```

3. (Recommended) Deploy with Docker Compose for production:
   ```bash
   # Build the Docker image
   docker compose build --build-arg AI_PROVIDER=ollama
   
   # Start the containers
   docker compose up -d
   ```

4. Verify the deployment:
   ```bash
   # Check container status
   docker compose ps
   
   # View logs
   docker compose logs -f docker-doctor
   ```

5. Access the dashboard at: http://localhost:8586

### Port Configuration

- **Dashboard (React + Flask)**: Port 8586
- The Flask API serves the React frontend and REST API on the same port

### Configuration

See `config.example.yaml` for all available options. Key settings to customize:

| Setting | Description |
|---------|-------------|
| `docker.connection` | Docker socket path or socket-proxy TCP address |
| `ai.provider` | AI backend (`ollama` currently supported) |
| `ai.host` | Ollama server URL |
| `ai.model` | Model name (e.g., `qwen2.5:32b-instruct-q4_K_M`) |
| `discord.webhook_url` | Discord webhook for notifications |
| `monitoring.schedule_time` | Daily monitoring time in 24h format |

### Updates

To update to a newer version:

```bash
# Pull the latest changes
git pull origin main

# Rebuild the image
docker compose build --build-arg AI_PROVIDER=ollama

# Restart the containers
docker compose down && docker compose up -d
```

### Troubleshooting

#### Dashboard Not Accessible

- Verify the container is running: `docker compose ps`
- Check if port 8586 is exposed: `docker inspect docker-doctor | grep "8586"`
- Verify your firewall allows traffic on port 8586

#### API Not Responding

- Check the container logs: `docker compose logs docker-doctor`
- Verify the SQLite database exists at `/app/data/logs.db`
- Ensure the database has the correct schema and data

#### AI Summarization Issues

- Verify your Ollama server is running and accessible from the Docker Doctor container
- Check that `ai.host` in config.yaml points to the correct Ollama endpoint
- Verify the model specified in `ai.model` exists on your Ollama server
- Check container logs for AI provider errors

### Using docker-socket-proxy (Recommended)

For security, it's recommended to use `tecnativa/docker-socket-proxy` instead of mounting the Docker socket directly:

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
      - POST=0  # Block mutations
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

### Backup and Recovery

Regularly backup the data volume:

```bash
# Create a backup
docker run --rm -v doctor-data:/source -v $(pwd)/backups:/backup alpine tar -czf /backup/docker-doctor-backup-$(date +%Y%m%d).tar.gz -C /source .

# Restore from backup
docker run --rm -v doctor-data:/target -v $(pwd)/backups:/backup alpine tar -xzf /backup/docker-doctor-backup-YYYYMMDD.tar.gz -C /target
```
