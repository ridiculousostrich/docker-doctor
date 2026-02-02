"""
Database schema definitions for Docker log storage.
"""

import sqlite3
from pathlib import Path


def get_database_path():
    """
    Get the path to the SQLite database file.

    Returns:
        Path: Path to logs.db in the data directory
    """
    # Go up from src/database/ to project root, then into data/
    db_path = Path(__file__).parent.parent.parent / "data" / "logs.db"

    # Create data directory if it doesn't exist
    db_path.parent.mkdir(parents=True, exist_ok=True)

    return db_path


def create_tables(conn):
    """
    Create all necessary database tables.

    Args:
        conn: SQLite database connection
    """
    cursor = conn.cursor()

    # Table 1: Track containers we're monitoring
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS containers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            image TEXT,
            first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Table 2: Store individual log entries
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS log_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            container_id INTEGER NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            log_level TEXT,
            message TEXT NOT NULL,
            FOREIGN KEY (container_id) REFERENCES containers(id)
        )
    """)

    # Table 3: Store daily summaries
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS daily_summaries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date DATE NOT NULL,
            container_id INTEGER NOT NULL,
            total_logs INTEGER DEFAULT 0,
            error_count INTEGER DEFAULT 0,
            warning_count INTEGER DEFAULT 0,
            ai_summary TEXT,
            FOREIGN KEY (container_id) REFERENCES containers(id),
            UNIQUE(date, container_id)
        )
    """)

    conn.commit()


def initialize_database():
    """
    Initialize the database with schema.
    Creates the database file and all tables.

    Returns:
        Path: Path to the created database
    """
    db_path = get_database_path()

    # Connect to database (creates file if it doesn't exist)
    conn = sqlite3.connect(db_path)

    # Create all tables
    create_tables(conn)

    # Close connection
    conn.close()

    print(f"Database initialized at: {db_path}")
    return db_path


if __name__ == "__main__":
    # Test: Initialize the database
    initialize_database()
