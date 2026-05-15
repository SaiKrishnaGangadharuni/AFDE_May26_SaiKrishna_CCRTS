"""Seed the database with roles, categories, sample users for each role,
and a handful of complaints in various states so the evaluator can immediately
explore every workflow path.

Run from the backend/ directory:
    python seed.py
"""
from datetime import datetime, timedelta
import random

from app.core.database import Base, engine, SessionLocal
from app.core.security import hash_password
from app.models import (
    Role, User, Category, Complaint, ComplaintHistory,
    Notification, Feedback, PriorityEnum, StatusEnum,
)
from app.services.complaint_service import compute_sla_due, generate_complaint_number


ROLES = [
    ("Admin", "Full system access"),
    ("Supervisor", "Monitors complaints & escalations"),
    ("SupportAgent", "Resolves assigned complaints"),
    ("Customer", "Registers and tracks complaints"),
]

CATEGORIES = [
    ("Billing Issues", "Disputes related to billing, invoices, or charges"),
    ("Service Disruption", "Outages or interruption of service"),
    ("Product Defects", "Damaged, defective, or non-functional product"),
    ("Technical Problems", "Software / connectivity / hardware issues"),
    ("Delivery Delays", "Shipment or delivery related issues"),
    ("Account Issues", "Login, password, profile or access problems"),
    ("Customer Service Complaints", "Issues with support quality / staff conduct"),
]

USERS = [
    # (name, email, password, role)
    ("System Admin", "admin@example.com", "Admin@123", "Admin"),
    ("Sara Supervisor", "supervisor@example.com", "Super@123", "Supervisor"),
    ("Alex Agent", "agent1@example.com", "Agent@123", "SupportAgent"),
    ("Bella Agent", "agent2@example.com", "Agent@123", "SupportAgent"),
    ("Chris Agent", "agent3@example.com", "Agent@123", "SupportAgent"),
    ("Carol Customer", "customer1@example.com", "Customer@123", "Customer"),
    ("Dan Customer", "customer2@example.com", "Customer@123", "Customer"),
    ("Eve Customer", "customer3@example.com", "Customer@123", "Customer"),
]


SAMPLE_COMPLAINTS = [
    {
        "subject": "Incorrect charge on my latest invoice",
        "description": "I was billed twice for the monthly subscription on April invoice. Please investigate and refund the duplicate amount.",
        "category": "Billing Issues",
        "priority": PriorityEnum.HIGH,
        "status": StatusEnum.IN_PROGRESS,
        "customer_email": "customer1@example.com",
        "agent_email": "agent1@example.com",
        "days_ago": 1,
    },
    {
        "subject": "Internet has been down since morning",
        "description": "Complete loss of connectivity since 8am. Router status lights look normal but no traffic flows.",
        "category": "Service Disruption",
        "priority": PriorityEnum.CRITICAL,
        "status": StatusEnum.ESCALATED,
        "customer_email": "customer2@example.com",
        "agent_email": "agent2@example.com",
        "days_ago": 0,
    },
    {
        "subject": "Received a damaged headset",
        "description": "The headset received yesterday has a broken left ear cup. Order #ORD-12345.",
        "category": "Product Defects",
        "priority": PriorityEnum.MEDIUM,
        "status": StatusEnum.RESOLVED,
        "customer_email": "customer1@example.com",
        "agent_email": "agent3@example.com",
        "days_ago": 5,
        "resolution_notes": "Replacement headset shipped via express courier. Tracking: TRK-99887.",
        "feedback": (5, "Very prompt resolution, thank you!"),
    },
    {
        "subject": "Cannot log into my online account",
        "description": "Password reset link is not arriving on my email. Tried three times.",
        "category": "Account Issues",
        "priority": PriorityEnum.MEDIUM,
        "status": StatusEnum.ASSIGNED,
        "customer_email": "customer3@example.com",
        "agent_email": "agent1@example.com",
        "days_ago": 2,
    },
    {
        "subject": "Package delayed by 5 days",
        "description": "Order placed 10 days ago, supposed to arrive by last week. Still in transit per tracking page.",
        "category": "Delivery Delays",
        "priority": PriorityEnum.LOW,
        "status": StatusEnum.PENDING_CUSTOMER,
        "customer_email": "customer2@example.com",
        "agent_email": "agent2@example.com",
        "days_ago": 3,
    },
    {
        "subject": "Mobile app crashes on launch (Android 14)",
        "description": "After the recent update, the app shows the splash screen and immediately closes. Device: Pixel 7, Android 14.",
        "category": "Technical Problems",
        "priority": PriorityEnum.HIGH,
        "status": StatusEnum.OPEN,
        "customer_email": "customer3@example.com",
        "agent_email": None,
        "days_ago": 0,
    },
    {
        "subject": "Rude behaviour from support agent over call",
        "description": "Yesterday's call with the support team was unprofessional. Please review the call recording for reference ID #CALL-7765.",
        "category": "Customer Service Complaints",
        "priority": PriorityEnum.MEDIUM,
        "status": StatusEnum.CLOSED,
        "customer_email": "customer1@example.com",
        "agent_email": "agent3@example.com",
        "days_ago": 10,
        "resolution_notes": "Apologies issued, training scheduled, account credited 1 month free.",
        "feedback": (4, "Apology accepted, glad you took the issue seriously."),
    },
    {
        "subject": "Late fee charged despite on-time payment",
        "description": "Payment was made on the 14th, due date was 15th, yet a late fee of $25 was added.",
        "category": "Billing Issues",
        "priority": PriorityEnum.MEDIUM,
        "status": StatusEnum.OPEN,
        "customer_email": "customer2@example.com",
        "agent_email": None,
        "days_ago": 0,
    },
]


