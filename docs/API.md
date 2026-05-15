# CCRTS API Reference

Base URL: `http://localhost:8000/api`

All endpoints (except `/auth/login`, `/auth/register`, `/auth/forgot-password`) require a Bearer JWT in the `Authorization` header.

The interactive Swagger UI at **`http://localhost:8000/docs`** is the easiest way to explore and call every endpoint.

---

## Authentication

### `POST /auth/register`
Public self-registration. Always creates a **Customer**.

Request:
```json
{
  "name": "Jane Doe",
  "email": "jane@example.com",
  "phone": "+91-9876543210",
  "password": "Strong@123"
}
```

Response `201`:
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "user": { "id": 9, "name": "Jane Doe", "email": "jane@example.com",
            "role": { "id": 4, "name": "Customer" }, "...": "..." }
}
```

### `POST /auth/login`
Request:
```json
{ "email": "admin@example.com", "password": "Admin@123" }
```
Response is identical to `/register`.

### `POST /auth/forgot-password`
Phase-1 simplified flow — supply email + new password. In production this would email a reset link.
```json
{ "email": "jane@example.com", "new_password": "NewStrong@123" }
```

### `GET /auth/me`
Returns the current user (verifies the JWT is still valid).

---

## Users

> Admin-only unless noted.

### `GET /users`
Optional query params: `role`, `q` (search name/email). Returns `UserOut[]`.

### `GET /users/agents`
Returns active SupportAgents — convenience for the assignment dropdown. Available to Admin & Supervisor.

### `GET /users/roles`
Returns all roles. Available to any authenticated user.

### `POST /users`
```json
{ "name": "...", "email": "...", "phone": "...",
  "password": "...", "role_id": 3 }
```

### `PUT /users/{user_id}`
Partial update — send any of `name`, `phone`, `is_active`, `role_id`.

### `DELETE /users/{user_id}`
Soft-delete (sets `is_active=false`). Cannot deactivate yourself.

---

## Categories

### `GET /categories`
Lists active categories. Available to any authenticated user.

### `POST /categories` (Admin)
```json
{ "name": "Refund Requests", "description": "..." }
```

### `PUT /categories/{id}` (Admin)
Partial update.

### `DELETE /categories/{id}` (Admin)
Soft-delete to preserve referential integrity.

---

## Complaints

### `POST /complaints`
Creates a complaint. Available to Customer / Supervisor / Admin.
```json
{
  "subject": "Internet down",
  "description": "No connectivity since morning",
  "category_id": 2,
  "priority": "Critical"
}
```
Response includes the auto-generated `complaint_number` (e.g. `CMP-20260513-3355`) and `sla_due_at` based on priority.

### `GET /complaints`
List + search + filter. Query parameters:

| Param | Type | Notes |
|---|---|---|
| `q` | string | Free-text across subject/description/number |
| `status` | enum | Open, Assigned, In Progress, Pending Customer Response, Escalated, Resolved, Closed, Reopened |
| `priority` | enum | Low, Medium, High, Critical |
| `category_id` | int | |
| `assigned_agent_id` | int | |
| `sla_breached` | bool | |
| `date_from`, `date_to` | ISO datetime | |
| `page`, `page_size` | int | defaults 1 and 50 |

Scope:
- Customer sees only their own complaints
- SupportAgent sees their assigned + unassigned
- Supervisor / Admin sees all

Returns `ComplaintListOut[]` — a lightweight projection.

### `GET /complaints/{id}`
Full complaint details including customer, agent, category, attachments, feedback.

### `PUT /complaints/{id}`
Update subject / description / category / priority. Customers can only edit while Open. Changing priority recomputes SLA.

### `DELETE /complaints/{id}` (Admin)
Hard delete with cascade.

### Workflow actions

#### `POST /complaints/{id}/assign` (Admin / Supervisor)
```json
{ "agent_id": 3 }
```
Status auto-transitions Open → Assigned.

#### `POST /complaints/{id}/status`
```json
{ "status": "In Progress", "comment": "Investigating..." }
```
Validates the state-machine transition. RBAC:
- Customer: only Resolved → Closed (confirm resolution)
- SupportAgent: must be the assignee
- Supervisor/Admin: any allowed transition

#### `POST /complaints/{id}/escalate` (Agent / Supervisor / Admin)
```json
{ "reason": "Customer is highly frustrated, requires manager attention" }
```

#### `POST /complaints/{id}/resolve` (Agent / Supervisor / Admin)
```json
{ "resolution_notes": "Replacement shipped, tracking TRK-99887" }
```

#### `POST /complaints/{id}/reopen`
```json
{ "reason": "Issue resurfaced after 2 days" }
```
Customer can reopen their own; others can reopen any. Resets SLA to a fresh window.

### `GET /complaints/{id}/history`
Full audit trail — every status change, assignment, comment, attachment upload, feedback submission.

### `POST /complaints/{id}/attachments`
multipart/form-data with field `file`. Max 10 MB. Returns `AttachmentOut`.

### `GET /complaints/{id}/attachments/{aid}/download`
Returns the file binary.

### `POST /complaints/{id}/feedback`
Only the complaint owner, only after Resolved/Closed, only once.
```json
{ "rating": 5, "comments": "Excellent service" }
```

---

## Notifications

### `GET /notifications`
Lists the current user's notifications (max 100, newest first).

Query param: `unread_only=true` to filter.

### `GET /notifications/unread-count`
Returns `{ "unread": 3 }`. Used by the navbar badge.

### `POST /notifications/{id}/read`
Marks a single notification as read.

### `POST /notifications/read-all`
Marks all current-user notifications as read.

---

## Dashboard & Analytics

### `GET /dashboard/stats`
Role-scoped totals.
```json
{
  "total_complaints": 8,
  "open": 2, "in_progress": 1, "pending_customer": 1,
  "escalated": 1, "resolved": 1, "closed": 1, "reopened": 0,
  "sla_breaches": 4,
  "avg_resolution_hours": 15.5
}
```

### `GET /dashboard/agent-performance` (Admin / Supervisor)
Per-agent counts of assigned/resolved/avg hours/SLA breaches.

### `GET /dashboard/category-breakdown`
Per-category complaint counts. Used for the dashboard pie chart.

### `GET /dashboard/trends?months=6`
Per-month total + resolved counts for the trailing N months.

### `GET /dashboard/customer-satisfaction` (Admin / Supervisor)
```json
{
  "average_rating": 4.5,
  "total_responses": 2,
  "distribution": { "5": 1, "4": 1 }
}
```

---

## Error Format

All errors are returned as:
```json
{ "detail": "Human-readable message" }
```

Validation errors from Pydantic return a structured 422:
```json
{ "detail": [ { "loc": ["body", "email"], "msg": "...", "type": "..." } ] }
```

## Quick Test Sequence (curl)

```bash
BASE=http://localhost:8000/api

