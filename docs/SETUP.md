# Detailed Setup Guide

This is a step-by-step walkthrough for a fresh machine. For quick start, see the [project README](../README.md).

## Prerequisites

| Tool | Minimum version | How to verify |
|---|---|---|
| Python | 3.10 | `python --version` |
| Node.js | 18 | `node --version` |
| npm | 9 | `npm --version` |
| git | any recent | `git --version` |

## Step 1 — Clone

```bash
git clone <your-repo-url> CCRTS
cd CCRTS
```

## Step 2 — Backend

### 2a. Virtual environment (recommended)

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 2b. Install Python packages

```bash
# from the backend/ directory
pip install -r ../requirements.txt
```

### 2c. (Optional) Configure environment

Copy `.env.example` to `.env` and adjust if you want a different SECRET_KEY or DATABASE_URL:

```bash
cp .env.example .env
```

To change the JWT secret (recommended for any non-throwaway deployment):
```
SECRET_KEY=<paste a long random string here>
```

### 2d. Seed the database

```bash
# Still in backend/
python seed.py
```

You should see output like:
```
Resetting schema...
Seeding roles...
Seeding categories...
Seeding users...
Seeding complaints...

✓ Seed complete!

Demo accounts:
  • Admin         admin@example.com         Admin@123
  • Supervisor    supervisor@example.com    Super@123
  ...
```

### 2e. Start the API server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Visit **http://localhost:8000/docs** — you should see the Swagger UI listing all 32 endpoints.

## Step 3 — Frontend

In a **new terminal**:

```bash
cd frontend
npm install
npm run dev
```

You should see:
```
VITE v5.4.x  ready in 400 ms
➜  Local:   http://localhost:5173/
```

Open **http://localhost:5173/** in your browser. The login page should appear pre-filled with the admin credentials; click *Sign in* to access the dashboard.

## Step 4 — Verify

Quick smoke test:

1. Log in as `admin@example.com / Admin@123` → see dashboard with 8 complaints
2. Click *Complaints* in the sidebar → filter by *SLA = Breached*
3. Open any complaint → review the audit trail
4. Sign out → log in as `customer1@example.com / Customer@123` → click *New Complaint*

## Common Issues

### `disk I/O error` from SQLite
Happens on some networked filesystems (NFS, certain Docker mounts). Move the DB to a local path:
```bash
# In backend/.env
DATABASE_URL=sqlite:////tmp/ccrts.db
```

### `email is not a valid email address` on `.local` domains
The `email-validator` library rejects reserved TLDs like `.local`. Use `.com`, `.org`, etc.

### Port already in use
Backend → change the `--port 8000` flag, then update `frontend/vite.config.js` proxy target.
Frontend → run with `npm run dev -- --port 3000`.

### CORS errors when running on different hosts
Add your origin to `CORS_ORIGINS` in `backend/app/core/config.py`.

### Tailwind classes not applying
Run `npm install` again, then `npm run dev`. The classes are JIT-compiled from `src/**/*.jsx`.

## Switching to PostgreSQL

1. Install PostgreSQL: https://www.postgresql.org/download/
2. Create a database: `createdb ccrts`
3. Install the driver: `pip install psycopg2-binary`
4. In `backend/.env`:
   ```
   DATABASE_URL=postgresql://postgres:password@localhost:5432/ccrts
   ```
5. Run `python seed.py` — SQLAlchemy handles the rest.

## Building Frontend for Production

```bash
cd frontend
npm run build
# Output goes to frontend/dist/ — serve with any static host (nginx, vercel, etc.)
```

## Where Do Things Live?

| Concern | File / Path |
|---|---|
| Add a new endpoint | `backend/app/routes/<module>.py` then include it in `app/main.py` |
| Add a DB column | `backend/app/models/models.py` + bump schema.sql, then delete `ccrts.db` and re-seed |
| Change SLA rules | `SLA_HOURS` dict in `backend/app/models/models.py` |
| Add a frontend page | `frontend/src/pages/<Name>.jsx` + register route in `App.jsx` |
| Change auth behaviour | `backend/app/core/security.py` and `app/core/deps.py` |
| File uploads | served from `backend/uploads/` (gitignored) |
