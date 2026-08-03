"""
Graceful shutdown handler for Docker Doctor components.

This module provides signal handling and cleanup routines for
all long-running components to ensure proper resource release
and state persistence on shutdown.
"""

import signal
import sys
import logging
import time
from typing import List, Callable

# Configure logging
logger = logging.getLogger(__name__)

# Global shutdown flag
downloading = False

def register_shutdown_handler(cleanup_functions: List[Callable]):
    """
    Register signal handlers for graceful shutdown.
    
    Args:
        cleanup_functions: List of functions to call on shutdown
    """
    def shutdown_handler(signum, frame):
        global downloading
        if downloading:
            logger.info("Shutdown already in progress, ignoring signal")
            return
        
        downloading = True
        logger.info("Received shutdown signal (SIGTERM/SIGINT) - initiating graceful shutdown...")
        
        # Call all registered cleanup functions
        for func in cleanup_functions:
            try:
                logger.info("Running cleanup function: %s", func.__name__)
                func()
            except Exception as e:
                logger.error("Cleanup function %s failed: %s", func.__name__, str(e))
        
        logger.info("Graceful shutdown completed")
        sys.exit(0)
    
    # Register for both SIGTERM and SIGINT
    signal.signal(signal.SIGTERM, shutdown_handler)
    signal.signal(signal.SIGINT, shutdown_handler)
    
    logger.info("Graceful shutdown handler registered for SIGTERM and SIGINT")


def cleanup_database_connections():
    """Cleanup function for closing database connections."""
    # This will be implemented in the database module
    from src.database.queries import close_all_connections
    close_all_connections()


def cleanup_ai_resources():
    """Cleanup function for AI model resources."""
    # This will be implemented in the AI module
    logger.info("Cleaning up AI model resources")
    # Add any model-specific cleanup here


def cleanup_discord_resources():
    """Cleanup function for Discord webhook resources."""
    # No explicit cleanup needed for discord_webhook, but we can log
    logger.info("Cleaning up Discord notification resources")


def get_default_cleanup_functions() -> List[Callable]:
    """Get list of default cleanup functions for all components."""
    return [
        cleanup_database_connections,
        cleanup_ai_resources,
        cleanup_discord_resources
    ]


if __name__ == "__main__":
    # Test the shutdown handler
    logging.basicConfig(level=logging.INFO)
    
    # Register the shutdown handler
    register_shutdown_handler(get_default_cleanup_functions())
    
    print("Shutdown handler registered. Simulating long-running process...")
    print("Send SIGTERM or SIGINT (Ctrl+C) to test shutdown.")
    
    # Simulate long-running work
    while True:
        time.sleep(1)
