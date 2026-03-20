"""
Analyze trends and changes in container logs over time.
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.database.queries import get_connection


def get_date_comparison(date=None, days_back=1):
    """
    Compare log statistics between two dates.

    Args:
        date (str): Date to analyze (defaults to today)
        days_back (int): How many days back to compare (default 1 = yesterday)

    Returns:
        dict: Comparison data for each container
    """
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")

    # Calculate comparison date
    date_obj = datetime.strptime(date, "%Y-%m-%d")
    comparison_date = (date_obj - timedelta(days=days_back)).strftime("%Y-%m-%d")

    conn = get_connection()
    cursor = conn.cursor()

    # Get summaries for both dates
    cursor.execute("""
        SELECT
            c.name,
            today.total_logs as today_logs,
            today.error_count as today_errors,
            today.warning_count as today_warnings,
            prev.total_logs as prev_logs,
            prev.error_count as prev_errors,
            prev.warning_count as prev_warnings
        FROM containers c
        LEFT JOIN daily_summaries today ON c.id = today.container_id AND today.date = ?
        LEFT JOIN daily_summaries prev ON c.id = prev.container_id AND prev.date = ?
        ORDER BY c.name
    """, (date, comparison_date))

    results = cursor.fetchall()
    conn.close()

    comparisons = {}

    for row in results:
        name = row[0]
        today_logs = row[1] or 0
        today_errors = row[2] or 0
        today_warnings = row[3] or 0
        prev_logs = row[4] or 0
        prev_errors = row[5] or 0
        prev_warnings = row[6] or 0

        # Calculate changes
        log_change = today_logs - prev_logs
        error_change = today_errors - prev_errors
        warning_change = today_warnings - prev_warnings

        # Calculate percentage changes
        error_pct = calculate_percentage_change(prev_errors, today_errors)
        warning_pct = calculate_percentage_change(prev_warnings, today_warnings)

        comparisons[name] = {
            'today': {
                'logs': today_logs,
                'errors': today_errors,
                'warnings': today_warnings
            },
            'previous': {
                'logs': prev_logs,
                'errors': prev_errors,
                'warnings': prev_warnings
            },
            'changes': {
                'logs': log_change,
                'errors': error_change,
                'warnings': warning_change,
                'error_pct': error_pct,
                'warning_pct': warning_pct
            }
        }

    return comparisons


def calculate_percentage_change(old_value, new_value):
    """
    Calculate percentage change between two values.

    Args:
        old_value (int): Previous value
        new_value (int): Current value

    Returns:
        float or None: Percentage change, or None if old_value is 0
    """
    if old_value == 0:
        if new_value > 0:
            return float('inf')  # Infinite increase
        else:
            return 0.0

    return ((new_value - old_value) / old_value) * 100


def get_new_errors(container_name, date=None, lookback_days=7):
    """
    Find error messages that are new (not seen in previous days).

    Args:
        container_name (str): Name of container
        date (str): Date to analyze (defaults to today)
        lookback_days (int): How many days to look back

    Returns:
        list: New error messages
    """
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")

    date_obj = datetime.strptime(date, "%Y-%m-%d")
    lookback_date = (date_obj - timedelta(days=lookback_days)).strftime("%Y-%m-%d")

    conn = get_connection()
    cursor = conn.cursor()

    # Get today's error messages
    cursor.execute("""
        SELECT DISTINCT l.message
        FROM log_entries l
        JOIN containers c ON l.container_id = c.id
        WHERE c.name = ?
        AND DATE(l.timestamp) = ?
        AND l.log_level = 'ERROR'
    """, (container_name, date))

    today_errors = {row[0] for row in cursor.fetchall()}

    # Get historical error messages
    cursor.execute("""
        SELECT DISTINCT l.message
        FROM log_entries l
        JOIN containers c ON l.container_id = c.id
        WHERE c.name = ?
        AND DATE(l.timestamp) >= ?
        AND DATE(l.timestamp) < ?
        AND l.log_level = 'ERROR'
    """, (container_name, lookback_date, date))

    historical_errors = {row[0] for row in cursor.fetchall()}

    conn.close()

    # Find new errors (in today but not in history)
    new_errors = today_errors - historical_errors

    return list(new_errors)


def format_trend_summary(container_name, comparison_data):
    """
    Generate a human-readable trend summary.

    Args:
        container_name (str): Container name
        comparison_data (dict): Comparison data from get_date_comparison

    Returns:
        str: Formatted summary
    """
    data = comparison_data.get(container_name, {})

    if not data:
        return "No trend data available"

    today = data['today']
    changes = data['changes']

    # If no errors today, simple message
    if today['errors'] == 0 and today['warnings'] == 0:
        return "No issues detected"

    summary_parts = []

    # Error trends
    if today['errors'] > 0:
        if changes['errors'] > 0:
            if changes['error_pct'] == float('inf'):
                summary_parts.append(f"NEW: {today['errors']} errors (none yesterday)")
            else:
                summary_parts.append(f"{today['errors']} errors (↑{changes['error_pct']:.0f}% from {data['previous']['errors']})")
        elif changes['errors'] < 0:
            summary_parts.append(f"{today['errors']} errors (↓{abs(changes['error_pct']):.0f}% from {data['previous']['errors']})")
        else:
            summary_parts.append(f"{today['errors']} errors (stable)")

    # Warning trends
    if today['warnings'] > 0:
        if changes['warnings'] > 0:
            if changes['warning_pct'] == float('inf'):
                summary_parts.append(f"NEW: {today['warnings']} warnings (none yesterday)")
            else:
                summary_parts.append(f"{today['warnings']} warnings (↑{changes['warning_pct']:.0f}% from {data['previous']['warnings']})")
        elif changes['warnings'] < 0:
            summary_parts.append(f"{today['warnings']} warnings (↓{abs(changes['warning_pct']):.0f}% from {data['previous']['warnings']})")
        else:
            summary_parts.append(f"{today['warnings']} warnings (stable)")

    return " | ".join(summary_parts)


if __name__ == "__main__":
    # Test trend analysis
    print("Analyzing trends...")
    print("=" * 60)
    print()

    comparisons = get_date_comparison()

    for container_name, data in comparisons.items():
        if data['today']['errors'] > 0 or data['today']['warnings'] > 0:
            print(f"{container_name}:")
            print(f"  {format_trend_summary(container_name, comparisons)}")

            # Check for new errors
            new_errors = get_new_errors(container_name)
            if new_errors:
                print(f"  ⚠️  {len(new_errors)} new error type(s) detected")
            print()
