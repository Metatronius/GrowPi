#!/bin/bash
# filepath: /home/plederer/Documents/GrowPi/install.sh

set -e

echo "=== GrowPi Automated Installer ==="

# Backend setup
echo "Setting up Python backend..."
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

read -p "Are you running on a Raspberry Pi with sensors attached? (y/n): " is_pi
if [[ "$is_pi" != "y" && "$is_pi" != "Y" ]]; then
    export GROWPI_DEV=1
    echo "Development mode enabled (mock sensors)."
else
    pip install adafruit-circuitpython-htu21d w1thermsensor gpiozero python-kasa
fi

echo "Starting backend server in the background..."
nohup python app.py > ../backend.log 2>&1 &

# Frontend setup
echo "Setting up frontend..."
cd ../frontend
npm install

echo "Starting frontend dev server (accessible on your network)..."
nohup npm run dev -- --host > ../frontend.log 2>&1 &

echo "=== Installation complete! ==="
echo "Backend running on http://localhost:5000"
echo "Frontend running on http://localhost:5173 (or http://<your-pi-ip>:5173 from other devices)"
echo "Check backend.log and frontend.log for server output."