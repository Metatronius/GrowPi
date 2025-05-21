# GrowPi — Raspberry Pi IoT Controller

A simple web-based control panel for Raspberry Pi projects.  
Built with Flask for the backend API and Svelte + Vite for the frontend UI.

---

## Project Structure

```
GrowPi/
├── backend/
│   ├── app.py
│   └── venv/
├── frontend/
│   ├── dist/
│   ├── src/
│   ├── index.html
│   └── vite.config.js
└── README.md
```

---

## Setup Instructions

### Clone the project

```
git clone https://github.com/Metatronius/Raspberry_pi.git
cd GrowPi
```

---

### Frontend Setup (Svelte + Vite)

```
cd frontend
npm install
npm run build
```

For development preview:

```
npm run dev
```

---

### Backend Setup (Flask)

```
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Or manually install:

```
pip install Flask flask-cors
```

Then run the backend:

```
python app.py
```

It will be available at:

- `http://localhost:5000`
- `http://<your-raspberrypi-ip>:5000`

---

## API Endpoints

- `GET /api/status` — JSON response with example temperature and humidity data.

```
{
  "temperature": 68,
  "humidity": 55
}
```

---

## Frontend Routes

- `/` — Serves `index.html` from `frontend/dist/`
- `/assets/*` — Serves JS/CSS assets built by Vite
- `/favicon.ico` — Optional favicon file (if added)

---

## Access from Other Devices

Find your Raspberry Pi’s IP with:

```
hostname -I
```

Then open `http://<raspberrypi-ip>:5000` in any browser on the same network.

---

## Notes

- The Vite base path is set to relative (`'./'`) in `vite.config.js`
- Rebuild the frontend after making any changes:

```
cd frontend
npm run build
```

---

## Future Improvements

- Add environment sensor integrations (DHT22, BME280)
- Control GPIO devices (relays, fans, lights)
- Add user authentication
- Deploy with a WSGI server like Gunicorn for production use

---

## License

MIT License
