#!/bin/bash

set -e

echo "=== GrowPi Automated Installer ==="

# Check for Python 3.9+
if ! python3 --version | grep -q "3.9"; then
    echo "WARNING: Python 3.9+ is recommended. Detected: $(python3 --version)"
fi

# Check for Node.js and npm
if ! command -v node >/dev/null 2>&1; then
    echo "ERROR: Node.js is not installed. Please install Node.js v18+ and rerun this script."
    exit 1
fi
if ! command -v npm >/dev/null 2>&1; then
    echo "ERROR: npm is not installed. Please install npm and rerun this script."
    exit 1
fi

# Backend setup
echo "Setting up Python backend..."
cd backend
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
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

# Ask if user wants to configure Kasa switches
read -p "Would you like to configure Kasa smart switches? (y/n): " use_kasa
if [[ "$use_kasa" == "y" || "$use_kasa" == "Y" ]]; then
    read -p "Enter your Kasa username (email) [leave blank to skip]: " kasa_user
    read -s -p "Enter your Kasa password [leave blank to skip]: " kasa_pass
    echo

    declare -A switches
    declare -a switch_names=("Fan" "Humidifier" "Light" "Dehumidifier" "Heater")
    for sw in "${switch_names[@]}"; do
        read -p "Would you like to use a Kasa switch for $sw? (y/n): " use_sw
        if [[ "$use_sw" == "y" || "$use_sw" == "Y" ]]; then
            read -p "Enter IP address of $sw plug: " ip
            switches[$sw]=$ip
        fi
    done

    # Use jq to update data.json if available, else fallback to sed
    if command -v jq >/dev/null 2>&1; then
        tmpfile=$(mktemp)
        jq_args=()
        [[ -n "$kasa_user" ]] && jq_args+=(--arg user "$kasa_user")
        [[ -n "$kasa_pass" ]] && jq_args+=(--arg pass "$kasa_pass")
        jq_script='
            . as $orig |
            (if ($user != null and $user != "") then .["Kasa configs"].Username = $user else . end) |
            (if ($pass != null and $pass != "") then .["Kasa configs"].Password = $pass else . end)
        '
        for sw in "${!switches[@]}"; do
            jq_args+=(--arg "${sw,,}" "${switches[$sw]}")
            jq_script+=" | (if (\$${sw,,} != null and \$${sw,,} != \"\") then .[\"Kasa configs\"].Device_IPs.${sw} = \$${sw,,} else . end)"
        done
        jq "${jq_args[@]}" "$jq_script" data.json > "$tmpfile" && mv "$tmpfile" data.json
    else
        # Fallback: naive sed replacement (will not add new fields if missing)
        if [ -n "$kasa_user" ]; then
            sed -i "s/\"Username\": \".*\"/\"Username\": \"$kasa_user\"/" data.json
        fi
        if [ -n "$kasa_pass" ]; then
            sed -i "s/\"Password\": \".*\"/\"Password\": \"$kasa_pass\"/" data.json
        fi
        for sw in "${!switches[@]}"; do
            sed -i "s/\"$sw\": \".*\"/\"$sw\": \"${switches[$sw]}\"/" data.json
        done
    fi
else
    echo "Skipping Kasa switch configuration."
fi

read -p "Are you running on a Raspberry Pi with sensors attached? (y/n): " is_pi
if [[ "$is_pi" != "y" && "$is_pi" != "Y" ]]; then
    export GROWPI_DEV=1
    echo "Development mode enabled (mock sensors)."
else
    pip install adafruit-circuitpython-htu21d w1thermsensor gpiozero python-kasa
fi

# Kill any running backend/frontend processes
echo "Stopping any running backend/frontend servers..."
pkill -f "python app.py" || true
pkill -f "vite" || true

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