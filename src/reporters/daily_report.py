"""
Generate daily reports from summaries.
"""

import sys
import textwrap
from pathlib import Path
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.database.queries import get_connection
from src.reporters.discord_notifier import send_discord_notification, should_send_notification, load_config
from src.analyzers.trend_analyzer import get_date_comparison, format_trend_summary, get_new_errors


def generate_daily_report(date=None):
    """
    Generate a formatted daily report.

    Args:
        date (str): Date in YYYY-MM-DD format (defaults to today)

    Returns:
        tuple: (report_text, report_data)
            - report_text (str): Formatted report text
            - report_data (dict): Structured data for notifications
    """
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")

    conn = get_connection()
    cursor = conn.cursor()

    # Get all containers with their summaries (including those with no logs)
    cursor.execute("""
        SELECT
            c.name,
            COALESCE(s.total_logs, 0) as total_logs,
            COALESCE(s.error_count, 0) as error_count,
            COALESCE(s.warning_count, 0) as warning_count,
            s.ai_summary
        FROM containers c
        LEFT JOIN daily_summaries s ON c.id = s.container_id AND s.date = ?
        ORDER BY
            COALESCE(s.error_count, 0) DESC,
            COALESCE(s.warning_count, 0) DESC,
            c.name
    """, (date,))

    summaries = cursor.fetchall()

    # Calculate overall statistics (count ALL containers, not just those with logs)
    cursor.execute("""
        SELECT
            COUNT(DISTINCT c.id) as container_count,
            COALESCE(SUM(s.total_logs), 0) as total_logs,
            COALESCE(SUM(s.error_count), 0) as total_errors,
            COALESCE(SUM(s.warning_count), 0) as total_warnings
        FROM containers c
        LEFT JOIN daily_summaries s ON c.id = s.container_id AND s.date = ?
    """, (date,))

    stats = cursor.fetchone()
    conn.close()

    # Get trend data for comparison
    trend_data = get_date_comparison(date)

    # Build the report
    report = []
    report.append("=" * 70)
    report.append(f"DOCKER CONTAINER DAILY REPORT - {date}")
    report.append("=" * 70)
    report.append("")

    # Overall summary
    report.append("📊 OVERVIEW")
    report.append("-" * 70)
    report.append(f"Containers monitored: {stats[0]}")
    report.append(f"Total log entries:    {stats[1]}")
    report.append(f"Total errors:         {stats[2]}")
    report.append(f"Total warnings:       {stats[3]}")
    report.append("")

    # Health assessment
    containers_with_errors = sum(1 for s in summaries if s[2] > 0)
    containers_with_warnings = sum(1 for s in summaries if s[3] > 0)

    if stats[2] == 0 and stats[3] == 0:
        health = "🟢 EXCELLENT - No errors or warnings detected"
    elif stats[2] == 0:
        health = f"🟡 GOOD - No errors, but {containers_with_warnings} container(s) with warnings"
    elif stats[2] < 10:
        health = f"🟡 ATTENTION NEEDED - {containers_with_errors} container(s) with errors"
    else:
        health = f"🔴 ISSUES DETECTED - {stats[2]} errors across {containers_with_errors} container(s)"

    report.append(f"Overall Health: {health}")
    report.append("")

    # Containers needing attention
    problem_containers = [s for s in summaries if s[2] > 0 or s[3] > 0]

    if problem_containers:
        report.append("⚠️  CONTAINERS NEEDING ATTENTION")
        report.append("-" * 70)
        for name, total, errors, warnings, summary in problem_containers:
            status = "🔴" if errors > 0 else "🟡"
            report.append(f"{status} {name}")
            report.append(f"   Logs: {total} | Errors: {errors} | Warnings: {warnings}")

            # Add trend information
            trend_summary = format_trend_summary(name, trend_data)
            if trend_summary and trend_summary != "No trend data available":
                report.append(f"   Trend: {trend_summary}")

            # Check for new errors
            if errors > 0:
                new_error_list = get_new_errors(name, date)
                if new_error_list:
                    report.append(f"   ⚠️  {len(new_error_list)} new error type(s) detected")

            if summary:
                # Wrap the summary text to 66 characters (70 minus the "   Summary: " prefix)
                wrapped = textwrap.fill(summary, width=66, subsequent_indent="            ")
                report.append(f"   Summary: {wrapped}")
            report.append("")

    # Healthy containers
    healthy_containers = [s for s in summaries if s[2] == 0 and s[3] == 0]

    if healthy_containers:
        report.append("✅ HEALTHY CONTAINERS")
        report.append("-" * 70)
        for name, total, errors, warnings, summary in healthy_containers:
            if total == 0:
                report.append(f"✅ {name}: No activity in 24h")
            else:
                report.append(f"✅ {name}: {total} logs")
        report.append("")

    report.append("=" * 70)
    report.append(f"Report generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("=" * 70)

    report_text = "\n".join(report)

    # Also return structured data for Discord
    report_data = {
        'total_containers': stats[0],
        'total_logs': stats[1],
        'total_errors': stats[2],
        'total_warnings': stats[3],
        'containers_with_errors': containers_with_errors,
        'problem_containers': [
            {'name': s[0], 'errors': s[2], 'warnings': s[3]}
            for s in problem_containers
        ],
        'healthy_containers': [
            {'name': s[0]}
            for s in healthy_containers
        ]
    }

    return report_text, report_data


def print_daily_report(date=None):
    """
    Print the daily report to console.

    Args:
        date (str): Date in YYYY-MM-DD format (defaults to today)

    Returns:
        dict: Report data for Discord notifications
    """
    report_text, report_data = generate_daily_report(date)
    print(report_text)
    return report_data


def save_daily_report(filename=None, date=None):
    """
    Save the daily report to a file.

    Args:
        filename (str): Output filename (defaults to report_YYYY-MM-DD.txt)
        date (str): Date in YYYY-MM-DD format (defaults to today)

    Returns:
        tuple: (report_path, report_data)
    """
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")

    if filename is None:
        filename = f"report_{date}.txt"

    # Save to data directory
    report_path = Path(__file__).parent.parent.parent / "data" / filename

    report_text, report_data = generate_daily_report(date)

    with open(report_path, 'w') as f:
        f.write(report_text)

    print(f"Report saved to: {report_path}")
    return report_path, report_data


if __name__ == "__main__":
    # Print today's report
    report_data = print_daily_report()

    # Save it to a file
    print()
    report_path, _ = save_daily_report()

    # Send Discord notification if configured
    print()
    config = load_config()
    if config and should_send_notification(report_data, config):
        print("Sending Discord notification...")
        send_discord_notification(report_data, report_path)
    else:
        print("Discord notification not sent (no issues detected or not configured)")
