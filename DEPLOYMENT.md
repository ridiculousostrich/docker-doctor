# Docker Doctor Deployment Guide

## Deployment to Production

### Prerequisites

- Proxmox VE environment (pve2)
- Docker and Docker Compose installed
- Access to the HAOS VM (if applicable)

### Deployment Steps

1. Ensure your Proxmox environment is properly configured:
   - HAOS VM is running with DHCP reservation for a static IP
   - Docker socket is accessible

2. Clone the Docker Doctor repository:
   ```bash
   git clone https://github.com/yourusername/docker-doctor.git
   cd docker-doctor
   ``"

3. Create a configuration file based on the example:
   ```bash
   cp config.example.yaml config.yaml
   # Edit config.yaml with your actual configuration values
   ```

4. Build and deploy the Docker Doctor application:
   ```bash
   # Build the Docker image with the desired AI provider
   docker-compose build --build-arg AI_PROVIDER=ollama
   
   # Start the containers
   docker-compose up -d
   ```

5. Verify the deployment:
   ```bash
   # Check container status
   docker-compose ps
   
   # View logs
   docker-compose logs -f docker-doctor
   ```

6. Access the dashboard at: http://localhost:8585

### Port Configuration

- **Frontend**: Port 8585 (React UI)
- **Backend API**: Port 8586 (Flask API)

### Firewall Configuration

Ensure your firewall allows traffic on port 8585 for the dashboard:

- If using Proxmox firewall: Allow TCP traffic on port 8585
- If using external firewall: Forward port 8585 to your Proxmox server

### Updates

To update to a newer version:

```bash
# Pull the latest changes
git pull origin main

# Rebuild the image
 docker-compose build --build-arg AI_PROVIDER=ollama

# Restart the containers
docker-compose down && docker-compose up -d
```

### Troubleshooting

#### Dashboard Not Accessible

- Verify the container is running: `docker-compose ps`
- Check if port 8585 is exposed in the container: `docker inspect docker-doctor | grep "8585"`
- Verify your firewall allows traffic on port 8585

#### API Not Responding

- Check the API container logs: `docker-compose logs docker-doctor`
- Verify the SQLite database exists at `/app/data/logs.db`
- Ensure the database has the correct schema and data

#### AI Summarization Issues

- Verify your AI provider (Ollama, OpenAI, etc.) is properly configured
- Check that required API keys or endpoints are correctly set in config.yaml
- Ensure your AI provider is running and accessible

### Backup and Recovery

Regularly backup the data volume:

```bash
# Create a backup of the data volume
mkdir -p /opt/docker-doctor/backups
docker run --rm -v docker-doctor-data:/source -v /opt/docker-doctor/backups:/backup alpine tar -czf /backup/docker-doctor-backup-$(date +%Y%m%d).tar.gz -C /source .

# Restore from backup
docker run --rm -v docker-doctor-data:/target -v /opt/docker-doctor/backups:/backup alpine tar -xzf /backup/docker-doctor-backup-YYYYMMDD.tar.gz -C /target
```
