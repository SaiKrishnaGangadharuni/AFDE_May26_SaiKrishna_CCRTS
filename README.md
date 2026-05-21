# Customer Complaint & Resolution Tracking System (CCRTS)

> **Capstone Phase 1** — Full-stack web application for centralised customer complaint management with role-based access, SLA tracking, escalation workflow, and analytics.

---

## 1. Project Overview

CCRTS is an enterprise complaint management platform that lets customers register issues, support agents work on them, supervisors monitor SLAs and escalations, and admins manage users and categories. The system maintains a full audit trail of every complaint's lifecycle, calculates SLA due-times automatically based on priority, raises notifications at every important step, and provides dashboards for tracking complaint trends and agent performance.

The application can be adapted to industries such as Telecom, Banking, Retail, E-Commerce, Healthcare, Logistics, Education, Utility Services, and IT Support.

## 2. Features Implemented (Phase 1)

| # | Module | Features |
|---|---|---|
| 1 | **Authentication & Authorisation** | Register / Login / Forgot-password / JWT-based sessions / 4 roles with RBAC |
| 2 | **Complaint Registration** | Auto-generated complaint number (`CMP-YYYYMMDD-XXXX`), priority, category, multi-file attachments |
| 3 | **Workflow Management** | 8 statuses with validated state transitions, assignment, reassignment |
| 4 | **SLA & Escalation** | Per-priority SLA (4h / 24h / 48h / 72h), live breach detection, escalation with reason |
| 5 | **Resolution** | Notes, resolution timestamp, customer confirmation, reopen flow |
| 6 | **Notifications** | In-app notifications on every status change, assignment, escalation; unread counter |
| 7 | **Dashboard & Analytics** | Role-scoped stats, agent performance, category breakdown, monthly trends, CSAT |
| 8 | **Feedback** | 1-5 star ratings + comments after resolution; customer-satisfaction report |
| + | **Audit Trail** | Complete history of every action on every complaint |

## 3. Technology Stack

| Layer | Technology |
|---|---|
| Frontend | React 18 (Vite) · React Router · Tailwind CSS · Axios · Recharts |
| Backend | FastAPI · SQLAlchemy 2 · Pydantic v2 · python-jose (JWT) · passlib (bcrypt) |
| Database | SQLite (default, file-based) — PostgreSQL/MySQL ready |
| Tooling | Python 3.10+ · Node 18+ · npm · Postman · GitHub |

## 4. Repository Structure

```
CCRTS/
├── backend/
│   ├── app/
│   │   ├── core/         # config, security (JWT/bcrypt), database, deps
│   │   ├── models/       # SQLAlchemy ORM models + enums + SLA rules
│   │   ├── schemas/      # Pydantic request/response schemas
│   │   ├── routes/       # auth, users, categories, complaints, notifications, dashboard
│   │   ├── services/     # business logic (complaint state-machine, SLA, history)
│   │   └── main.py       # FastAPI app entrypoint
│   ├── uploads/          # complaint attachments
│   ├── seed.py           # populate DB with roles, categories, demo users + complaints
│   ├── .env.example      # config overrides template
│   └── ccrts.db          # SQLite file (created after first seed/run)
├── frontend/
│   ├── src/
│   │   ├── components/   # Layout, ProtectedRoute, Badges
│   │   ├── context/      # AuthContext (JWT in localStorage)
│   │   ├── lib/          # api.js (axios), helpers.js
│   │   ├── pages/        # Login, Register, Dashboard, ComplaintList/New/Detail,
│   │   │                 # AgentQueue, Escalations, Reports, Users, Categories,
│   │   │                 # Notifications, ForgotPassword
│   │   ├── App.jsx       # Router with role-protected routes
│   │   └── main.jsx
│   ├── index.html
│   ├── vite.config.js    # proxies /api → backend
│   ├── tailwind.config.js
│   └── package.json
├── database/
│   ├── schema.sql        # canonical DDL (SQLite/PostgreSQL-compatible)
│   ├── sample-data.sql   # roles + categories seed
│   ├── er-diagram.md     # ER + workflow diagrams (Mermaid)
│   └── README.md
├── docs/
│   ├── API.md            # endpoint reference with curl examples
│   └── SETUP.md          # detailed setup walkthrough
├── screenshots/          # UI / API screenshots (capture during testing)
├── requirements.txt      # Python deps
├── .gitignore
└── README.md             # this file
```

