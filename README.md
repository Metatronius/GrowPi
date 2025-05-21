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

### Frontend Setup

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

### Backend Setup

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

