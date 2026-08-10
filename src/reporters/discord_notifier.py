"""
Discord notification system for daily reports.
"""

import sys
import os
from pathlib import Path
import yaml
from discord_webhook import DiscordWebhook, DiscordEmbed
from datetime import datetime
from src.utils.retry import retry_discord_call

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


def load_config():
    """Load configuration from config.yaml"""
    config_path = Path(__file__).parent.parent.parent / "config.yaml"
    if config_path.exists():
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    return None


@retry_discord_call
def send_discord_notification(report_data, report_file_path=None):
    """
    Send a Discord notification with the daily report.

    Args:
        report_data (dict): Report data with keys:
            - total_containers: int
            - total_logs: int
            - total_errors: int
            - total_warnings: int
            - containers_with_errors: int
            - problem_containers: list of dicts
            - healthy_containers: list of dicts
        report_file_path (Path): Optional path to full report text file
    """
    config = load_config()

    # Check env var first, then config
    webhook_url = os.environ.get("DISCORD_WEBHOOK_URL", "")

    if not webhook_url:
        if not config or 'discord' not in config:
            print("Discord not configured in config.yaml")
            return False
        webhook_url = config['discord']['webhook_url']

    if 'YOUR_WEBHOOK' in webhook_url:
        print("Please update webhook_url in config.yaml")
        return False

    # Create webhook
    webhook = DiscordWebhook(url=webhook_url, username="Docker Monitor")

    # Determine overall health color
    if report_data['total_errors'] == 0 and report_data['total_warnings'] == 0:
        color = 0x00FF00  # Green
        status = "🟢 All Systems Healthy"
    elif report_data['total_errors'] == 0:
        color = 0xFFFF00  # Yellow
        status = f"🟡 {report_data['total_warnings']} Warnings Detected"
    elif report_data['total_errors'] < 10:
        color = 0xFFA500  # Orange
        status = f"🟠 {report_data['total_errors']} Errors Detected"
    else:
        color = 0xFF0000  # Red
        status = f"🔴 {report_data['total_errors']} Errors - Attention Needed"

    # Create main embed
    embed = DiscordEmbed(
        title=f"Docker Container Daily Report - {datetime.now().strftime('%Y-%m-%d')}",
        description=status,
        color=color
    )

    # Add overview fields
    embed.add_embed_field(
        name="📊 Overview",
        value=f"**Containers:** {report_data['total_containers']}\n"
              f"**Total Logs:** {report_data['total_logs']:,}\n"
              f"**Errors:** {report_data['total_errors']}\n"
              f"**Warnings:** {report_data['total_warnings']}",
        inline=False
    )

    # Add problem containers if any
    if report_data['problem_containers']:
        problem_list = []
        for container in report_data['problem_containers'][:5]:  # Limit to 5
            name = container['name']
            errors = container['errors']
            warnings = container['warnings']

            if errors > 0:
                problem_list.append(f"🔴 **{name}**: {errors} errors, {warnings} warnings")
            else:
                problem_list.append(f"🟡 **{name}**: {warnings} warnings")

        if len(report_data['problem_containers']) > 5:
            problem_list.append(f"... and {len(report_data['problem_containers']) - 5} more")

        embed.add_embed_field(
            name="⚠️ Containers Needing Attention",
            value="\n".join(problem_list),
            inline=False
        )

    # Add healthy container count
    healthy_count = len(report_data['healthy_containers'])
    embed.add_embed_field(
        name="✅ Healthy Containers",
        value=f"{healthy_count} containers running smoothly",
        inline=False
    )

    # Add note about full report
    if report_file_path:
        embed.add_embed_field(
            name="📄 Full Report",
            value="See attached file for complete analysis with AI summaries and trend data",
            inline=False
        )

    # Add footer
    embed.set_footer(text=f"Generated at {datetime.now().strftime('%H:%M:%S')}")

    webhook.add_embed(embed)

    # Attach the full report file if provided
    if report_file_path and report_file_path.exists():
        with open(report_file_path, "rb") as f:
            webhook.add_file(file=f.read(), filename=report_file_path.name)

    # Send it
    response = webhook.execute()

    if response.status_code == 200 or response.status_code == 204:
        print(f"✅ Discord notification sent successfully")
        return True
    else:
        print(f"❌ Failed to send Discord notification: {response.status_code}")
        return False


def should_send_notification(report_data, config):
    """
    Determine if a notification should be sent based on config rules.

    Args:
        report_data (dict): Report data
        config (dict): Configuration from config.yaml

    Returns:
        bool: True if notification should be sent
    """
    discord_config = config.get('discord', {})

    # Always send if configured
    if discord_config.get('always_send_daily', False):
        return True

    # Send if errors detected and configured to do so
    if report_data['total_errors'] > 0 and discord_config.get('notify_on_errors', True):
        return True

    # Send if warnings exceed threshold
    warning_threshold = discord_config.get('warning_threshold', 50)
    if report_data['total_warnings'] > warning_threshold and discord_config.get('notify_on_warnings', True):
        return True

    return False


if __name__ == "__main__":
    # Test notification
    test_data = {
        'total_containers': 18,
        'total_logs': 3104,
        'total_errors': 279,
        'total_warnings': 1346,
        'containers_with_errors': 5,
        'problem_containers': [
            {'name': 'immich_server', 'errors': 154, 'warnings': 1},
            {'name': 'immich_microservices', 'errors': 107, 'warnings': 0},
            {'name': 'grafana', 'errors': 11, 'warnings': 0},
        ],
        'healthy_containers': [
            {'name': 'prometheus'},
            {'name': 'portainer'},
        ]
    }

    print("Sending test Discord notification...")

    # Try to attach the most recent report if it exists
    from pathlib import Path
    data_dir = Path(__file__).parent.parent.parent / "data"
    report_files = sorted(data_dir.glob("report_*.txt"), reverse=True)
    report_path = report_files[0] if report_files else None

    send_discord_notification(test_data, report_path)
