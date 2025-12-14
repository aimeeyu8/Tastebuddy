#!/bin/bash
echo "====================================="
echo "   Launching TasteBuddy (Backend + Frontend)"
echo "====================================="

# Start backend
echo "Starting backend..."
cd backend
source venv/bin/activate
uvicorn main:app --reload --host 127.0.0.1 --port 8000 &
BACKEND_PID=$!

# Wait for backend to boot
sleep 2

# Start frontend
echo "Starting frontend on http://localhost:5500 ..."
cd ../frontend
python3 -m http.server 5500 &
FRONTEND_PID=$!

# Open browser
sleep 1
open "http://localhost:5500" 2>/dev/null || xdg-open "http://localhost:5500"

echo "TasteBuddy is live!"
wait
