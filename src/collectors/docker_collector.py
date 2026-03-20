
"""
Docker log collector module.
Retrieves logs from Docker containers.
"""

import docker
import yaml
from pathlib import Path


def load_config():
    """Load configuration from config.yaml"""
    config_path = Path(__file__).parent.parent.parent / "config.yaml"
    if config_path.exists():
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    return None


def get_docker_client():
    """Get Docker client configured from config.yaml."""
    config = load_config()

    if config and 'docker' in config:
        connection = config['docker'].get('connection', 'unix:///var/run/docker.sock')
        return docker.DockerClient(base_url=connection)

    # Default to local socket if no config
    return docker.from_env()
