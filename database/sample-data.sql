-- =============================================================================
-- CCRTS — Sample seed data (run after schema.sql)
-- Passwords are bcrypt-hashed using the value shown next to each user.
-- For convenience, prefer running `python backend/seed.py` instead — it inserts
-- everything below plus generates realistic SLA timestamps and history entries.
-- =============================================================================

-- Roles ------------------------------------------------------------------------
INSERT INTO roles (name, description) VALUES
  ('Admin',        'Full system access'),
  ('Supervisor',   'Monitors complaints & escalations'),
  ('SupportAgent', 'Resolves assigned complaints'),
  ('Customer',     'Registers and tracks complaints');

-- Categories ------------------------------------------------------------------
INSERT INTO categories (name, description) VALUES
  ('Billing Issues',               'Disputes related to billing, invoices, or charges'),
  ('Service Disruption',           'Outages or interruption of service'),
  ('Product Defects',              'Damaged, defective, or non-functional product'),
  ('Technical Problems',           'Software / connectivity / hardware issues'),
  ('Delivery Delays',              'Shipment or delivery related issues'),
  ('Account Issues',               'Login, password, profile or access problems'),
  ('Customer Service Complaints',  'Issues with support quality / staff conduct');

-- NOTE: Inserting users via raw SQL requires bcrypt-hashed passwords.
-- Use `python backend/seed.py` to seed users + sample complaints with
-- properly hashed passwords. The seed script is the authoritative source.

-- =============================================================================
-- End of sample data
-- =============================================================================
