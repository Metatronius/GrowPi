#!/bin/bash

echo "Stopping GrowPi backend and frontend..."

# Stop backend (Flask)
pkill -f "python app.py" || true

# Stop frontend (Vite dev server)
pkill -f "vite" || true

echo "Restarting backend..."
cd backend
source venv/bin/activate
nohup python app.py > ../backend.log 2>&1 &

echo "Restarting frontend..."
cd ../frontend
nohup npm run dev -- --host > ../frontend.log 2>&1 &

sleep 2

echo "Checking server status..."
if pgrep -f "python app.py" >/dev/null; then
    echo "Backend is running."
else
    echo "Backend failed to start. Check backend.log."
fi
if pgrep -f "vite" >/dev/null; then
    echo "Frontend is running."
else
    echo "Frontend failed to start. Check frontend.log."
fi

echo "GrowPi backend and frontend restarted."
echo "Check backend.log and frontend.log for output."