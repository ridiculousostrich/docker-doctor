"""
Unit tests for trend_analyzer.py - Trend analysis over time
"""

import os
import unittest
from datetime import datetime, timedelta
import sqlite3

# Import the module to test
import sys
sys.path.append('/workspace/docker-doctor')
from src.analyzers.trend_analyzer import get_date_comparison, get_new_errors, format_trend_summary


class TestTrendAnalyzer(unittest.TestCase):
    """Test cases for trend analysis functionality."""

    def setUp(self):
        """Create a temporary database before each test."""
        self.db_path = "/tmp/test_trend_db.db"
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS containers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                container_id TEXT,
                name TEXT,
                status TEXT,
                image TEXT,
                created_at TEXT,
                log_count INTEGER,
                error_count INTEGER,
                warning_count INTEGER,
                summary TEXT,
                timestamp TEXT
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_summaries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                container_id INTEGER,
                date TEXT,
                total_logs INTEGER,
                error_count INTEGER,
                warning_count INTEGER,
                FOREIGN KEY (container_id) REFERENCES containers (id)
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS log_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                container_id INTEGER,
                message TEXT,
                log_level TEXT,
                timestamp TEXT,
                FOREIGN KEY (container_id) REFERENCES containers (id)
            )
        ''')
        conn.commit()
        conn.close()

    def tearDown(self):
        """Clean up temporary database after each test."""
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_get_date_comparison_empty(self):
        """Test comparison with no data."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO containers (container_id, name, status, image, created_at, log_count, error_count, warning_count, summary, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            'abc123', 'redis', 'running', 'redis:latest', '2026-07-31T10:00:00Z',
            100, 1, 0, 'Stable', datetime.now().isoformat()
        ))
        conn.commit()
        conn.close()

        comparison = get_date_comparison()
        self.assertEqual(len(comparison), 0)

    def test_get_date_comparison_with_data(self):
        """Test comparison with data from yesterday and today."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Insert container
        cursor.execute('''
            INSERT INTO containers (container_id, name, status, image, created_at, log_count, error_count, warning_count, summary, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            'abc123', 'redis', 'running', 'redis:latest', '2026-07-31T10:00:00Z',
            100, 1, 0, 'Stable', datetime.now().isoformat()
        ))
        container_id = cursor.lastrowid

        # Insert summary for yesterday
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        cursor.execute('''
            INSERT INTO daily_summaries (container_id, date, total_logs, error_count, warning_count)
            VALUES (?, ?, ?, ?, ?)
        ''', (container_id, yesterday, 50, 0, 1))

        # Insert summary for today
        today = datetime.now().strftime('%Y-%m-%d')
        cursor.execute('''
            INSERT INTO daily_summaries (container_id, date, total_logs, error_count, warning_count)
            VALUES (?, ?, ?, ?, ?)
        ''', (container_id, today, 100, 2, 3))

        conn.commit()
        conn.close()

        comparison = get_date_comparison()
        self.assertIn('redis', comparison)
        self.assertEqual(comparison['redis']['today']['logs'], 100)
        self.assertEqual(comparison['redis']['today']['errors'], 2)
        self.assertEqual(comparison['redis']['previous']['errors'], 0)
        self.assertEqual(comparison['redis']['changes']['errors'], 2)

    def test_get_new_errors(self):
        """Test detection of new error messages."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Insert container
        cursor.execute('''
            INSERT INTO containers (container_id, name, status, image, created_at, log_count, error_count, warning_count, summary, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            'abc123', 'redis', 'running', 'redis:latest', '2026-07-31T10:00:00Z',
            100, 1, 0, 'Stable', datetime.now().isoformat()
        ))
        container_id = cursor.lastrowid

        # Insert historical errors
        for msg in ["Connection timeout", "Disk full"]:
            cursor.execute('''
                INSERT INTO log_entries (container_id, message, log_level, timestamp)
                VALUES (?, ?, ?, ?)
            ''', (container_id, msg, 'ERROR', (datetime.now() - timedelta(days=2)).isoformat()))

        # Insert current error (one new, one known)
        current_errors = ["Cannot bind port", "Connection timeout"]
        for msg in current_errors:
            cursor.execute('''
                INSERT INTO log_entries (container_id, message, log_level, timestamp)
                VALUES (?, ?, ?, ?)
            ''', (container_id, msg, 'ERROR', datetime.now().isoformat()))

        conn.commit()
        conn.close()

        new_errors = get_new_errors('redis')
        self.assertEqual(len(new_errors), 1)
        self.assertIn("Cannot bind port", new_errors)
        self.assertNotIn("Connection timeout", new_errors)

    def test_format_trend_summary(self):
        """Test formatting of trend summary text."""
        comparison_data = {
            'redis': {
                'today': {'logs': 100, 'errors': 5, 'warnings': 3},
                'previous': {'logs': 80, 'errors': 3, 'warnings': 2},
                'changes': {'logs': 20, 'errors': 2, 'warnings': 1, 'error_pct': 66.67, 'warning_pct': 50.0}
            }
        }
        
        summary = format_trend_summary('redis', comparison_data)
        self.assertIn("5 errors (↑67% from 3)", summary)
        self.assertIn("3 warnings (↑50% from 2)", summary)

    def test_format_trend_summary_new_errors(self):
        """Test formatting when errors are new."""
        comparison_data = {
            'redis': {
                'today': {'logs': 100, 'errors': 4, 'warnings': 0},
                'previous': {'logs': 80, 'errors': 0, 'warnings': 0},
                'changes': {'logs': 20, 'errors': 4, 'warnings': 0, 'error_pct': float('inf'), 'warning_pct': 0.0}
            }
        }
        
        summary = format_trend_summary('redis', comparison_data)
        self.assertIn("NEW: 4 errors (none yesterday)", summary)


if __name__ == '__main__':
    unittest.main()