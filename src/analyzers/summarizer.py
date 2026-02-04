"""
Generate daily summaries from collected logs.
"""

import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.database.queries import get_connection, add_daily_summary


def generate_daily_summary(container_id, date=None):
    """
    Generate a daily summary for a specific container.

    Args:
        container_id (int): ID of the container
        date (str): Date in YYYY-MM-DD format (defaults to today)

    Returns:
        dict: Summary statistics
    """
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")

    conn = get_connection()
    cursor = conn.cursor()

    # Get container name
    cursor.execute("SELECT name FROM containers WHERE id = ?", (container_id,))
    container_name = cursor.fetchone()[0]

    # Count total logs for this container on this date
    cursor.execute("""
        SELECT COUNT(*)
        FROM log_entries
        WHERE container_id = ?
        AND DATE(timestamp) = ?
    """, (container_id, date))
    total_logs = cursor.fetchone()[0]

    # Count errors
    cursor.execute("""
        SELECT COUNT(*)
        FROM log_entries
        WHERE container_id = ?
        AND DATE(timestamp) = ?
        AND log_level = 'ERROR'
    """, (container_id, date))
    error_count = cursor.fetchone()[0]

    # Count warnings
    cursor.execute("""
        SELECT COUNT(*)
        FROM log_entries
        WHERE container_id = ?
        AND DATE(timestamp) = ?
        AND log_level = 'WARN'
    """, (container_id, date))
    warning_count = cursor.fetchone()[0]

    # Generate simple text summary
    summary_text = f"{container_name}: {total_logs} logs"
    if error_count > 0:
        summary_text += f", {error_count} errors"
    if warning_count > 0:
        summary_text += f", {warning_count} warnings"
    if error_count == 0 and warning_count == 0:
        summary_text += " - All clear"

    conn.close()

    # Store the summary in database
    add_daily_summary(
        container_id=container_id,
        date=date,
        total_logs=total_logs,
        error_count=error_count,
        warning_count=warning_count,
        ai_summary=summary_text
    )

    return {
        "container_id": container_id,
        "container_name": container_name,
        "date": date,
        "total_logs": total_logs,
        "error_count": error_count,
        "warning_count": warning_count,
        "summary": summary_text
    }


def generate_all_summaries(date=None):
    """
    Generate daily summaries for all containers.

    Args:
        date (str): Date in YYYY-MM-DD format (defaults to today)

    Returns:
        list: List of summary dictionaries
    """
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")

    print(f"Generating daily summaries for {date}")
    print("=" * 60)
    print()

    conn = get_connection()
    cursor = conn.cursor()

    # Get all containers that have logs on this date
    cursor.execute("""
        SELECT DISTINCT c.id, c.name
        FROM containers c
        JOIN log_entries l ON c.id = l.container_id
        WHERE DATE(l.timestamp) = ?
        ORDER BY c.name
    """, (date,))

    containers = cursor.fetchall()
    conn.close()

    summaries = []

    for container_id, container_name in containers:
        summary = generate_daily_summary(container_id, date)
        summaries.append(summary)

        # Print status
        status = "✅" if summary["error_count"] == 0 else "⚠️"
        print(f"{status} {summary['summary']}")

    print()
    print("=" * 60)
    print(f"Generated {len(summaries)} summaries")

    return summaries


if __name__ == "__main__":
    # Test: Generate summaries for today
    summaries = generate_all_summaries()

    # Print overall statistics
    print()
    print("Overall Statistics:")
    print("-" * 60)

    total_logs = sum(s["total_logs"] for s in summaries)
    total_errors = sum(s["error_count"] for s in summaries)
    total_warnings = sum(s["warning_count"] for s in summaries)
    containers_with_errors = sum(1 for s in summaries if s["error_count"] > 0)

    print(f"Total containers: {len(summaries)}")
    print(f"Total logs: {total_logs}")
    print(f"Total errors: {total_errors}")
    print(f"Total warnings: {total_warnings}")
    print(f"Containers with errors: {containers_with_errors}")
