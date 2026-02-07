"""
Log parsing and analysis functions.
Detects log levels and patterns in log messages.
"""

import re


def detect_log_level(message):
    """
    Detect the log level from a log message.

    Args:
        message (str): Log message text

    Returns:
        str: Detected log level (ERROR, WARN, INFO, DEBUG)
    """
    # Check for explicit log level markers first (highest priority)
    # These are more reliable than keyword matching
    explicit_patterns = [
        (r'\[ERR\]|\[ERROR\]', 'ERROR'),
        (r'\[WRN\]|\[WARN\]|\[WARNING\]', 'WARN'),
        (r'\[INF\]|\[INFO\]', 'INFO'),
        (r'\[DBG\]|\[DEBUG\]', 'DEBUG'),
    ]

    for pattern, level in explicit_patterns:
        if re.search(pattern, message, re.IGNORECASE):
            return level

    # Fall back to keyword matching if no explicit marker found
    message_upper = message.upper()

    # Check for error patterns
    error_patterns = [
        r'\bERROR\b',
        r'\bFAIL(ED|URE)?\b',
        r'\bEXCEPTION\b',
        r'\bCRITICAL\b',
        r'\bFATAL\b',
        r'\bPANIC\b',
    ]

    for pattern in error_patterns:
        if re.search(pattern, message_upper):
            return "ERROR"

    # Check for warning patterns
    warning_patterns = [
        r'\bWARN(ING)?\b',
        r'\bCAUTION\b',
        r'\bDEPRECAT(ED|ION)\b',
    ]

    for pattern in warning_patterns:
        if re.search(pattern, message_upper):
            return "WARN"

    # Check for debug patterns
    debug_patterns = [
        r'\bDEBUG\b',
        r'\bTRACE\b',
    ]

    for pattern in debug_patterns:
        if re.search(pattern, message_upper):
            return "DEBUG"

    # Default to INFO
    return "INFO"

def extract_timestamp(message):
    """
    Try to extract a timestamp from the log message.

    Args:
        message (str): Log message text

    Returns:
        str or None: Extracted timestamp in ISO format, or None if not found
    """
    from datetime import datetime

    # Common timestamp patterns
    patterns = [
        # Jellyfin style: [06:38:35] or [11:40:43]
        (r'\[(\d{2}:\d{2}:\d{2})\]', '%H:%M:%S'),
        # ISO format: 2026-02-07T18:54:01 or 2026-02-07 18:54:01
        (r'(\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2})', '%Y-%m-%d %H:%M:%S'),
        # Common format: 2026-02-07 18:54:01.123
        (r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', '%Y-%m-%d %H:%M:%S'),
    ]

    for pattern, fmt in patterns:
        match = re.search(pattern, message)
        if match:
            timestamp_str = match.group(1).replace('T', ' ')
            try:
                # For time-only formats, use today's date
                if fmt == '%H:%M:%S':
                    time_obj = datetime.strptime(timestamp_str, fmt)
                    now = datetime.now()
                    # Combine today's date with the extracted time
                    full_timestamp = datetime(
                        now.year, now.month, now.day,
                        time_obj.hour, time_obj.minute, time_obj.second
                    )
                    return full_timestamp.strftime('%Y-%m-%d %H:%M:%S')
                else:
                    dt = datetime.strptime(timestamp_str, fmt)
                    return dt.strftime('%Y-%m-%d %H:%M:%S')
            except ValueError:
                continue

    return None

def parse_log_line(line):
    """
    Parse a log line and extract information.

    Args:
        line (str): Raw log line

    Returns:
        dict: Parsed log information with keys:
            - message: The full log message
            - level: Detected log level
            - clean_message: Message with log level prefix removed
    """
    line = line.strip()

    if not line:
        return None

    # Detect log level
    level = detect_log_level(line)

    # Try to clean up the message by removing common log prefixes
    clean_message=line

    # Remove timestamp patterns
    clean_message = re.sub(r'^\[.*?\]\s*', '', clean_message)  # [timestamp]
    clean_message = re.sub(r'^\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\s*', '', clean_message)  # bare timestamp

    # Remove log level prefix: ERROR:, INFO:, etc.
    clean_message = re.sub(r'^(ERROR|WARN|WARNING|INFO|DEBUG|TRACE)[:\s]+', '', clean_message, flags=re.IGNORECASE)


    # Try to extract timestamp from message
    timestamp = extract_timestamp(line)

    return {
        "message": line,
        "level": level,
        "clean_message": clean_message,
        "timestamp": timestamp
    }


if __name__ == "__main__":
    # Test the parser with sample log lines
    test_logs = [
        "2024-01-01 10:00:00 INFO: Application started successfully",
        "[ERROR] Database connection failed",
        "WARNING: Disk space running low",
        "Request completed in 150ms",
        "FATAL: Out of memory",
        "deprecated function call detected",
        "Debug: Processing item 42",
        "Connection timeout - retrying",
    ]

    print("Testing Log Parser")
    print("=" * 60)
    print()

    for log in test_logs:
        parsed = parse_log_line(log)
        if parsed:
            print(f"Original: {log}")
            print(f"  Level: {parsed['level']}")
            print(f"  Clean:  {parsed['clean_message']}")
            print()