def seed():
    print("Resetting schema...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # Roles ---------------------------------------------------------------
        print("Seeding roles...")
        roles_by_name: dict[str, Role] = {}
        for name, desc in ROLES:
            r = Role(name=name, description=desc)
            db.add(r); db.flush()
            roles_by_name[name] = r

        # Categories ----------------------------------------------------------
        print("Seeding categories...")
        categories_by_name: dict[str, Category] = {}
        for name, desc in CATEGORIES:
            c = Category(name=name, description=desc)
            db.add(c); db.flush()
            categories_by_name[name] = c

        # Users ---------------------------------------------------------------
        print("Seeding users...")
        users_by_email: dict[str, User] = {}
        for name, email, pwd, role_name in USERS:
            u = User(
                name=name, email=email, password_hash=hash_password(pwd),
                role_id=roles_by_name[role_name].id,
            )
            db.add(u); db.flush()
            users_by_email[email] = u

        # Complaints ----------------------------------------------------------
        print("Seeding complaints...")
        for spec in SAMPLE_COMPLAINTS:
            customer = users_by_email[spec["customer_email"]]
            agent = users_by_email[spec["agent_email"]] if spec.get("agent_email") else None
            cat = categories_by_name[spec["category"]]
            created_at = datetime.utcnow() - timedelta(days=spec.get("days_ago", 0),
                                                      hours=random.randint(0, 23))
            priority = spec["priority"]
            status = spec["status"]

            c = Complaint(
                complaint_number=generate_complaint_number(db),
                customer_id=customer.id,
                category_id=cat.id,
                assigned_agent_id=agent.id if agent else None,
                subject=spec["subject"],
                description=spec["description"],
                priority=priority,
                status=status,
                sla_due_at=compute_sla_due(priority, base=created_at),
                created_at=created_at,
                updated_at=created_at,
            )
            if status in (StatusEnum.RESOLVED, StatusEnum.CLOSED):
                c.resolution_notes = spec.get("resolution_notes")
                c.resolved_at = created_at + timedelta(hours=random.randint(2, 30))
                if status == StatusEnum.CLOSED:
                    c.closed_at = c.resolved_at + timedelta(hours=random.randint(2, 12))
            if status == StatusEnum.ESCALATED:
                c.escalated_at = created_at + timedelta(hours=random.randint(1, 4))
                c.escalation_reason = "SLA approaching, customer pressing for urgent fix"

            db.add(c); db.flush()

            # History entries
            db.add(ComplaintHistory(
                complaint_id=c.id, updated_by=customer.id, action="created",
                new_status=StatusEnum.OPEN, comment="Complaint registered",
                updated_at=created_at,
            ))
            if agent:
                db.add(ComplaintHistory(
                    complaint_id=c.id, updated_by=users_by_email["supervisor@example.com"].id,
                    action="assigned", old_status=StatusEnum.OPEN, new_status=StatusEnum.ASSIGNED,
                    comment=f"Assigned to {agent.name}",
                    updated_at=created_at + timedelta(hours=1),
                ))
            if status not in (StatusEnum.OPEN, StatusEnum.ASSIGNED):
                db.add(ComplaintHistory(
                    complaint_id=c.id, updated_by=(agent.id if agent else customer.id),
                    action="status_change", old_status=StatusEnum.ASSIGNED, new_status=status,
                    comment=f"Status moved to {status.value}",
                    updated_at=created_at + timedelta(hours=3),
                ))

            # Feedback
            if "feedback" in spec:
                rating, comments = spec["feedback"]
                db.add(Feedback(complaint_id=c.id, rating=rating, comments=comments))

            # Notification to customer
            db.add(Notification(
                user_id=customer.id, complaint_id=c.id,
                title=f"Complaint {c.complaint_number} registered",
                message=f"Your complaint '{c.subject}' was registered.",
                is_read=spec.get("days_ago", 0) > 2,
                created_at=created_at,
            ))

        db.commit()
        print("\n✓ Seed complete!\n")
        print("Demo accounts (all passwords end with @123):")
        for name, email, pwd, role in USERS:
            print(f"  • {role:<13} {email:<28} password: {pwd}")
        print()
    finally:
        db.close()


if __name__ == "__main__":
    seed()