# 1. Login as Customer
TOK=$(curl -s -X POST $BASE/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"customer1@example.com","password":"Customer@123"}' \
  | python -c "import sys,json;print(json.load(sys.stdin)['access_token'])")

# 2. Create a complaint
NEW=$(curl -s -X POST $BASE/complaints \
  -H "Authorization: Bearer $TOK" \
  -H "Content-Type: application/json" \
  -d '{"subject":"App freezes on launch","description":"Crashes immediately after splash.","category_id":4,"priority":"High"}')
echo "$NEW"

# 3. Login as Supervisor and assign to an agent
STOK=$(curl -s -X POST $BASE/auth/login -H "Content-Type: application/json" \
  -d '{"email":"supervisor@example.com","password":"Super@123"}' \
  | python -c "import sys,json;print(json.load(sys.stdin)['access_token'])")

CID=$(echo "$NEW" | python -c "import sys,json;print(json.load(sys.stdin)['id'])")
curl -X POST $BASE/complaints/$CID/assign \
  -H "Authorization: Bearer $STOK" -H "Content-Type: application/json" \
  -d '{"agent_id":3}'

# 4. Agent resolves it
ATOK=$(curl -s -X POST $BASE/auth/login -H "Content-Type: application/json" \
  -d '{"email":"agent1@example.com","password":"Agent@123"}' \
  | python -c "import sys,json;print(json.load(sys.stdin)['access_token'])")

curl -X POST $BASE/complaints/$CID/resolve \
  -H "Authorization: Bearer $ATOK" -H "Content-Type: application/json" \
  -d '{"resolution_notes":"Update pushed, please reinstall app."}'

# 5. Customer leaves feedback
curl -X POST $BASE/complaints/$CID/feedback \
  -H "Authorization: Bearer $TOK" -H "Content-Type: application/json" \
  -d '{"rating":5,"comments":"Fast fix, thanks!"}'
```
