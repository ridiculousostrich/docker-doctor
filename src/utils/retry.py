"""
Retry logic with exponential backoff for AI and external service calls.
"""

import functools
import time
import logging
from typing import Callable, Any, Optional
import requests

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def retry_with_backoff(func: Callable, max_retries: int = 3, base_delay: float = 1.0, 
                      should_retry: Optional[Callable[[Exception], bool]] = None) -> Any:
    """
    Execute a function with exponential backoff retry logic.

    Args:
        func: Function to execute
        max_retries: Maximum number of retry attempts
        base_delay: Base delay in seconds (exponentially increased)
        should_retry: Optional function to determine if retry should occur based on exception
                     Default: retry on any Exception

    Returns:
        Result of func if successful

    Raises:
        Exception: If all retries fail
    """
    
    if should_retry is None:
        should_retry = lambda exc: True

    for attempt in range(max_retries + 1):
        try:
            logger.info(f"Attempt {attempt + 1}/{max_retries + 1} for {func.__name__}")
            result = func()
            logger.info(f"Successfully executed {func.__name__} on attempt {attempt + 1}")
            return result
        except Exception as e:
            if attempt == max_retries:
                logger.error(f"All {max_retries + 1} attempts failed for {func.__name__}")
                raise e
            
            if not should_retry(e):
                logger.info(f"Exception not retryable: {e}")
                raise e
            
            delay = base_delay * (2 ** attempt)  # Exponential backoff: 1s, 2s, 4s...
            logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay:.1f} seconds...")
            time.sleep(delay)

    # This should never be reached due to the raise above
    raise Exception("Unexpected state in retry_with_backoff")


def retry_ai_call(ai_function: Callable) -> Callable:
    """
    Specialized retry decorator for AI summarization calls.
    
    Example usage:
        @retry_ai_call
        def summarize_logs(logs):
            ...
    """
    def should_retry_ai_exception(e: Exception) -> bool:
        # Retry on network errors, timeouts, rate limits, and server errors
        error_str = str(e).lower()
        retryable_errors = [
            'connection', 'timeout', 'rate limit', 'server', '500', 
            'network', 'failed to connect', 'unavailable'
        ]
        return any(keyword in error_str for keyword in retryable_errors)

    @functools.wraps(ai_function)
    def wrapper(*args, **kwargs):
        return retry_with_backoff(
            lambda: ai_function(*args, **kwargs),
            max_retries=3,
            base_delay=2.0,
            should_retry=should_retry_ai_exception
        )
    return wrapper


def retry_discord_call(webhook_function: Callable) -> Callable:
    """
    Specialized retry for Discord webhook notifications.
    
    Example usage:
        @retry_discord_call
        def send_discord_notification(report):
            ...
    """
    def should_retry_discord_exception(e: Exception) -> bool:
        # Retry on network issues, 429 (rate limit), 5xx errors
        # Discord API: 429 = rate limit, 403 = invalid webhook, 404 = invalid webhook
        error_str = str(e).lower()
        if isinstance(e, requests.exceptions.RequestException):
            # For HTTP errors, check status code
            if hasattr(e, 'response') and e.response is not None:
                status_code = e.response.status_code
                # Retry on 429 (rate limit), 500, 502, 503, 504
                if status_code in [429, 500, 502, 503, 504]:
                    return True
                # Don't retry on 403 (invalid webhook), 404 (deleted webhook)
                if status_code in [403, 404]:
                    return False
        
        # Also retry common transport errors
        retryable_errors = [
            'connection', 'timeout', 'network', 'failed to connect'
        ]
        return any(keyword in error_str for keyword in retryable_errors)

    @functools.wraps(webhook_function)
    def wrapper(*args, **kwargs):
        return retry_with_backoff(
            lambda: webhook_function(*args, **kwargs),
            max_retries=3,
            base_delay=1.0,
            should_retry=should_retry_discord_exception
        )
    return wrapper


# Usage example:
# @retry_ai_call
# def summarize_logs(logs):
#     return ai_provider.summarize(logs)
# 
# @retry_discord_call
# def send_notification(report):
#     return discord_webhook.send(report)


if __name__ == '__main__':
    # Simple test
    def failing_function():
        raise Exception("Temporary failure")
    
    try:
        result = retry_with_backoff(failing_function, max_retries=2, base_delay=0.5)
    except Exception as e:
        print(f"Function failed after retries: {e}")