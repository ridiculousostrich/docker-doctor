"""
Unit tests for ai_summarizer.py - AI-powered log summarization
"""

import os
import unittest
import tempfile

# Import the module to test
import sys
sys.path.append('/workspace/docker-doctor')
from ai_summarizer import summarize_logs


class TestAISummarizer(unittest.TestCase):
    """Test cases for AI summarization functionality."""

    def test_summarize_logs_no_errors(self):
        """Test summarization with clean logs."""
        logs = [
            "[INFO] Container started successfully",
            "[INFO] Connection accepted from 192.168.1.10",
            "[INFO] Request processed in 12ms"
        ]
        
        summary = summarize_logs(logs)
        self.assertIsInstance(summary, str)
        self.assertGreater(len(summary), 0)
        self.assertNotIn("error", summary.lower())

    def test_summarize_logs_with_errors(self):
        """Test summarization with error logs."""
        logs = [
            "[ERROR] Database connection failed",
            "[ERROR] Timeout while fetching data",
            "[INFO] Retrying connection..."
        ]
        
        summary = summarize_logs(logs)
        self.assertIsInstance(summary, str)
        self.assertGreater(len(summary), 0)
        self.assertIn("error", summary.lower())

    def test_summarize_logs_empty(self):
        """Test summarization with empty log list."""
        logs = []
        summary = summarize_logs(logs)
        self.assertIsInstance(summary, str)
        self.assertIn("no log data", summary.lower())

    def test_summarize_logs_large_input(self):
        """Test summarization with large number of logs."""
        logs = [f"[INFO] Log entry {i}" for i in range(100)]
        summary = summarize_logs(logs)
        self.assertIsInstance(summary, str)
        self.assertGreater(len(summary), 0)


if __name__ == '__main__':
    unittest.main()