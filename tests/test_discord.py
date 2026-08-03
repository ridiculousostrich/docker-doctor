"""
Unit tests for discord_notifier.py - Discord webhook notifications
"""

import os
import unittest
from unittest.mock import patch, Mock
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.reporters.discord_notifier import send_discord_notification, should_send_notification


class TestDiscordNotifier(unittest.TestCase):
    """Test cases for Discord notification functionality."""

    def setUp(self):
        """Set up test environment."""
        # Mock config file
        self.test_config = {
            'discord': {
                'webhook_url': 'https://discord.com/api/webhooks/test',
                'notify_on_errors': True,
                'notify_on_warnings': True,
                'warning_threshold': 50,
                'always_send_daily': False
            }
        }

    @patch('src.reporters.discord_notifier.DiscordWebhook')
    def test_send_discord_notification_success(self, mock_webhook):
        """Test successful notification send."""
        # Mock webhook response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_webhook_instance = Mock()
        mock_webhook_instance.execute.return_value = mock_response
        mock_webhook.return_value = mock_webhook_instance
        
        report_data = {
            'total_containers': 3,
            'total_logs': 152,
            'total_errors': 2,
            'total_warnings': 1,
            'containers_with_errors': 1,
            'problem_containers': [{'name': 'redis', 'errors': 2, 'warnings': 0}],
            'healthy_containers': [{'name': 'nginx'}]
        }
        
        result = send_discord_notification(report_data)
        
        self.assertTrue(result)
        mock_webhook.assert_called_once()
        mock_webhook_instance.add_embed.assert_called_once()

    @patch('src.reporters.discord_notifier.DiscordWebhook')
    def test_send_discord_notification_failure(self, mock_webhook):
        """Test failed notification send (server error)."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_webhook_instance = Mock()
        mock_webhook_instance.execute.return_value = mock_response
        mock_webhook.return_value = mock_webhook_instance
        
        report_data = {
            'total_containers': 2,
            'total_logs': 89,
            'total_errors': 8,
            'total_warnings': 5,
            'containers_with_errors': 1,
            'problem_containers': [{'name': 'postgres', 'errors': 8, 'warnings': 0}],
            'healthy_containers': []
        }
        
        result = send_discord_notification(report_data)
        
        self.assertFalse(result)

    @patch('src.reporters.discord_notifier.DiscordWebhook')
    def test_send_discord_notification_no_config(self, mock_webhook):
        """Test notification with missing config."""
        result = send_discord_notification({})
        
        self.assertFalse(result)
        mock_webhook.assert_not_called()

    @patch('src.reporters.discord_notifier.DiscordWebhook')
    def test_send_discord_notification_invalid_webhook(self, mock_webhook):
        """Test notification with invalid webhook URL."""
        # Temporarily modify the config
        import src.reporters.discord_notifier as dn
        old_load_config = dn.load_config
        dn.load_config = lambda: {
            'discord': {
                'webhook_url': 'YOUR_WEBHOOK',
                'notify_on_errors': True
            }
        }
        
        try:
            result = send_discord_notification({})
            self.assertFalse(result)
        finally:
            dn.load_config = old_load_config

    def test_should_send_notification_always(self):
        """Test notification when always_send_daily is True."""
        config = {'discord': {'always_send_daily': True}}
        report_data = {'total_errors': 0, 'total_warnings': 0}
        
        self.assertTrue(should_send_notification(report_data, config))

    def test_should_send_notification_with_errors(self):
        """Test notification when errors detected and notify_on_errors is True."""
        config = {'discord': {'notify_on_errors': True}}
        report_data = {'total_errors': 5, 'total_warnings': 0}
        
        self.assertTrue(should_send_notification(report_data, config))

    def test_should_send_notification_no_errors(self):
        """Test no notification when no errors and always_send_daily=False."""
        config = {'discord': {'always_send_daily': False, 'notify_on_errors': True}}
        report_data = {'total_errors': 0, 'total_warnings': 0}
        
        self.assertFalse(should_send_notification(report_data, config))

    def test_should_send_notification_warnings_above_threshold(self):
        """Test notification when warnings exceed threshold."""
        config = {'discord': {'notify_on_warnings': True, 'warning_threshold': 10}}
        report_data = {'total_errors': 0, 'total_warnings': 15}
        
        self.assertTrue(should_send_notification(report_data, config))

    def test_should_send_notification_warnings_below_threshold(self):
        """Test no notification when warnings below threshold."""
        config = {'discord': {'notify_on_warnings': True, 'warning_threshold': 20}}
        report_data = {'total_errors': 0, 'total_warnings': 15}
        
        self.assertFalse(should_send_notification(report_data, config))


if __name__ == '__main__':
    unittest.main()