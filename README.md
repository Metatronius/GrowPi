# GrowPi — Raspberry Pi IoT Controller

A web-based control panel for Raspberry Pi grow projects.  
**Backend:** Flask API (Python)  
**Frontend:** Svelte + Vite (JavaScript)

---

## Features

- Real-time monitoring of temperature, humidity, water temperature, and pH
- Automated control of fan, humidifier, and grow lights via Kasa smart plugs
- Configurable ideal ranges for each grow stage
- Light scheduling and pH calibration
- Email/SMS notifications for out-of-range conditions
- Modular, easy-to-extend codebase

---

## Prerequisites

- **Raspberry Pi** (recommended, required for GPIO and sensors)
- **Python 3.9+**
- **Node.js** (v18+ recommended) and **npm**
- **git**

### Hardware Sensors Used

- **HTU21D**: Temperature & Humidity sensor (I2C)
- **MCP3008**: 8-channel ADC for analog sensors (SPI)
- **DS18B20**: Water temperature sensor (1-Wire) or analog sensor via MCP3008
- **Analog pH Sensor**: Recommended to use the Atlas Scientific Surveyor Analog pH kit because it can be left in the resevoir. Connected via MCP3008
- **Kasa Smart Plugs**: For controlling Fan, Humidifier, and Light (WiFi)

---
## Project Structure

```
GrowPi/
├── backend/
│   ├── app.py
│   ├── data.json
│   ├── requirements.txt
│   ├── controls/
│   └── meters/
├── frontend/
│   ├── dist/
│   ├── src/
│   ├── index.html
│   └── vite.config.js
└── README.md
```

---

## Hardware Setup

- **HTU21D**: Connect to I2C pins (SDA/SCL) on the Pi.
- **MCP3008**: Connect to SPI pins (MISO, MOSI, SCLK, CE0/CE1).
- **DS18B20**: Connect to a GPIO pin (with pull-up resistor) or via MCP3008.
- **pH Sensor**: Connect analog output to MCP3008 channel.
- **Kasa Smart Plugs**: Set up via Kasa app, ensure on same WiFi as Pi.

---

## Scripts

- **install.sh**: Automates backend/frontend setup and startup.
- **restart.sh**: Restarts backend and frontend servers.

---

## Quick Install (Recommended)

You can use the provided `install.sh` script to automate the entire setup process for both backend and frontend.

### 1. Make the script executable

```bash
chmod +x install.sh
```

### 2. Run the installer

```bash
./install.sh
```

- The script will prompt you to specify if you are running on a Raspberry Pi with sensors attached.
- It will set up the Python backend, Node.js frontend, install all dependencies, and start both servers in the background.
- Logs will be saved as `backend.log` and `frontend.log` in the project directory.

### 3. Access the Web UI

- On your Pi: [http://localhost:5173](http://localhost:5173)
- On another device: [http://"<your-pi-ip>":5173](http://<your-pi-ip>:5173)

---

**Manual installation steps are below if you prefer to set up each part yourself.**

## Installation (Step-by-Step)

### 1. Clone the Repository

```bash
git clone https://github.com/Metatronius/Raspberry_pi.git
cd Raspberry_pi/GrowPi
```

### 2. Backend Setup (Python/Flask)

#### a. Create and activate a Python virtual environment

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
```

#### b. Install Python dependencies

```bash
pip install -r requirements.txt
```

#### c. (Raspberry Pi only) Install hardware dependencies

```bash
pip install adafruit-circuitpython-htu21d w1thermsensor gpiozero python-kasa
```

#### d. (Development only) If you are NOT on a Raspberry Pi, set the environment variable to mock sensors:

```bash
export GROWPI_DEV=1
```

#### e. Start the backend server

```bash
python app.py
```

The backend API will be available at `http://localhost:5000` or `http://<your-pi-ip>:5000`.

---

### 3. Frontend Setup (Svelte/Vite)

#### a. Install Node.js (v18+ recommended) and npm if not already installed

- [Node.js download page](https://nodejs.org/)

#### b. Install frontend dependencies

```bash
cd ../frontend
npm install
```

#### c. Start the frontend development server

```bash
npm run dev -- --host
```

- The frontend will be available at `http://<your-pi-ip>:5173` on your network.

---

### 4. Configuration

- Edit `backend/data.json` to match your sensor pins and Kasa device info.
- Make sure your Pi and Kasa devices are on the same network.

---

### 5. Access the Web UI

- On your Pi: [http://localhost:5173](http://localhost:5173)
- On another device: [http://<your-pi-ip>:5173](http://<your-pi-ip>:5173)

---

### 6. Troubleshooting

- If you get errors about missing hardware, set `export GROWPI_DEV=1` before running the backend.
- If you cannot access the frontend from another device, make sure you started Vite with `--host` and your firewall allows port 5173.
- If you see CORS or proxy errors, check your `vite.config.js` proxy settings.

---


## License

GPL License

---

## Credits

- [Svelte](https://svelte.dev/)
- [Flask](https://flask.palletsprojects.com/)
- [python-kasa](https://python-kasa.readthedocs.io/)
- [Adafruit CircuitPython HTU21D](https://github.com/adafruit/Adafruit_CircuitPython_HTU21D)