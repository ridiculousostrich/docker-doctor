"""
AI-powered log summarization using configurable AI providers.
"""

import sys
from pathlib import Path
import yaml
from typing import Dict, Any
from src.utils.retry import retry_ai_call

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.database.queries import get_connection
from src.ai import get_ai_provider


def load_ai_config() -> Dict[str, Any]:
    """Load AI configuration from config.yaml, with environment variable override."""
    config_path = Path(__file__).parent.parent.parent / "config.yaml"
    if config_path.exists():
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
    else:
        config = {}
    
    # Override config with environment variables if set
    import os
    
    # AI provider (e.g., ollama, openai, anthropic)
    if os.getenv('AI_PROVIDER'):
        config['ai'] = config.get('ai', {})
        config['ai']['provider'] = os.getenv('AI_PROVIDER')
    
    # AI host endpoint
    if os.getenv('AI_HOST'):
        config['ai'] = config.get('ai', {})
        config['ai']['host'] = os.getenv('AI_HOST')
    
    # AI model name
    if os.getenv('AI_MODEL'):
        config['ai'] = config.get('ai', {})
        config['ai']['model'] = os.getenv('AI_MODEL')
    
    # AI temperature
    if os.getenv('AI_TEMPERATURE'):
        config['ai'] = config.get('ai', {})
        try:
            config['ai']['temperature'] = float(os.getenv('AI_TEMPERATURE'))
        except ValueError:
            pass  # Keep default if invalid
    
    return config.get('ai', {})


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


@retry_ai_call
def generate_ai_summary(container_name, logs_data, total_logs, error_count, warning_count):
    """
    Generate an AI summary using the configured AI provider.

    Args:
        container_name (str): Name of the container
        logs_data (dict): Dictionary with 'errors' and 'warnings' lists
        total_logs (int): Total number of logs
        error_count (int): Number of errors
        warning_count (int): Number of warnings

    Returns:
        str: AI-generated summary
    """
    # Build the prompt for AI provider
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
Analyze these logs and provide a brief summary in plain text (no markdown formatting).

Your summary should:
1. Identify the main pattern or issue in 1-2 sentences
2. Assess severity: CRITICAL (service down/data loss), CONCERNING (degraded performance/unusual), or MINOR (normal noise)
3. State if action is needed in 1 sentence

Context for common patterns:
- "context canceled" / "connection aborted" = Usually client disconnects (minor unless extreme volume)
- Repeated identical errors = Often noise, not escalating issues
- "getaddrinfo ENOTFOUND" = DNS/network client issues, not server problems
- "duplicate key" database errors = Data integrity issue, concerning if frequent
- Authentication failures = Could be bots/invalid attempts (minor) or config issues (concerning)

Key question: Is the SERVICE actually impaired, or just handling normal internet noise?

Format: Write 2-3 sentences of plain text. No bullet points, no markdown headers, no special formatting."""

    try:
        # Use the configured AI provider
        ai_config = load_ai_config()
        ai_provider = get_ai_provider(ai_config)
        
        summary = ai_provider.generate_summary(prompt)
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
