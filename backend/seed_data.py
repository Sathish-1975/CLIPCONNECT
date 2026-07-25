"""
============================================================
ClipConnect - Test Seed Script
============================================================
Populates the database with sample users (Client, Editor, Admin),
editor profile, projects, messages, and escrow payments for testing.
============================================================
"""

import sys
import os
import bcrypt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from database import db
from models import (
    User, UserRole, EditorProfile, EditorCategory, ClientProfile,
    Project, BudgetType, ProjectVisibility, ProjectPriority, ProjectStatus,
    Message, Payment, Transaction, Invoice, UserSettings
)

app = create_app()

def hash_pass(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def seed_database():
    with app.app_context():
        print("[START] Seeding database with test data...")
        db.create_all()

        # 1. Admin User
        admin = User.query.filter_by(email="admin@clipconnect.com").first()
        if not admin:
            admin = User(
                full_name="Admin Director",
                email="admin@clipconnect.com",
                password=hash_pass("Admin@123456"),
                role=UserRole.ADMIN
            )
            admin.is_active = True
            admin.is_verified = True
            db.session.add(admin)

        # 2. Client User
        client = User.query.filter_by(email="client@example.com").first()
        if not client:
            client = User(
                full_name="Sarah Client",
                email="client@example.com",
                password=hash_pass("Client@123456"),
                role=UserRole.CLIENT
            )
            client.is_active = True
            client.is_verified = True
            db.session.add(client)
            db.session.flush()

            cp = ClientProfile(
                user_id=client.id,
                company_name="Creative Studios",
                industry="Content Creation"
            )
            db.session.add(cp)

        # 3. Editor User
        editor = User.query.filter_by(email="editor@example.com").first()
        if not editor:
            editor = User(
                full_name="Alex Editor",
                email="editor@example.com",
                password=hash_pass("Editor@123456"),
                role=UserRole.EDITOR
            )
            editor.is_active = True
            editor.is_verified = True
            db.session.add(editor)
            db.session.flush()

            ep = EditorProfile(
                user_id=editor.id,
                username="alexedits",
                tagline="Professional Video Editor & Motion Designer",
                bio="10+ years creating viral YouTube videos and cinematic trailers.",
                category="youtube",
                experience_years=5,
                skills=["Premiere Pro", "After Effects", "DaVinci Resolve", "Color Grading"],
                software_used=["Premiere Pro", "After Effects"],
                hourly_rate=1200.0,
                fixed_price_from=5000.0,
                fixed_price_to=50000.0,
                availability_status="available",
                avg_rating=4.9,
                total_reviews=18,
                completed_projects=15
            )
            db.session.add(ep)

        db.session.commit()

        # Fetch IDs
        client = User.query.filter_by(email="client@example.com").first()
        editor = User.query.filter_by(email="editor@example.com").first()

        # 4. Create Sample Project
        proj = Project.query.filter_by(client_id=client.id).first()
        if not proj:
            proj = Project(
                client_id=client.id,
                title="YouTube Tech Review Video Editing",
                category=EditorCategory.YOUTUBE,
                description="Need a sleek, fast-paced video editor to edit a 10-minute 4K tech review video with motion graphics and sound design.",
                budget=8500.0,
                budget_type=BudgetType.FIXED,
                required_skills=["Premiere Pro", "Motion Graphics"],
                editing_software=["Premiere Pro"],
                experience_required="Intermediate",
                priority=ProjectPriority.HIGH,
                visibility=ProjectVisibility.PUBLIC,
                status=ProjectStatus.PUBLISHED
            )
            db.session.add(proj)
            db.session.commit()

        # 5. Create Sample Chat Message
        msg = Message.query.filter_by(sender_id=client.id, receiver_id=editor.id).first()
        if not msg:
            msg = Message(
                sender_id=client.id,
                receiver_id=editor.id,
                project_id=proj.id,
                content="Hi Alex! I saw your portfolio and would love to hire you for my tech review video project.",
                message_type="text"
            )
            db.session.add(msg)
            db.session.commit()

        # 6. Create Sample Payment Transaction
        pay = Payment.query.filter_by(client_id=client.id).first()
        if not pay:
            pay = Payment(
                project_id=proj.id,
                client_id=client.id,
                editor_id=editor.id,
                amount=8500.0,
                currency="INR",
                razorpay_order_id="order_test_12345",
                status="escrow_held"
            )
            db.session.add(pay)
            db.session.commit()

        print("\n" + "="*60)
        print("  [OK] Database Seeding Successfully Completed!")
        print("="*60)
        print("  [KEYS] Test User Accounts:")
        print("     1. Admin:  email: admin@clipconnect.com  | pass: Admin@123456")
        print("     2. Client: email: client@example.com     | pass: Client@123456")
        print("     3. Editor: email: editor@example.com     | pass: Editor@123456")
        print("="*60 + "\n")

if __name__ == '__main__':
    seed_database()
