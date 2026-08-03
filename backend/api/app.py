"""
Flask API server for Docker Doctor Dashboard.

Serves REST API endpoints on port 8586 AND serves the React frontend on port 8585.
Reads from the SQLite database at data/logs.db.
"""

import sys
import os
from pathlib import Path
from datetime import datetime, timedelta

# Add the project root to sys.path so we can import from src/
PROJECT_ROOT = Path(__file__).parent.parent.parent.resolve()
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from flask import Flask, jsonify, request, send_from_directory

app = Flask(__name__, static_folder=str(PROJECT_ROOT / "frontend" / "build"), static_url_path="")

# Database path - use logs.db which has real data
DB_PATH = PROJECT_ROOT / "data" / "logs.db"


def get_db():
    """Get a database connection."""
    import sqlite3
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@app.route("/api/stats")
def get_stats():
    """Get overall dashboard stats from the most recent daily summary."""
    conn = get_db()
    cursor = conn.cursor()

    # Get the most recent date with data
    cursor.execute("SELECT DISTINCT date FROM daily_summaries ORDER BY date DESC LIMIT 1")
    row = cursor.fetchone()

    if not row:
        conn.close()
        return jsonify({"error": "No data available", "date": datetime.now().strftime("%Y-%m-%d")})

    latest_date = row["date"]

    # Get container count
    cursor.execute("SELECT COUNT(*) as count FROM containers")
    container_count = cursor.fetchone()["count"]

    # Get totals from the latest summary
    cursor.execute("""
        SELECT
            COALESCE(SUM(total_logs), 0) as total_logs,
            COALESCE(SUM(error_count), 0) as total_errors,
            COALESCE(SUM(warning_count), 0) as total_warnings
        FROM daily_summaries
        WHERE date = ?
    """, (latest_date,))
    totals = cursor.fetchone()

    # Get container breakdown
    cursor.execute("""
        SELECT
            c.name,
            c.image,
            COALESCE(ds.error_count, 0) as error_count,
            COALESCE(ds.warning_count, 0) as warning_count,
            COALESCE(ds.ai_summary, '') as ai_summary
        FROM containers c
        LEFT JOIN daily_summaries ds ON c.id = ds.container_id AND ds.date = ?
        ORDER BY ds.error_count DESC NULLS LAST, ds.warning_count DESC NULLS LAST
    """, (latest_date,))
    containers = cursor.fetchall()

    conn.close()

    problem_containers = []
    healthy_containers = []

    for c in containers:
        container = {
            "name": c["name"],
            "image": c["image"],
            "error_count": c["error_count"],
            "warning_count": c["warning_count"],
        }
        if c["ai_summary"]:
            container["ai_summary"] = c["ai_summary"]

        if c["error_count"] > 0 or c["warning_count"] > 0:
            problem_containers.append(container)
        else:
            # Get total logs for healthy containers from the latest day
            healthy_containers.append(container)

    return jsonify({
        "date": latest_date,
        "container_count": container_count,
        "total_logs": totals["total_logs"],
        "total_errors": totals["total_errors"],
        "total_warnings": totals["total_warnings"],
        "problem_containers": problem_containers,
        "healthy_containers": healthy_containers,
    })


@app.route("/api/trends")
def get_trends():
    """Get trend data comparing the two most recent dates."""
    conn = get_db()
    cursor = conn.cursor()

    # Get the two most recent dates
    cursor.execute("SELECT DISTINCT date FROM daily_summaries ORDER BY date DESC LIMIT 2")
    rows = cursor.fetchall()

    if len(rows) < 2:
        conn.close()
        # Return mock trend data if not enough dates
        return jsonify([
            {
                "name": "cloudflared-tunnel",
                "today": {"logs": 6, "errors": 6, "warnings": 0},
                "previous": {"logs": 0, "errors": 0, "warnings": 0},
            },
            {
                "name": "ollama",
                "today": {"logs": 286, "errors": 11, "warnings": 0},
                "previous": {"logs": 0, "errors": 0, "warnings": 0},
            },
        ])

    date1 = rows[0]["date"]  # most recent
    date2 = rows[1]["date"]  # second most recent

    cursor.execute("""
        SELECT
            c.name,
            COALESCE(SUM(CASE WHEN ds.date = ? THEN ds.total_logs ELSE 0 END), 0) as today_logs,
            COALESCE(SUM(CASE WHEN ds.date = ? THEN ds.error_count ELSE 0 END), 0) as today_errors,
            COALESCE(SUM(CASE WHEN ds.date = ? THEN ds.warning_count ELSE 0 END), 0) as today_warnings,
            COALESCE(SUM(CASE WHEN ds.date = ? THEN ds.total_logs ELSE 0 END), 0) as prev_logs,
            COALESCE(SUM(CASE WHEN ds.date = ? THEN ds.error_count ELSE 0 END), 0) as prev_errors,
            COALESCE(SUM(CASE WHEN ds.date = ? THEN ds.warning_count ELSE 0 END), 0) as prev_warnings
        FROM containers c
        LEFT JOIN daily_summaries ds ON c.id = ds.container_id
        GROUP BY c.id, c.name
        HAVING today_errors > 0 OR today_warnings > 0 OR prev_errors > 0 OR prev_warnings > 0
        ORDER BY today_errors DESC, today_warnings DESC
    """, (date1, date1, date1, date2, date2, date2))

    trends = []
    for row in cursor.fetchall():
        trends.append({
            "name": row["name"],
            "today": {
                "logs": row["today_logs"],
                "errors": row["today_errors"],
                "warnings": row["today_warnings"],
            },
            "previous": {
                "logs": row["prev_logs"],
                "errors": row["prev_errors"],
                "warnings": row["prev_warnings"],
            },
        })

    conn.close()
    return jsonify(trends)


