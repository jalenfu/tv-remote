# PC TV Remote

Control your PC's media and browser from your phone! This project lets you play/pause, control volume, open URLs, and even select Twitch streams from a mobile-friendly web interface.

---

## Features
- Play/Pause, Next, Previous, Volume Up/Down
- Open any URL in Firefox
- Quick links for YouTube, Twitch, Netflix, Crunchyroll
- Select and open Twitch streams by channel name
- Mobile-friendly web UI

---

## Setup Instructions

### 1. Clone or Download the Project

```
git clone <repo-url>
cd tv-remote-2
```

### 2. Install Python (if not already installed)
- [Download Python](https://www.python.org/downloads/) (version 3.8+ recommended)

### 3. Create and Activate a Virtual Environment (Recommended)

On Windows:
```
python -m venv venv
venv\Scripts\activate
```

On Mac/Linux:
```
python3 -m venv venv
source venv/bin/activate
```

### 4. Install Dependencies

```
pip install -r requirements.txt
```

### 5. Download and Set Up geckodriver
- Download the latest [geckodriver release](https://github.com/mozilla/geckodriver/releases) for your OS.
- Extract the executable and place it in the project folder (or add it to your system PATH).

### 6. Run the Server

```
uvicorn main:app --host 0.0.0.0 --port 8000
```

---

## Frontend Setup

The frontend is a React app located in the `frontend/` directory.

### Development

1. Install dependencies:
   ```sh
   cd frontend
   npm install
   ```
2. Start the development server:
   ```sh
   npm run dev
   ```
   The app will be available at the URL shown in the terminal (usually http://localhost:5173).

### Production Build

1. Build the frontend for production:
   ```sh
   cd frontend
   npm run build
   ```
   This will output static files to `frontend/dist/`.

2. The FastAPI backend is configured to serve the production build from `frontend/dist` automatically.

### Notes
- The frontend communicates with the backend via the `/api/` endpoints.
- For local development, you may need to configure CORS or use a proxy if running frontend and backend on different ports.
- Make sure the backend is running for full functionality.

---

## Accessing the Web UI from Your Phone

1. **Connect your phone and PC to the same Wi-Fi/network.**
2. **Find your PC's local IP address:**
   - On Windows, run `ipconfig` in Command Prompt and look for `IPv4 Address` (e.g., `192.168.1.100`).
3. **On your phone, open a browser and go to:**
   ```
   http://<your-pc-ip>:8000/
   ```
   (Replace `<your-pc-ip>` with your actual IP address.)
4. **Use the web interface to control your PC!**

---

## Troubleshooting
- If you can't access the server from your phone:
  - Make sure the server is running and your firewall allows connections on port 8000.
  - Double-check that both devices are on the same network.
  - Try accessing `http://<your-pc-ip>:8000/static/index.html` directly.
- If Selenium features (Twitch stream selection) don't work:
  - Ensure `geckodriver` is in your project folder or PATH.
  - Make sure Firefox is installed.

---

## Customization
- Edit `static/index.html` to change the web UI.
- Add more endpoints in `main.py` for additional controls or site integrations.

---

## License
MIT (or your preferred license) 