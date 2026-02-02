"""
Database query functions for inserting and retrieving data.
"""

import sqlite3
from datetime import datetime
try:
    from .schema import get_database_path
except ImportError:
    from schema import get_database_path


def get_connection():
    """
    Get a connection to the database.

    Returns:
        sqlite3.Connection: Database connection
    """
    db_path = get_database_path()
    conn = sqlite3.connect(db_path)
    # Enable foreign key constraints
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def add_container(name, image=None):
    """
    Add or update a container in the database.

    Args:
        name (str): Container name
        image (str): Container image name (optional)

    Returns:
        int: Container ID
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Try to insert, or update last_seen if it already exists
    cursor.execute("""
        INSERT INTO containers (name, image, last_seen)
        VALUES (?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(name) DO UPDATE SET
            last_seen = CURRENT_TIMESTAMP,
            image = COALESCE(excluded.image, image)
    """, (name, image))

    # Get the container ID
    cursor.execute("SELECT id FROM containers WHERE name = ?", (name,))
    container_id = cursor.fetchone()[0]

    conn.commit()
    conn.close()

    return container_id


def add_log_entry(container_id, message, log_level=None):
    """
    Add a log entry to the database.

    Args:
        container_id (int): ID of the container
        message (str): Log message
        log_level (str): Log level (INFO, WARN, ERROR, etc.)

    Returns:
        int: Log entry ID
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO log_entries (container_id, message, log_level)
        VALUES (?, ?, ?)
    """, (container_id, message, log_level))

    log_id = cursor.lastrowid

    conn.commit()
    conn.close()

    return log_id


def add_daily_summary(container_id, date, total_logs, error_count,
                      warning_count, ai_summary=None):
    """
    Add or update a daily summary.

    Args:
        container_id (int): ID of the container
        date (str): Date in YYYY-MM-DD format
        total_logs (int): Total number of log entries
        error_count (int): Number of errors
        warning_count (int): Number of warnings
        ai_summary (str): AI-generated summary (optional)

    Returns:
        int: Summary ID
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO daily_summaries
            (date, container_id, total_logs, error_count, warning_count, ai_summary)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(date, container_id) DO UPDATE SET
            total_logs = excluded.total_logs,
            error_count = excluded.error_count,
            warning_count = excluded.warning_count,
            ai_summary = COALESCE(excluded.ai_summary, ai_summary)
    """, (date, container_id, total_logs, error_count, warning_count, ai_summary))

    summary_id = cursor.lastrowid

    conn.commit()
    conn.close()

    return summary_id


def get_container_logs(container_id, limit=100):
    """
    Get recent logs for a container.

    Args:
        container_id (int): ID of the container
        limit (int): Maximum number of logs to retrieve

    Returns:
        list: List of tuples (timestamp, log_level, message)
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT timestamp, log_level, message
        FROM log_entries
        WHERE container_id = ?
        ORDER BY timestamp DESC
        LIMIT ?
    """, (container_id, limit))

    logs = cursor.fetchall()
    conn.close()

    return logs


if __name__ == "__main__":
    # Test the functions
    print("Testing database queries...")

    # Add a test container
    container_id = add_container("test-container", "nginx:latest")
    print(f"✓ Added container with ID: {container_id}")

    # Add some test log entries
    log_id1 = add_log_entry(container_id, "Server started successfully", "INFO")
    log_id2 = add_log_entry(container_id, "Connection timeout", "WARN")
    log_id3 = add_log_entry(container_id, "Database connection failed", "ERROR")
    print(f"✓ Added 3 log entries (IDs: {log_id1}, {log_id2}, {log_id3})")

    # Add a daily summary
    today = datetime.now().strftime("%Y-%m-%d")
    summary_id = add_daily_summary(
        container_id=container_id,
        date=today,
        total_logs=3,
        error_count=1,
        warning_count=1,
        ai_summary="Test container had 1 error and 1 warning today."
    )
    print(f"✓ Added daily summary with ID: {summary_id}")

    # Retrieve logs
    logs = get_container_logs(container_id, limit=10)
    print(f"\n✓ Retrieved {len(logs)} logs:")
    for timestamp, level, message in logs:
        print(f"  [{timestamp}] {level}: {message}")

    print("\n✅ All tests passed!")
