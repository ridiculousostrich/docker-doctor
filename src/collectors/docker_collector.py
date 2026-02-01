"""
Docker log collector module.
Retrieves logs from Docker containers.
"""

import docker


def get_container_logs(container_name, tail=100):
    """
    Get recent logs from a Docker container.

    Args:
        container_name (str): Name of the container
        tail (int): Number of recent log lines to retrieve

    Returns:
        str: Container logs
    """
    client = docker.from_env()
    container = client.containers.get(container_name)
    logs = container.logs(tail=tail).decode('utf-8')
    return logs


if __name__ == "__main__":
    # Test code
    print("Docker Log Collector - Test Mode")

    # Try to list containers
    try:
        client = docker.from_env()
        containers = client.containers.list()
        print(f"\nFound {len(containers)} running containers:")
        for container in containers:
            print(f"  - {container.name}")
    except Exception as e:
        print(f"\nError connecting to Docker: {e}")
        print("Make sure Docker is running and accessible.")

