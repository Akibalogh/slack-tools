#!/bin/bash
# Startup script for Customer Group Admin Panel

set -e

echo "🚀 Starting Customer Group Admin Panel..."

# Navigate to project root
cd "$(dirname "$0")/.."

# Activate virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "❌ Virtual environment not found. Please run: python3 -m venv venv"
    exit 1
fi

# Check if database exists, if not initialize it
if [ ! -f "data/admin_panel.db" ]; then
    echo "📦 Initializing database..."
    python3 webapp/database.py
fi

# Start the scheduler in the background
echo "⏰ Starting scheduler..."
python3 webapp/scheduler.py &
SCHEDULER_PID=$!
echo "Scheduler PID: $SCHEDULER_PID"

# Start the Flask app
echo "🌐 Starting web server on port 5001..."
echo "📱 Open http://localhost:5001 in your browser"
echo ""
echo "Press Ctrl+C to stop"

# Trap Ctrl+C to kill both processes
trap "echo ''; echo '🛑 Stopping...'; kill $SCHEDULER_PID 2>/dev/null; exit 0" INT TERM

PORT=5001 FLASK_ENV=development python3 webapp/app.py


