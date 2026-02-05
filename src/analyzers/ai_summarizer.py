"""
AI-powered log summarization using Ollama.
"""

import sys
from pathlib import Path
import ollama

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.database.queries import get_connection


def get_container_logs_for_analysis(container_id, date, max_logs=50):
    """
    Get relevant logs for AI analysis.

    Args:
        container_id (int): Container ID
        date (str): Date in YYYY-MM-DD format
        max_logs (int): Maximum number of logs to analyze

    Returns:
        dict: Logs grouped by level
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Get errors
    cursor.execute("""
        SELECT message
        FROM log_entries
        WHERE container_id = ?
        AND DATE(timestamp) = ?
        AND log_level = 'ERROR'
        ORDER BY timestamp DESC
        LIMIT ?
    """, (container_id, date, max_logs))
    errors = [row[0] for row in cursor.fetchall()]

    # Get warnings
    cursor.execute("""
        SELECT message
        FROM log_entries
        WHERE container_id = ?
        AND DATE(timestamp) = ?
        AND log_level = 'WARN'
        ORDER BY timestamp DESC
        LIMIT ?
    """, (container_id, date, max_logs))
    warnings = [row[0] for row in cursor.fetchall()]

    conn.close()

    return {
        "errors": errors,
        "warnings": warnings
    }


def generate_ai_summary(container_name, logs_data, total_logs, error_count, warning_count):
    """
    Generate an AI summary using Ollama.

    Args:
        container_name (str): Name of the container
        logs_data (dict): Dictionary with 'errors' and 'warnings' lists
        total_logs (int): Total number of logs
        error_count (int): Number of errors
        warning_count (int): Number of warnings

    Returns:
        str: AI-generated summary
    """
    # Build the prompt for Ollama
    prompt = f"""Analyze these Docker container logs and provide a brief summary.

Container: {container_name}
Total logs: {total_logs}
Errors: {error_count}
Warnings: {warning_count}

"""

    if logs_data["errors"]:
        prompt += f"\nError messages (showing up to 10):\n"
        for i, error in enumerate(logs_data["errors"][:10], 1):
            prompt += f"{i}. {error}\n"

    if logs_data["warnings"]:
        prompt += f"\nWarning messages (showing up to 10):\n"
        for i, warning in enumerate(logs_data["warnings"][:10], 1):
            prompt += f"{i}. {warning}\n"

    prompt += """
Provide a concise 2-3 sentence summary that:
1. Identifies the main issues or patterns
2. Assesses severity (critical, concerning, or minor)
3. Suggests if action is needed

Keep it brief and actionable."""

    try:
        # Call Ollama API
        client = ollama.Client(host='http://192.168.1.9:11434')
        response = client.chat(
            model='llama3.1:8B',
            messages=[{
                'role': 'user',
                'content': prompt
            }]
        )

        summary = response['message']['content'].strip()
        return summary

    except Exception as e:
        return f"AI summary unavailable: {str(e)}"


def enhance_summary_with_ai(container_id, date=None):
    """
    Enhance an existing summary with AI analysis.

    Args:
        container_id (int): Container ID
        date (str): Date in YYYY-MM-DD format (defaults to today)

    Returns:
        str: Enhanced AI summary
    """
    from datetime import datetime

    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")

    conn = get_connection()
    cursor = conn.cursor()

    # Get container info and summary stats
    cursor.execute("""
        SELECT c.name, s.total_logs, s.error_count, s.warning_count
        FROM containers c
        JOIN daily_summaries s ON c.id = s.container_id
        WHERE s.container_id = ? AND s.date = ?
    """, (container_id, date))

    result = cursor.fetchone()
    if not result:
        conn.close()
        return None

    container_name, total_logs, error_count, warning_count = result

    # If no errors or warnings, simple summary
    if error_count == 0 and warning_count == 0:
        ai_summary = f"✅ {container_name} is operating normally with no errors or warnings detected."
    else:
        # Get logs for AI analysis
        logs_data = get_container_logs_for_analysis(container_id, date)

        print(f"  Generating AI summary for {container_name}...")
        ai_summary = generate_ai_summary(
            container_name,
            logs_data,
            total_logs,
            error_count,
            warning_count
        )

    # Update the summary in the database
    cursor.execute("""
        UPDATE daily_summaries
        SET ai_summary = ?
        WHERE container_id = ? AND date = ?
    """, (ai_summary, container_id, date))

    conn.commit()
    conn.close()

    return ai_summary


def enhance_all_summaries_with_ai(date=None):
    """
    Enhance all summaries with AI analysis.

    Args:
        date (str): Date in YYYY-MM-DD format (defaults to today)
    """
    from datetime import datetime

    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")

    print(f"Enhancing summaries with AI for {date}")
    print("=" * 60)
    print()

    conn = get_connection()
    cursor = conn.cursor()

    # Get all containers with summaries for this date
    cursor.execute("""
        SELECT s.container_id, c.name
        FROM daily_summaries s
        JOIN containers c ON s.container_id = c.id
        WHERE s.date = ?
        ORDER BY c.name
    """, (date,))

    containers = cursor.fetchall()
    conn.close()

    for container_id, container_name in containers:
        print(f"Processing: {container_name}")
        summary = enhance_summary_with_ai(container_id, date)
        if summary:
            print(f"  ✓ Enhanced")
        print()

    print("=" * 60)
    print(f"Enhanced {len(containers)} summaries with AI")


if __name__ == "__main__":
    # Test: Enhance all summaries with AI
    enhance_all_summaries_with_ai()