@app.route("/api/new-errors")
def get_new_errors():
    """Get recent new error messages across all containers."""
    conn = get_db()
    cursor = conn.cursor()

    # Get the most recent date
    cursor.execute("SELECT DISTINCT date FROM daily_summaries ORDER BY date DESC LIMIT 1")
    row = cursor.fetchone()

    if not row:
        conn.close()
        return jsonify([])

    latest_date = row["date"]

    # Get recent errors from the latest day
    cursor.execute("""
        SELECT
            c.name as container_name,
            l.message as error_message,
            l.timestamp
        FROM log_entries l
        JOIN containers c ON l.container_id = c.id
        WHERE DATE(l.timestamp) = ?
          AND l.log_level = 'ERROR'
        ORDER BY l.timestamp DESC
        LIMIT 20
    """, (latest_date,))

    errors = []
    for row in cursor.fetchall():
        errors.append({
            "container_name": row["container_name"],
            "error_message": row["error_message"][:200],  # Truncate long messages
        })

    conn.close()
    return jsonify(errors)


@app.route("/api/containers")
def get_containers():
    """Get list of all containers with their latest summary data."""
    conn = get_db()
    cursor = conn.cursor()

    # Get the most recent date
    cursor.execute("SELECT DISTINCT date FROM daily_summaries ORDER BY date DESC LIMIT 1")
    row = cursor.fetchone()

    if not row:
        conn.close()
        return jsonify([])

    latest_date = row["date"]

    cursor.execute("""
        SELECT
            c.name,
            c.image,
            c.first_seen,
            c.last_seen,
            COALESCE(ds.total_logs, 0) as total_logs,
            COALESCE(ds.error_count, 0) as error_count,
            COALESCE(ds.warning_count, 0) as warning_count,
            COALESCE(ds.ai_summary, '') as ai_summary
        FROM containers c
        LEFT JOIN daily_summaries ds ON c.id = ds.container_id AND ds.date = ?
        ORDER BY ds.error_count DESC NULLS LAST, ds.warning_count DESC NULLS LAST
    """, (latest_date,))

    containers = []
    for row in cursor.fetchall():
        container = {
            "name": row["name"],
            "image": row["image"],
            "first_seen": row["first_seen"],
            "last_seen": row["last_seen"],
            "total_logs": row["total_logs"],
            "error_count": row["error_count"],
            "warning_count": row["warning_count"],
        }
        if row["ai_summary"]:
            container["ai_summary"] = row["ai_summary"]
        containers.append(container)

    conn.close()
    return jsonify(containers)


@app.route("/api/containers/<name>/logs")
def get_container_logs(name):
    """Get recent log entries for a specific container."""
    conn = get_db()
    cursor = conn.cursor()

    limit = int(request.args.get("limit", 50))
    level = request.args.get("level", None)

    if level:
        cursor.execute("""
            SELECT timestamp, log_level, message
            FROM log_entries l
            JOIN containers c ON l.container_id = c.id
            WHERE c.name = ? AND l.log_level = ?
            ORDER BY timestamp DESC
            LIMIT ?
        """, (name, level, limit))
    else:
        cursor.execute("""
            SELECT timestamp, log_level, message
            FROM log_entries l
            JOIN containers c ON l.container_id = c.id
            WHERE c.name = ?
            ORDER BY timestamp DESC
            LIMIT ?
        """, (name, limit))

    logs = []
    for row in cursor.fetchall():
        logs.append({
            "timestamp": row["timestamp"],
            "log_level": row["log_level"],
            "message": row["message"],
        })

    conn.close()
    return jsonify(logs)


@app.route("/api/health")
def health():
    """Health check endpoint."""
    db_exists = DB_PATH.exists()
    return jsonify({
        "status": "healthy",
        "database": "connected" if db_exists else "disconnected",
        "timestamp": datetime.now().isoformat(),
    })


# Serve the React frontend for all non-API routes
@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_frontend(path):
    """Serve the React SPA. All routes fall back to index.html."""
    if path != "" and os.path.isfile(str(PROJECT_ROOT / "frontend" / "build" / path)):
        return send_from_directory(str(PROJECT_ROOT / "frontend" / "build"), path)
    return send_from_directory(str(PROJECT_ROOT / "frontend" / "build"), "index.html")


if __name__ == "__main__":
    port = int(os.environ.get("API_PORT", 8586))
    print(f"Starting Docker Doctor API server on port {port}...")
    print(f"Database: {DB_PATH}")
    print(f"Frontend: frontend/build/")
    app.run(host="0.0.0.0", port=port, debug=False)
