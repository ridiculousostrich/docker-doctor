"""
Main log collection pipeline.
Retrieves logs from Docker containers and stores them in the database.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.collectors.docker_collector import get_docker_client
from src.database.queries import add_container, add_log_entry
from src.analyzers.log_parser import parse_log_line


def collect_logs_from_container(container_name, tail=None):
    """
    Collect logs from a specific container and store in database.

    Args:
        container_name (str): Name of the container
        tail (int): DEPRECATED - now collects last 24 hours

    Returns:
        dict: Summary of collection (container_id, logs_collected)
    """
    print(f"Collecting logs from: {container_name}")

    # Get Docker client
    client = get_docker_client()

    # Get the container
    container = client.containers.get(container_name)

    # Add container to database (or update if exists)
    container_id = add_container(
        name=container.name,
        image=container.image.tags[0] if container.image.tags else None
    )

    # Get logs from last 24 hours
    from datetime import datetime, timedelta

    # Calculate timestamp for 24 hours ago
    since = datetime.now() - timedelta(hours=24)

    # Get logs since that timestamp
    logs = container.logs(since=since).decode('utf-8')

    # Split into individual lines
    log_lines = logs.strip().split('\n')

    print(f"  Found {len(log_lines)} log lines")

    # Store each log line in database
    logs_stored = 0
    for line in log_lines:
        if line.strip():  # Skip empty lines
            # Parse the log line to detect level
            parsed = parse_log_line(line)
            if parsed:
                add_log_entry(
                    container_id=container_id,
                    message=parsed['message'],
                    log_level=parsed['level'],
                    timestamp=parsed.get('timestamp')  # Use extracted timestamp if available
                )
                logs_stored += 1

    print(f"  Stored {logs_stored} log entries in database")

    return {
        "container_id": container_id,
        "container_name": container_name,
        "logs_collected": logs_stored
    }


def collect_logs_from_all_containers(tail=None):
    """
    Collect logs from all running containers.

    Args:
        tail (int): DEPRECATED - now collects last 24 hours

    Returns:
        list: List of collection summaries
    """
    print("Collecting logs from all running containers...")
    print()

    # Get Docker client
    client = get_docker_client()

    # Get all running containers
    containers = client.containers.list()

    print(f"Found {len(containers)} running containers")
    print()

    results = []

    for container in containers:
        try:
            result = collect_logs_from_container(container.name, tail=tail)
            results.append(result)
            print()
        except Exception as e:
            print(f"  ⚠️  Error collecting logs from {container.name}: {e}")
            print()

    return results


if __name__ == "__main__":
    # Test: Collect logs from all containers
    print("=" * 60)
    print("Docker Log Collector - Test Run")
    print("=" * 60)
    print()

    results = collect_logs_from_all_containers(tail=50)

    print("=" * 60)
    print("Collection Summary")
    print("=" * 60)

    total_logs = sum(r["logs_collected"] for r in results)

    print(f"Containers processed: {len(results)}")
    print(f"Total logs collected: {total_logs}")
    print()

    for result in results:
        print(f"  • {result['container_name']}: {result['logs_collected']} logs")