## 5. Setup Instructions

### 5.1 Backend

```bash
cd backend

# (Optional) create virtual environment
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

# Install dependencies (from project root requirements.txt)
pip install -r ../requirements.txt

# Seed the database (creates ccrts.db + demo data)
python seed.py

# Run the API
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API is now live at:
- **Swagger UI:** http://localhost:8000/docs
- **Redoc:** http://localhost:8000/redoc
- **OpenAPI JSON:** http://localhost:8000/openapi.json

### 5.2 Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at **http://localhost:5173** and proxies API calls to the backend.

### 5.3 Demo Accounts (after running seed.py)

| Role | Email | Password |
|---|---|---|
| Admin | `admin@example.com` | `Admin@123` |
| Supervisor | `supervisor@example.com` | `Super@123` |
| Support Agent | `agent1@example.com` | `Agent@123` |
| Support Agent | `agent2@example.com` | `Agent@123` |
| Support Agent | `agent3@example.com` | `Agent@123` |
| Customer | `customer1@example.com` | `Customer@123` |
| Customer | `customer2@example.com` | `Customer@123` |
| Customer | `customer3@example.com` | `Customer@123` |

## 6. API Documentation

Comprehensive endpoint reference is in **[`docs/API.md`](docs/API.md)**.

The interactive Swagger UI (http://localhost:8000/docs) lets you call any endpoint directly — click *Authorize* and paste a JWT obtained from `POST /api/auth/login`.

**Endpoint summary (32 total):**

```
Authentication
  POST   /api/auth/register
  POST   /api/auth/login
  POST   /api/auth/forgot-password
  GET    /api/auth/me

Users (Admin/Supervisor)
  GET    /api/users
  POST   /api/users
  GET    /api/users/agents
  GET    /api/users/roles
  PUT    /api/users/{user_id}
  DELETE /api/users/{user_id}

Categories
  GET    /api/categories
  POST   /api/categories
  PUT    /api/categories/{category_id}
  DELETE /api/categories/{category_id}

Complaints
  POST   /api/complaints
  GET    /api/complaints                  (search & filter)
  GET    /api/complaints/{id}
  PUT    /api/complaints/{id}
  DELETE /api/complaints/{id}
  POST   /api/complaints/{id}/assign
  POST   /api/complaints/{id}/status
  POST   /api/complaints/{id}/escalate
  POST   /api/complaints/{id}/resolve
  POST   /api/complaints/{id}/reopen
  GET    /api/complaints/{id}/history
  POST   /api/complaints/{id}/attachments
  GET    /api/complaints/{id}/attachments/{aid}/download
  POST   /api/complaints/{id}/feedback

Notifications
  GET    /api/notifications
  GET    /api/notifications/unread-count
  POST   /api/notifications/{id}/read
  POST   /api/notifications/read-all

Dashboard & Analytics
  GET    /api/dashboard/stats
  GET    /api/dashboard/agent-performance
  GET    /api/dashboard/category-breakdown
  GET    /api/dashboard/trends
  GET    /api/dashboard/customer-satisfaction
