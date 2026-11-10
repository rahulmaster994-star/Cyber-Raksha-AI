# 🚀 CYBER RAKSHA AI — DEPLOYMENT & OPERATIONS GUIDE
**Stage 8: Local, Containerized & Free-Tier Deployment Runbook**

---

## 1. Prerequisites

- Python 3.11+ (tested on Python 3.11 - 3.13)
- Node.js 20+ and npm 10+
- Git
- Optional: Docker and Docker Compose (v2.20+)

---

## 2. Option A: Local Native Deployment (Recommended for Development)

### A. Backend Setup
```bash
# 1. Navigate to backend directory
cd backend

# 2. Create virtual environment
python -m venv venv

# Windows
venv\Scripts\activate
# Linux/macOS
source venv/bin/activate

# 3. Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# 4. Copy configuration
cp .env.example .env

# 5. Start ASGI server
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```
Backend will be live at `http://127.0.0.1:8000`.  
Swagger docs available at `http://127.0.0.1:8000/docs`.

### B. Frontend Setup
```bash
# 1. In a separate terminal, navigate to frontend directory
cd frontend

# 2. Install dependencies
npm install

# 3. Start Vite dev server
npm run dev
```
Frontend will be live at `http://localhost:5173`.

---

## 3. Option B: Containerized Deployment with Docker Compose

A multi-stage container build orchestrates backend and frontend with zero external dependencies.

```bash
# 1. From root directory, build and launch containers
docker compose up -d --build

# 2. Verify container health status
docker compose ps

# 3. Check logs
docker compose logs -f backend
```

- Backend API: `http://localhost:8000`
- Frontend Web App: `http://localhost` (Port 80)
- Health check runs automatically every 30 seconds.

---

## 4. Option C: Zero-Budget / Free-Tier Cloud Deployment

Cyber Raksha AI requires zero paid APIs and can run on free-tier platforms:

### 1. Render.com / Railway.app (Backend Web Service)
- **Service Type:** Web Service (Docker or Python 3.11).
- **Build Command:** `pip install -r backend/requirements.txt`
- **Start Command:** `cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- **Environment Variables:**
  - `APP_ENV=production`
  - `DEBUG=False`
  - `DATABASE_URL=sqlite:///./cyber_raksha.db` (or attach Render Free PostgreSQL)
  - `CORS_ORIGINS=https://your-frontend.vercel.app`
- **Free Tier Consideration:** Free web services spin down after 15 minutes of inactivity; allow 30-50s cold start on first request.

### 2. Vercel / Cloudflare Pages / Netlify (Frontend Web App)
- **Framework Preset:** Vite
- **Root Directory:** `frontend`
- **Build Command:** `npm run build`
- **Output Directory:** `dist`
- **Environment Variables:**
  - `VITE_API_BASE_URL=https://your-backend.onrender.com`

---

## 5. Browser Extension Deployment

1. Open Google Chrome, Microsoft Edge, or Brave.
2. Navigate to `chrome://extensions` or `edge://extensions`.
3. Enable **Developer mode** toggle in the top-right corner.
4. Click **Load unpacked**.
5. Select the `browser_extension/` directory from this repository.
6. The 🛡️ Cyber Raksha AI shield icon will appear in your browser toolbar.
7. Click Options (or the ⚙️ icon in popup) to configure the target backend API URL.

---

## 6. Mobile & Android PWA Installation

1. Deploy frontend to an HTTPS domain (e.g. Vercel) or open `http://localhost:5173` on mobile Chrome via local network.
2. In Chrome on Android, tap the three-dot menu (**⋮**) in the top right.
3. Tap **Add to Home screen** or **Install Cyber Raksha AI**.
4. Confirm installation. The app will install to the Android app drawer.
5. **Share Target Testing:** In WhatsApp, SMS, or any browser, select a suspicious URL -> tap **Share** -> choose **Cyber Raksha AI**. The PWA opens with the URL pre-filled in the Phishing Scanner.

---

## 7. Database Maintenance: Backup & Restore

### Create Instant Verified Backup
```bash
python backend/scripts/backup_db.py
```
Output:
```
[*] Starting backup from cyber_raksha.db...
[SUCCESS] Backup created successfully!
  Location: backend/backups/cyber_raksha_backup_20261108_000000.db
  Integrity: OK
  SHA256: [checksum]
```

### Restore from Most Recent Backup
```bash
python backend/scripts/restore_db.py
```
Safely validates integrity, creates a pre-restore safety copy, and restores tables.

