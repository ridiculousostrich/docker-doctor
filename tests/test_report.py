"""
Unit tests for daily_report.py - Daily health report generation
"""

import os
import unittest

# Import the module to test
import sys
sys.path.append('/workspace/docker-doctor')
from daily_report import generate_daily_report


class TestDailyReport(unittest.TestCase):
    """Test cases for daily report generation."""

    def test_generate_daily_report_basic(self):
        """Test report generation with minimal data."""
        daily_summary = {
            'total_containers': 3,
            'running': 3,
            'stopped': 0,
            'total_logs': 152,
            'total_errors': 2,
            'total_warnings': 1,
            'health_status': '🟡',
            'new_errors': ['Database connection timeout'],
            'summary': 'System is partially degraded. One new error detected.'
        }
        
        report = generate_daily_report(daily_summary)
        self.assertIsInstance(report, str)
        self.assertIn('Docker Doctor Daily Report', report)
        self.assertIn('🟡', report)
        self.assertIn('2 errors', report)

    def test_generate_daily_report_health_green(self):
        """Test report with healthy status."""
        daily_summary = {
            'total_containers': 5,
            'running': 5,
            'stopped': 0,
            'total_logs': 210,
            'total_errors': 0,
            'total_warnings': 0,
            'health_status': '🟢',
            'new_errors': [],
            'summary': 'All containers are healthy.'
        }
        
        report = generate_daily_report(daily_summary)
        self.assertIn('🟢', report)
        self.assertNotIn('error', report.lower())

    def test_generate_daily_report_health_red(self):
        """Test report with critical status."""
        daily_summary = {
            'total_containers': 2,
            'running': 0,
            'stopped': 2,
            'total_logs': 45,
            'total_errors': 8,
            'total_warnings': 5,
            'health_status': '🔴',
            'new_errors': ['Container crashed', 'Network unreachable'],
            'summary': 'Critical failure. Multiple containers offline.'
        }
        
        report = generate_daily_report(daily_summary)
        self.assertIn('🔴', report)
        self.assertIn('Critical', report)
        self.assertIn('8 errors', report)

    def test_generate_daily_report_no_new_errors(self):
        """Test report when no new errors detected."""
        daily_summary = {
            'total_containers': 4,
            'running': 4,
            'stopped': 0,
            'total_logs': 89,
            'total_errors': 1,
            'total_warnings': 2,
            'health_status': '🟡',
            'new_errors': [],
            'summary': 'System is stable.'
        }
        
        report = generate_daily_report(daily_summary)
        self.assertIn('No new errors detected', report)


if __name__ == '__main__':
    unittest.main()