```

## 7. Database Design

See **[`database/er-diagram.md`](database/er-diagram.md)** for the full ER diagram and workflow state machine.

**7 tables:** `roles`, `users`, `categories`, `complaints`, `complaint_history`, `attachments`, `feedback`, `notifications`.

Schema script: **[`database/schema.sql`](database/schema.sql)**

## 8. Screenshots

Place screenshots in `screenshots/` once captured. Suggested shots for the submission:

1. **`01_login.png`** — Login page with demo creds
2. **`02_dashboard_admin.png`** — Admin dashboard with stats & charts
3. **`03_complaint_list.png`** — Complaint list with filters
4. **`04_complaint_new.png`** — New complaint form
5. **`05_complaint_detail.png`** — Detail page with timeline & actions
6. **`06_agent_queue.png`** — Agent's personal queue
7. **`07_escalations.png`** — Supervisor escalations view
8. **`08_reports.png`** — Reports / analytics
9. **`09_users.png`** — Admin user management
10. **`10_categories.png`** — Category management
11. **`11_swagger_ui.png`** — Auto-generated API docs
12. **`12_postman_login.png`** — Postman testing `POST /api/auth/login`
13. **`13_postman_complaints.png`** — Postman testing complaints flow

## 9. Testing

Test the API via:
- **Swagger UI** at `/docs` (easiest)
- **Postman** — collection can be imported from `/openapi.json`
- **curl** — examples are in `docs/API.md`

Sample curl:

```bash
# Login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"Admin@123"}'

# List complaints (use the token returned above)
curl http://localhost:8000/api/complaints \
  -H "Authorization: Bearer <YOUR_TOKEN>"
```

## 10. Project Status — Phase 1 Deliverables

- [x] Requirement specification — understood from project doc
- [x] High-level design — 3-tier architecture documented in README
- [x] Database design — schema.sql + ER diagram
- [x] Responsive UI — Tailwind responsive layout
- [x] Login & dashboard pages
- [x] Complaint management screens (List, New, Detail with full workflow)
- [x] REST API — 32 endpoints
- [x] Authentication APIs — register/login/forgot/me
- [x] Complaint CRUD APIs
- [x] Notification APIs
- [x] Database schema & sample data
- [ ] Screenshots (capture after running locally)

## 11. Future Enhancements (Out of Scope for Phase 1)

- AI-based complaint categorisation / sentiment analysis
- Chatbot / WhatsApp / SMS integration
- Mobile application
- Social-media complaint integration
- Multi-language support
- Real-time WebSocket notifications

## 12. License & Plagiarism Statement

This is original work created for the AFDE Jan 2026 capstone Phase 1 submission. No code has been copied from another participant's repository or any third-party project. All open-source dependencies are used under their respective licenses (MIT/BSD/Apache 2.0).

---

# Phase 2 — ETL Pipeline & Analytics Dashboard

Phase 2 extends the Phase 1 platform with a Python + Pandas ETL pipeline that ingests a CSV complaint dataset, cleans it, loads it into separate analytics tables, and surfaces the results through a new **Analytics & ETL** dashboard.

## 13. Phase 2 Scope (per spec)

- Import complaint datasets
- Track SLA violations
- Generate complaint trend reports
- Build resolution analytics

## 14. ETL Workflow

```
datasets/complaints_dataset.csv      <-- 218 rows (mixed-case, dupes, nulls intentional)
                |
                | etl/extract.py     Pandas read_csv + schema check
                v
            raw DataFrame
                |
                | etl/transform.py   1. drop empty rows
                |                    2. drop duplicates by complaint_id
                |                    3. strip whitespace
                |                    4. normalize priority   (low/HIGH/Med -> Low/High/Medium)
                |                    5. normalize status     (in_progress/InProgress -> In Progress)
                |                    6. coerce numeric & datetime columns
                |                    7. backfill sla_hours from canonical map
                |                    8. compute sla_breached = resolution_time > sla_hours
                v
            cleaned DataFrame (210 rows)
                |
                | pandas aggregations
                v
            ┌──────────────────┬──────────────────┬───────────────────────┬──────────────────────┐
            v                  v                  v                       v                      v
     analytics_complaints   category_stats   sla_breach_report    resolution_trends    agent_performance
                                                                                                  (etl/load.py)
