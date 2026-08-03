"""
Unit tests for queries.py - SQLite database operations
"""

import os
import unittest
import tempfile
import sqlite3
from datetime import datetime, timedelta

# Import the module to test
import sys
sys.path.append('/workspace/docker-doctor')
from src.database.queries import init_db, save_container_data, get_daily_summary, get_trend_data


class TestQueries(unittest.TestCase):
    """Test cases for database functions."""

    def setUp(self):
        """Create a temporary database file before each test."""
        self.db_path = tempfile.mktemp(suffix='.db')
        init_db(self.db_path)
        
    def tearDown(self):
        """Clean up temporary database after each test."""
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
    
    def test_init_db_creates_table(self):
        """Test that init_db creates the containers table."""
        # Execute a query to verify table exists
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='containers'
        """)
        result = cursor.fetchone()
        conn.close()
        self.assertIsNotNone(result, "containers table was not created")
        
    def test_save_container_data(self):
        """Test saving container data."""
        sample_data = {
            'container_id': 'abc123',
            'name': 'redis',
            'status': 'running',
            'image': 'redis:latest',
            'created_at': '2026-08-01T10:00:00Z',
            'log_count': 47,
            'error_count': 3,
            'warning_count': 1,
            'summary': 'Redis is stable. No critical errors.',
            'timestamp': datetime.now().isoformat()
        }
        
        save_container_data(self.db_path, sample_data)
        
        # Verify data was stored
        summary = get_daily_summary(self.db_path, datetime.now().date())
        self.assertIsNotNone(summary)
        self.assertEqual(summary['error_count'], 3)
        self.assertEqual(summary['log_count'], 47)
        
    def test_get_daily_summary(self):
        """Test retrieving daily summary."""
        # Insert test data
        sample_data = {
            'container_id': 'def456',
            'name': 'nginx',
            'status': 'running',
            'image': 'nginx:alpine',
            'created_at': '2026-08-01T10:00:00Z',
            'log_count': 102,
            'error_count': 0,
            'warning_count': 2,
            'summary': 'Nginx serving traffic normally.',
            'timestamp': datetime.now().isoformat()
        }
        save_container_data(self.db_path, sample_data)
        
        summary = get_daily_summary(self.db_path, datetime.now().date())
        self.assertEqual(summary['log_count'], 102)
        self.assertEqual(summary['error_count'], 0)
        
    def test_get_trend_data(self):
        """Test retrieving trend data over multiple days."""
        # Insert data for two days
        today = datetime.now()
        yesterday = today - timedelta(days=1)
        
        data_yesterday = {
            'container_id': 'ghi789',
            'name': 'postgres',
            'status': 'running',
            'image': 'postgres:15',
            'created_at': '2026-07-31T10:00:00Z',
            'log_count': 50,
            'error_count': 2,
            'warning_count': 0,
            'summary': 'PostgreSQL is stable.',
            'timestamp': yesterday.isoformat()
        }
        
        data_today = {
            'container_id': 'ghi789',
            'name': 'postgres',
            'status': 'running',
            'image': 'postgres:15',
            'created_at': '2026-08-01T10:00:00Z',
            'log_count': 60,
            'error_count': 0,
            'warning_count': 1,
            'summary': 'PostgreSQL is stable.',
            'timestamp': today.isoformat()
        }
        
        save_container_data(self.db_path, data_yesterday)
        save_container_data(self.db_path, data_today)
        
        trends = get_trend_data(self.db_path, 2)
        self.assertEqual(len(trends), 2)
        self.assertEqual(trends[0]['error_count'], 0)
        self.assertEqual(trends[1]['error_count'], 2)


if __name__ == '__main__':
    unittest.main() 