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

echo "GrowPi backend and frontend restarted."
echo "Check backend.log and frontend.log for output."