```

### Stages explained

| Stage | File | What it does |
|------|------|--------------|
| **Extract** | `etl/extract.py` | Reads `datasets/complaints_dataset.csv` (or `.xlsx`) via Pandas. Verifies required columns are present. |
| **Transform** | `etl/transform.py` | Cleans, normalizes, and derives `sla_breached`. Builds 4 aggregation DataFrames (category, SLA-by-priority, monthly trend, per-agent). |
| **Load** | `etl/load.py` | Truncate + insert into 5 analytics tables. Each ETL run also records a row in `analytics_etl_runs` (audit log). |
| **Orchestrator** | `etl/run_etl.py` | Wires Extract -> Transform -> Load together. CLI + programmatic API. |

## 15. Phase 2 — How to Run the ETL

### From the command line
```bash
cd AFDE_May26_SaiKrishna_CCRTS
# Phase 1 venv already has SQLAlchemy & FastAPI. Add pandas:
backend\venv\Scripts\activate
pip install pandas openpyxl
python -m etl.run_etl
```

You should see:
```
[ETL] Source: datasets/complaints_dataset.csv
[ETL] Summary:
  status: success
  run_id: 1
  rows_extracted: 218
  rows_after_clean: 210
  duplicates_dropped: 5
  null_rows_dropped: 3
  rows_loaded: 210
```

### From the UI
1. Start the backend: `uvicorn app.main:app --reload`
2. Start the frontend: `cd frontend && npm run dev`
3. Login as Admin or Supervisor
4. Open the **Analytics** menu item
5. Click the **Run ETL** button — the dashboard refreshes with new data

## 16. Phase 2 — Analytics API endpoints

| Method | URL | Auth | Description |
|--------|-----|------|-------------|
| POST | `/api/etl/run` | Admin / Supervisor | Trigger the ETL pipeline against the default dataset |
| GET | `/api/etl/runs` | Any logged-in user | List recent ETL runs |
| GET | `/api/etl/latest` | Any logged-in user | Latest ETL run summary |
| GET | `/api/analytics/summary` | Any logged-in user | Overall counts + breach rate + last-run summary |
| GET | `/api/analytics/sla-breaches` | Any logged-in user | SLA breaches grouped by priority |
| GET | `/api/analytics/categories` | Any logged-in user | Complaints + resolution averages per category |
| GET | `/api/analytics/resolution-trends` | Any logged-in user | Monthly resolution-time trend |
| GET | `/api/analytics/agents` | Any logged-in user | Agent-wise handled / resolved / breach metrics |

## 17. Phase 2 — Analytics Tables (separate from operational tables)

| Table | Purpose |
|-------|---------|
| `analytics_complaints` | Cleaned, normalized complaint rows from the ETL run |
| `analytics_category_stats` | Counts + breach + avg resolution per category |
| `analytics_sla_breaches` | Breach count + breach rate per priority |
| `analytics_resolution_trends` | Monthly resolution metrics |
| `analytics_agent_performance` | Per-agent handled / resolved / breach + avg resolution |
| `analytics_etl_runs` | Audit log of every ETL execution |

## 18. Phase 2 — Dataset

`datasets/complaints_dataset.csv` — 218 rows including 5 intentional duplicates and 3 fully-empty rows so the Transform stage has work to do.

Columns: `complaint_id, complaint_category, priority, sla_hours, resolution_time_hours, status, agent_name, created_date, resolved_date`

## 19. Phase 2 — Deliverables Checklist

- [x] ETL scripts (`etl/` package — extract / transform / load / run_etl)
- [x] Reporting / analytics tables (6 new tables, isolated from operational)
- [x] Analytics dashboards (new **Analytics** page with Recharts)
- [x] Updated APIs (`/api/etl/*` + `/api/analytics/*`)
- [x] Dataset committed under `datasets/`
- [x] README updated with ETL workflow explanation
- [ ] Screenshots of ETL execution and dashboard (capture during demo)
