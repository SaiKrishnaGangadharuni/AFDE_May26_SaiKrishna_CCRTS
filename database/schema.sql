-- =============================================================================
-- CCRTS — Customer Complaint & Resolution Tracking System
-- Database Schema (SQLite dialect; PostgreSQL-compatible with minor tweaks)
-- =============================================================================
-- Mirrors the SQLAlchemy ORM in backend/app/models/models.py
-- Run on a fresh SQLite database:
--     sqlite3 ccrts.db < database/schema.sql
-- =============================================================================

PRAGMA foreign_keys = ON;

-- ------------------------------ ROLES ----------------------------------------
CREATE TABLE roles (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    name         VARCHAR(50)  NOT NULL UNIQUE,
    description  VARCHAR(255)
);

-- ------------------------------ USERS ----------------------------------------
CREATE TABLE users (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    name           VARCHAR(120) NOT NULL,
    email          VARCHAR(120) NOT NULL UNIQUE,
    phone          VARCHAR(20),
    password_hash  VARCHAR(255) NOT NULL,
    role_id        INTEGER NOT NULL REFERENCES roles(id),
    is_active      BOOLEAN  NOT NULL DEFAULT 1,
    created_at     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_users_email   ON users(email);
CREATE INDEX idx_users_role_id ON users(role_id);

-- ------------------------------ CATEGORIES -----------------------------------
CREATE TABLE categories (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    name         VARCHAR(120) NOT NULL UNIQUE,
    description  VARCHAR(255),
    is_active    BOOLEAN NOT NULL DEFAULT 1
);

-- ------------------------------ COMPLAINTS -----------------------------------
CREATE TABLE complaints (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    complaint_number    VARCHAR(40)  NOT NULL UNIQUE,
    customer_id         INTEGER      NOT NULL REFERENCES users(id),
    category_id         INTEGER      NOT NULL REFERENCES categories(id),
    assigned_agent_id   INTEGER REFERENCES users(id),
    subject             VARCHAR(200) NOT NULL,
    description         TEXT         NOT NULL,
    priority            VARCHAR(20)  NOT NULL DEFAULT 'Medium'
                          CHECK (priority IN ('Low','Medium','High','Critical')),
    status              VARCHAR(40)  NOT NULL DEFAULT 'Open'
                          CHECK (status IN ('Open','Assigned','In Progress',
                                            'Pending Customer Response','Escalated',
                                            'Resolved','Closed','Reopened')),
    sla_due_at          DATETIME NOT NULL,
    sla_breached        BOOLEAN  NOT NULL DEFAULT 0,
    resolution_notes    TEXT,
    resolved_at         DATETIME,
    closed_at           DATETIME,
    escalated_at        DATETIME,
    escalation_reason   VARCHAR(500),
    created_at          DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_complaints_status     ON complaints(status);
CREATE INDEX idx_complaints_priority   ON complaints(priority);
CREATE INDEX idx_complaints_customer   ON complaints(customer_id);
CREATE INDEX idx_complaints_agent      ON complaints(assigned_agent_id);
CREATE INDEX idx_complaints_created_at ON complaints(created_at);
CREATE INDEX idx_complaints_number     ON complaints(complaint_number);

-- ------------------------------ COMPLAINT_HISTORY ----------------------------
CREATE TABLE complaint_history (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    complaint_id   INTEGER NOT NULL REFERENCES complaints(id) ON DELETE CASCADE,
    updated_by     INTEGER NOT NULL REFERENCES users(id),
    old_status     VARCHAR(40),
    new_status     VARCHAR(40),
    action         VARCHAR(80) NOT NULL,    -- created, assigned, status_change, comment, resolved, escalated, reopened, attachment_uploaded, feedback_submitted
    comment        TEXT,
    updated_at     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_history_complaint  ON complaint_history(complaint_id);
CREATE INDEX idx_history_updated_at ON complaint_history(updated_at);

-- ------------------------------ ATTACHMENTS ----------------------------------
CREATE TABLE attachments (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    complaint_id   INTEGER NOT NULL REFERENCES complaints(id) ON DELETE CASCADE,
    file_name      VARCHAR(255) NOT NULL,
    stored_name    VARCHAR(255) NOT NULL,
    content_type   VARCHAR(100),
    size_bytes     INTEGER,
    uploaded_by    INTEGER REFERENCES users(id),
    uploaded_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_attachments_complaint ON attachments(complaint_id);

-- ------------------------------ FEEDBACK -------------------------------------
CREATE TABLE feedback (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    complaint_id   INTEGER NOT NULL UNIQUE REFERENCES complaints(id) ON DELETE CASCADE,
    rating         INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
    comments       TEXT,
    submitted_at   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ------------------------------ NOTIFICATIONS --------------------------------
CREATE TABLE notifications (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id        INTEGER NOT NULL REFERENCES users(id),
    complaint_id   INTEGER REFERENCES complaints(id) ON DELETE SET NULL,
    title          VARCHAR(200) NOT NULL,
    message        TEXT NOT NULL,
    is_read        BOOLEAN  NOT NULL DEFAULT 0,
    created_at     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_notifications_user    ON notifications(user_id);
CREATE INDEX idx_notifications_unread  ON notifications(is_read);
CREATE INDEX idx_notifications_created ON notifications(created_at);

-- =============================================================================
-- End of schema.
-- =============================================================================
