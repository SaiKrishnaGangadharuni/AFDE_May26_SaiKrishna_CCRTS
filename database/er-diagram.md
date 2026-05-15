# Entity-Relationship Diagram

```mermaid
erDiagram
    ROLES ||--o{ USERS : "has"
    USERS ||--o{ COMPLAINTS : "files (customer)"
    USERS ||--o{ COMPLAINTS : "handles (agent)"
    USERS ||--o{ COMPLAINT_HISTORY : "performs"
    USERS ||--o{ NOTIFICATIONS : "receives"
    CATEGORIES ||--o{ COMPLAINTS : "classifies"
    COMPLAINTS ||--o{ COMPLAINT_HISTORY : "tracks"
    COMPLAINTS ||--o{ ATTACHMENTS : "has"
    COMPLAINTS ||--|| FEEDBACK : "rated by"
    COMPLAINTS ||--o{ NOTIFICATIONS : "triggers"

    ROLES {
        int id PK
        string name UK
        string description
    }
    USERS {
        int id PK
        string name
        string email UK
        string phone
        string password_hash
        int role_id FK
        boolean is_active
        datetime created_at
    }
    CATEGORIES {
        int id PK
        string name UK
        string description
        boolean is_active
    }
    COMPLAINTS {
        int id PK
        string complaint_number UK
        int customer_id FK
        int category_id FK
        int assigned_agent_id FK
        string subject
        text description
        enum priority
        enum status
        datetime sla_due_at
        boolean sla_breached
        text resolution_notes
        datetime resolved_at
        datetime closed_at
        datetime escalated_at
        string escalation_reason
        datetime created_at
        datetime updated_at
    }
    COMPLAINT_HISTORY {
        int id PK
        int complaint_id FK
        int updated_by FK
        enum old_status
        enum new_status
        string action
        text comment
        datetime updated_at
    }
    ATTACHMENTS {
        int id PK
        int complaint_id FK
        string file_name
        string stored_name
        string content_type
        int size_bytes
        int uploaded_by FK
        datetime uploaded_at
    }
    FEEDBACK {
        int id PK
        int complaint_id FK,UK
        int rating
        text comments
        datetime submitted_at
    }
    NOTIFICATIONS {
        int id PK
        int user_id FK
        int complaint_id FK
        string title
        text message
        boolean is_read
        datetime created_at
    }
```

## Status Workflow

```mermaid
stateDiagram-v2
    [*] --> Open: Customer registers
    Open --> Assigned: Supervisor/Admin assigns agent
    Open --> Escalated: Severe priority
    Assigned --> InProgress: Agent picks up
    Assigned --> Resolved: Quick fix
    InProgress --> PendingCustomer: Agent needs info
    InProgress --> Escalated: Cannot resolve
    InProgress --> Resolved: Fix applied
    PendingCustomer --> InProgress: Customer responds
    PendingCustomer --> Resolved: Confirmed
    Escalated --> InProgress: Supervisor reassigns
    Escalated --> Resolved: Resolved at higher tier
    Resolved --> Closed: Customer confirms
    Resolved --> Reopened: Customer not satisfied
    Closed --> Reopened: Re-emerging issue
    Reopened --> InProgress: Re-investigation
    Closed --> [*]
```

## SLA Rules

| Priority | Resolution Time |
|---|---|
| Low | 72 hours |
| Medium | 48 hours |
| High | 24 hours |
| Critical | 4 hours |

The `sla_due_at` column is computed at complaint creation as `created_at + SLA_HOURS[priority]`. The `sla_breached` flag is recomputed on every read so dashboards reflect the latest state without a background job.
