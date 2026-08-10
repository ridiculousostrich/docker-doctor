#!/usr/bin/env python3
"""
Data freshness verification script for Docker Doctor v1.2 release.
This script checks that the dashboard is actually showing current data
and not stale historical data.
"""

import sys
import os
from datetime import datetime, timedelta
import sqlite3
from pathlib import Path


def check_data_freshness():
    """
    Verify that the data in the database is fresh (within last 20 minutes).
    This is a key requirement for v1.2 release.
    """
    try:
        # Get the database path
        project_root = Path(__file__).parent.resolve()
        db_path = project_root / "data" / "logs.db"
        
        if not db_path.exists():
            print(f"ERROR: Database file not found at {db_path}")
            return False
            
        # Connect to database and check for recent entries
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Get the newest log entry timestamp
        cursor.execute("SELECT MAX(timestamp) as newest_log FROM log_entries")
        result = cursor.fetchone()
        newest_log_timestamp = result[0] if result and result[0] else None
        
        if not newest_log_timestamp:
            print("ERROR: No log entries found in database")
            conn.close()
            return False
            
        # Calculate how old the newest data is
        newest_log_dt = datetime.fromisoformat(newest_log_timestamp)
        current_time = datetime.now()
        data_age = current_time - newest_log_dt
        
        print(f"Latest log entry: {newest_log_timestamp}")
        print(f"Data age: {data_age}")
        
        # Check if data is within expected freshness window (last 20 minutes)
        freshness_threshold = timedelta(minutes=20)
        if data_age > freshness_threshold:
            print(f"ERROR: Data is too old ({data_age.total_seconds()} seconds)")
            conn.close()
            return False
        else:
            print(f"SUCCESS: Data is fresh (less than {freshness_threshold.total_seconds()} seconds old)")
            conn.close()
            return True
            
    except Exception as e:
        print(f"ERROR: Failed to check data freshness - {e}")
        return False


def check_for_stale_data_indicators():
    """
    Check for any known indicators of stale data in the system.
    """
    try:
        project_root = Path(__file__).parent.resolve()
        db_path = project_root / "data" / "logs.db"
        
        if not db_path.exists():
            print("WARNING: Database file does not exist (unexpected for v1.2)")
            return False
            
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Check database content - this would help validate that logs are actually being collected
        cursor.execute("SELECT COUNT(*) as total_logs FROM log_entries")
        log_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT DISTINCT date FROM daily_summaries ORDER BY date DESC LIMIT 1")
        latest_date_result = cursor.fetchone()
        latest_date = latest_date_result[0] if latest_date_result else None
        
        conn.close()
        
        if log_count == 0:
            print("WARNING: Database is empty (no logs collected)")
            return False
        else:
            print(f"SUCCESS: Database has {log_count} log entries")
            
        if latest_date:
            print(f"Latest summary date: {latest_date}")
            # The dashboard should ideally show current (today) data, not old dates
            if latest_date != datetime.now().strftime("%Y-%m-%d"):
                print(f"WARNING: Latest summary date {latest_date} is not today ({datetime.now().strftime('%Y-%m-%d')})")
                return False
            else:
                print("SUCCESS: Latest summary is for today")
                return True
        else:
            print("WARNING: No daily summaries found")
            return False
            
    except Exception as e:
        print(f"ERROR: Failed to check stale data indicators - {e}")
        return False


def main():
    print("=== Docker Doctor Data Freshness Verification ===")
    print("This script ensures the system is actually showing current data")
    print("and not historical data as was reported in v1.1")
    print()
    
    # 1. Check if database exists
    project_root = Path(__file__).parent.resolve()
    db_path = project_root / "data" / "logs.db"
    
    print(f"Checking database at: {db_path}")
    
    if not db_path.exists():
        print("WARNING: This indicates the v1.1 issue of baking in old data - if the image had data/logs.db it's the old location")
        print("This is corrected in v1.2 with CLEAN DOCKERFILE")
        print()
    
    # 2. Check actual data freshness
    freshness_ok = check_data_freshness()
    
    print()
    
    # 3. Check for stale data indicators (if database exists)
    if db_path.exists():
        data_indicators_ok = check_for_stale_data_indicators()
    else:
        data_indicators_ok = False
    
    print()
    
    if freshness_ok and data_indicators_ok:
        print("✅ ALL CHECKS PASSED - System ready for v1.2.0 release")
        return 0
    else:
        print("❌ CHECKS FAILED - System needs attention before release")
        return 1


if __name__ == "__main__":
    sys.exit(main())