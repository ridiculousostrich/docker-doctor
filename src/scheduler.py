"""
Scheduler for automated daily monitoring.
Runs the full monitoring workflow once per day at configured time.
"""

import time
import yaml
from pathlib import Path
from datetime import datetime, timedelta
import subprocess
import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("/workspace/docker-doctor/logs/scheduler.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

from src.utils.graceful_shutdown import register_shutdown_handler, get_default_cleanup_functions


def load_config():
    """Load configuration from config.yaml"""
    config_path = Path(__file__).parent.parent / "config.yaml"
    if config_path.exists():
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    return {}


def run_workflow():
    """Execute the full monitoring workflow."""
    logger.info("Starting monitoring workflow at %s", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    print("=" * 70)
    print(f"Starting monitoring workflow at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    print()

    steps = [
        ("Collecting logs", ["python", "src/collectors/log_collector.py"]),
        ("Generating summaries", ["python", "src/analyzers/summarizer.py"]),
        ("Running AI analysis", ["python", "src/analyzers/ai_summarizer.py"]),
        ("Generating report", ["python", "src/reporters/daily_report.py"]),
    ]

    for step_name, command in steps:
        logger.info("Starting step: %s", step_name)
        print(f"→ {step_name}...")
        print()
        try:
            # Don't capture output - let it stream to console
            result = subprocess.run(command, check=True, timeout=300)  # 5-minute timeout
            logger.info("Completed step: %s", step_name)
            print()
            print(f"✓ {step_name} completed")
        except subprocess.CalledProcessError as e:
            logger.error("Step %s failed with exit code %d", step_name, e.returncode)
            print()
            print(f"✗ {step_name} failed with exit code {e.returncode}")
            return False
        except subprocess.TimeoutExpired:
            logger.error("Step %s timed out after 5 minutes", step_name)
            print()
            print(f"✗ {step_name} timed out after 5 minutes")
            return False
        print()

    logger.info("Workflow completed successfully at %s", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    print("=" * 70)
    print(f"Workflow completed successfully at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    print()

    return True


def calculate_next_run(schedule_time):
    """
    Calculate the next run time based on schedule.

    Args:
        schedule_time (str): Time in HH:MM format (24-hour)

    Returns:
        datetime: Next scheduled run time
    """
    now = datetime.now()

    # Parse the schedule time
    hour, minute = map(int, schedule_time.split(':'))

    # Create datetime for today at scheduled time
    next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)

    # If that time has already passed today, schedule for tomorrow
    if next_run <= now:
        next_run += timedelta(days=1)

    return next_run


def main():
    """Main scheduler loop."""
    logger.info("Docker Doctor scheduler started")
    print("Docker Doctor - Automated Monitoring Scheduler")
    print("=" * 70)
    print()

    # Load config
    config = load_config()
    schedule_time = config.get('monitoring', {}).get('schedule_time', '06:00')

    print(f"Scheduled to run daily at: {schedule_time}")
    print()

    # Run immediately on startup
    print("Running initial workflow on startup...")
    print()
    run_workflow()

    # Register shutdown handlers
    register_shutdown_handler(get_default_cleanup_functions())

    # Main scheduling loop
    while True:
        # Calculate next run time
        next_run = calculate_next_run(schedule_time)
        sleep_seconds = (next_run - datetime.now()).total_seconds()

        logger.info("Next run scheduled for: %s", next_run.strftime('%Y-%m-%d %H:%M:%S'))
        print(f"Next run scheduled for: {next_run.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Sleeping for {sleep_seconds / 3600:.1f} hours...")
        print()

        # Sleep until next run
        time.sleep(sleep_seconds)

        # Run the workflow
        run_workflow()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Scheduler stopped by user")
        print("\nScheduler stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.exception("Scheduler crashed")
        print(f"\nScheduler crashed: {e}")
        sys.exit(1)
