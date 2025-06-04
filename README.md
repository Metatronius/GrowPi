# GrowPi — Raspberry Pi IoT Controller

A web-based control panel for Raspberry Pi grow projects.  
**Backend:** Flask API (Python)  
**Frontend:** Svelte + Vite (JavaScript)

---

## Prerequisites

- **Raspberry Pi** (recommended, required for GPIO and sensors)
- **Python 3.9+**
- **Node.js** (v18+ recommended) and **npm**
- **git**

---

## 1. Clone the Repository

```sh
git clone https://github.com/Metatronius/Raspberry_pi.git
cd Raspberry-pi/GrowPi
```

---

## 2. Frontend Setup

```sh
cd frontend
npm install
npm run build
```

- For development preview:  
  ```sh
  npm run dev
  ```
- The built frontend will be in `frontend/dist/`.

---

## 3. Backend Setup

```sh
cd ../backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**Install hardware dependencies (on Raspberry Pi):**

```sh
pip install adafruit-circuitpython-htu21d w1thermsensor gpiozero python-kasa
```

---

## 4. Enable 1-Wire and I2C Interfaces (Raspberry Pi only)

- Run `sudo raspi-config`
- Enable **I2C** and **1-Wire** under *Interfacing Options*
- Reboot if prompted

---

## 5. Configure `data.json`

Edit `backend/data.json` to match your sensor pins and Kasa device info.

---

## 6. Run the Backend Server

```sh
cd backend
source venv/bin/activate
python app.py
```

- The API will be available at:  
  `http://localhost:5000`  
  or  
  `http://<your-raspberrypi-ip>:5000`

---

## 7. Access the Web UI

Open a browser and go to:  
`http://<your-raspberrypi-ip>:5000`

---

## Notes

- **GPIO and sensors only work on Raspberry Pi hardware.**
- For development on other platforms, mock or comment out hardware-specific code.
- For Kasa device control, your Pi and Kasa devices must be on the same network.

---

## Troubleshooting

- If you get import errors for sensor libraries, ensure you installed all hardware dependencies.
- If sensors are not detected, check wiring and that I2C/1-Wire are enabled.

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

