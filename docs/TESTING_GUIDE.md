# End-to-End Testing Guide

This is the checklist used to verify every feature of CCRTS works correctly.
Follow each phase in order; expected output is documented at every step.

> Total time: ~20-30 minutes when everything works first try.

---

## Phase 0 — Prerequisites Check

Open **PowerShell** (or a VS Code terminal) and run:

```powershell
python --version
node --version
npm --version
git --version
```

**Expected:** Python ≥ 3.10, Node ≥ 18, npm ≥ 9, Git installed.

---

## Phase 1 — Backend Setup

```powershell
cd D:\path\to\repo\backend

# Create and activate virtual environment
python -m venv venv
.\venv\Scripts\activate

# Install Python dependencies
pip install -r ..\requirements.txt

# Seed the SQLite database with demo data
python seed.py
```

**Expected after seed:** `✓ Seed complete!` followed by 8 demo accounts printed (Admin / Supervisor / 3 Agents / 3 Customers).

A new file `ccrts.db` (~50 KB) appears in the backend folder.

---

## Phase 2 — Start the Backend Server

```powershell
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Expected:** `INFO: Uvicorn running on http://0.0.0.0:8000`

Verify in browser:
- http://localhost:8000/         → JSON health check
- http://localhost:8000/docs     → Swagger UI listing 32 endpoints

📸 Screenshot: `11_swagger_ui.png`

---

## Phase 3 — Test the API via Swagger

1. In Swagger, expand `POST /api/auth/login` → Try it out → submit:
   ```json
   { "email": "admin@example.com", "password": "Admin@123" }
   ```
   Expect 200 with `access_token` in response.

2. Click **Authorize** (top-right) → enter username `admin@example.com` and password `Admin@123` → Authorize → Close.

3. Try a few endpoints with the lock now closed:
   - `GET /api/auth/me`               → 200, your admin user
   - `GET /api/complaints`            → 200, 8 complaints
   - `GET /api/dashboard/stats`       → 200, role-scoped totals
   - `POST /api/complaints` with `{ "subject":"...", "description":"...", "category_id":1, "priority":"High" }`  → 201

📸 Screenshots: `12_swagger_login.png`, `13_swagger_create_complaint.png`

---

## Phase 4 — Frontend Setup

In a **new** terminal (keep uvicorn running):

```powershell
cd D:\path\to\repo\frontend
npm install
npm run dev
```

**Expected:** `VITE ready in 400 ms` → http://localhost:5173/

Open the URL — login page loads with pre-filled admin credentials.

📸 Screenshot: `01_login.png`

---

## Phase 5 — UI Walkthrough (all 4 roles)

### 5A — Admin (admin@example.com / Admin@123)
- Dashboard: 8 stat cards + pie chart + bar chart + recent complaints
- Complaints list: filters (search, status, priority, category, SLA) all work
- Complaint detail: actions toolbar, audit trail, attachments section visible
- Users page: 8 users listed, can create new user
- Categories page: 7 categories, can add new

📸 Screenshots: `02_dashboard_admin.png`, `03_complaint_list.png`, `05_complaint_detail.png`, `09_users.png`, `10_categories.png`

### 5B — Customer (customer1@example.com / Customer@123)
- Dashboard scoped to this customer's complaints only
- Create new complaint: subject, description, category, priority, attachments
- Notifications list shows confirmation of new complaint

📸 Screenshot: `04_complaint_new.png`

### 5C — Supervisor (supervisor@example.com / Super@123)
- Assign the new complaint to an agent → status changes to Assigned
- Escalations page shows escalated + SLA-breached complaints
- Reports page: agent performance, category distribution, trends, CSAT

📸 Screenshots: `07_escalations.png`, `08_reports.png`

### 5D — Support Agent (agent1@example.com / Agent@123)
- My Queue shows assigned complaints
- Update status to "In Progress" → "Resolved" with resolution notes

📸 Screenshot: `06_agent_queue.png`

### 5E — Back to Customer (customer1)
- Confirm Resolution & Close → status becomes Closed
- Submit Feedback (5 stars + comment) → feedback section appears

---

## End-to-End Lifecycle Verification

After 5E, the same complaint will have walked through:

```
Open → Assigned → In Progress → Resolved → Closed
```

with 6 audit-trail entries showing the correct actors (customer, supervisor, agent), and dashboard metrics reflecting the change. SLA timer, notifications, and feedback all visible on the detail page.

---

## Cleanup

Stop the servers with `Ctrl + C` in each terminal.

Then commit your work:

```powershell
git add .
git commit -m "<descriptive message>"
git push
```

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| `python` not recognised | Install Python from python.org with "Add to PATH" |
| `npm` blocked by execution policy | Use `npm.cmd` instead, or run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` |
| `passlib` error reading bcrypt version | Already patched — use `bcrypt` directly per current `security.py` |
| Port 8000/5173 in use | Stop the other process, or use `--port 8001` / `--port 5174` |
| `disk I/O error` from SQLite | Move the project off cloud-synced folder, or set `DATABASE_URL=sqlite:///C:/temp/ccrts.db` |
| 401 Unauthorized on every API call | Token expired (8h default) — re-Authorize in Swagger |
| Frontend shows blank page | Check browser console (F12); make sure backend is running |
