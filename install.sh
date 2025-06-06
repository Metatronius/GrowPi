#!/bin/bash

set -e

echo "=== GrowPi Automated Installer ==="

# Backend setup
echo "Setting up Python backend..."
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Setup data.json from template if needed
if [ ! -f data.json ]; then
    if [ -f data.json.example ]; then
        cp data.json.example data.json
        echo "Copied data.json.example to data.json"
    else
        echo "ERROR: data.json.example not found! Please provide a template."
        exit 1
    fi
fi

# Prompt for Kasa config
read -p "Enter your Kasa username (email) [leave blank to skip]: " kasa_user
read -s -p "Enter your Kasa password [leave blank to skip]: " kasa_pass
echo
read -p "Enter IP address of Fan plug [leave blank to skip]: " fan_ip
read -p "Enter IP address of Humidifier plug [leave blank to skip]: " humid_ip
read -p "Enter IP address of Light plug [leave blank to skip]: " light_ip

# Use jq to update data.json if available, else fallback to sed
if command -v jq >/dev/null 2>&1; then
    tmpfile=$(mktemp)
    jq \
    --arg user "$kasa_user" \
    --arg pass "$kasa_pass" \
    --arg fan "$fan_ip" \
    --arg humid "$humid_ip" \
    --arg light "$light_ip" \
    '
    if ($user != "") then .["Kasa configs"].Username = $user else . end |
    if ($pass != "") then .["Kasa configs"].Password = $pass else . end |
    if ($fan != "") then .["Kasa configs"].Device_IPs.Fan = $fan else . end |
    if ($humid != "") then .["Kasa configs"].Device_IPs.Humidifier = $humid else . end |
    if ($light != "") then .["Kasa configs"].Device_IPs.Light = $light else . end
    ' data.json > "$tmpfile" && mv "$tmpfile" data.json
else
    # Fallback: naive sed replacement (will not add new fields if missing)
    if [ -n "$kasa_user" ]; then
        sed -i "s/\"Username\": \".*\"/\"Username\": \"$kasa_user\"/" data.json
    fi
    if [ -n "$kasa_pass" ]; then
        sed -i "s/\"Password\": \".*\"/\"Password\": \"$kasa_pass\"/" data.json
    fi
    if [ -n "$fan_ip" ]; then
        sed -i "s/\"Fan\": \".*\"/\"Fan\": \"$fan_ip\"/" data.json
    fi
    if [ -n "$humid_ip" ]; then
        sed -i "s/\"Humidifier\": \".*\"/\"Humidifier\": \"$humid_ip\"/" data.json
    fi
    if [ -n "$light_ip" ]; then
        sed -i "s/\"Light\": \".*\"/\"Light\": \"$light_ip\"/" data.json
    fi
fi

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