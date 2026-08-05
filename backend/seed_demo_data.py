"""
============================================================
ClipConnect - Demo Data Seeder
============================================================
Why this file exists:
  Provides a robust data seeding script to generate a massive amount of dummy data
  for testing the platform's performance, dashboards, and workflows.

What it does:
  - Clears existing data (WARNING!)
  - Generates 1 Admin, 20 Clients, 30 Editors
  - Generates Editor profiles, skills, portfolios
  - Generates 100 Projects in various statuses
  - Generates Proposals, Payments, and Transactions
============================================================
"""

import sys
import os
import random
from datetime import datetime, timedelta, timezone

# Add the parent directory to the path so we can import app modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app
from database import db
from models.user_model import User, UserRole
from models.client_profile_model import ClientProfile
from models.editor_profile_model import EditorProfile, EditorCategory, AvailabilityStatus
from models.project_model import Project, ProjectStatus
from models.proposal_model import Proposal
from models.payment_model import Payment, Transaction
from models.analytics_model import ProfileView
from models.review_model import Review

import bcrypt

def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(rounds=12)).decode('utf-8')

def run_seeder():
    with app.app_context():
        # Drop all existing data
        print("Dropping existing tables...")
        db.drop_all()
        print("Creating fresh tables...")
        db.create_all()

        print("Creating users (Admin, Clients, Editors)...")
        
        # Admin
        admin = User(full_name="System Admin", email="admin@clipconnect.com", password=hash_password('password'), role=UserRole.ADMIN)
        db.session.add(admin)

        # Clients (20)
        clients = []
        for i in range(1, 21):
            c = User(full_name=f"Client {i}", email=f"client{i}@example.com", password=hash_password('password'), role=UserRole.CLIENT)
            db.session.add(c)
            clients.append(c)
        
        # Editors (30)
        editors = []
        categories = list(EditorCategory)
        availabilities = list(AvailabilityStatus)
        
        for i in range(1, 31):
            e = User(full_name=f"Editor {i}", email=f"editor{i}@example.com", password=hash_password('password'), role=UserRole.EDITOR)
            db.session.add(e)
            editors.append(e)

        db.session.commit()

        # Profiles
        print("Creating profiles...")
        for c in clients:
            cp = ClientProfile(user_id=c.id, company_name=f"Company {c.id}", website=f"https://company{c.id}.com")
            db.session.add(cp)
        
        for e in editors:
            ep = EditorProfile(
                user_id=e.id,
                username=f"editor_{e.id}",
                tagline=f"Pro Video Editor {e.id}",
                category=random.choice(categories),
                hourly_rate=random.randint(20, 150),
                experience_years=random.randint(1, 15),
                availability=random.choice(availabilities),
                is_verified=random.choice([True, False, True]), # 2/3 chance to be verified
                skills=['Premiere Pro', 'After Effects', 'Color Grading'][:random.randint(1,3)]
            )
            db.session.add(ep)
        
        db.session.commit()

        # Projects (100)
        print("Creating 100 projects in various statuses...")
        statuses = list(ProjectStatus)
        projects = []
        for i in range(1, 101):
            client = random.choice(clients)
            status = random.choice(statuses)
            budget = random.randint(500, 5000)
            
            p = Project(
                client_id=client.id,
                title=f"Awesome Video Project #{i}",
                description=f"This is a dummy project description for project {i}.",
                budget=budget,
                category=EditorCategory.YOUTUBE,
                status=status
            )
            
            # If status implies it has an editor, assign one
            if status in [ProjectStatus.IN_PROGRESS, ProjectStatus.UNDER_REVIEW, ProjectStatus.REVISION_REQUESTED, ProjectStatus.COMPLETED]:
                p.hired_editor_id = random.choice(editors).id
                
            db.session.add(p)
            projects.append(p)
        
        db.session.commit()

        # Proposals
        print("Creating proposals...")
        for p in projects:
            if p.status == ProjectStatus.PUBLISHED:
                # Add some pending proposals
                for _ in range(random.randint(1, 5)):
                    prop = Proposal(
                        project_id=p.id,
                        editor_id=random.choice(editors).id,
                        cover_letter="I can do this!",
                        proposed_price=float(p.budget) * random.uniform(0.8, 1.2),
                        status='pending'
                    )
                    db.session.add(prop)
            elif p.hired_editor_id:
                # Create the accepted proposal
                prop = Proposal(
                    project_id=p.id,
                    editor_id=p.hired_editor_id,
                    cover_letter="I am the hired editor.",
                    proposed_price=float(p.budget),
                    status='accepted'
                )
                db.session.add(prop)
        
        db.session.commit()

        # Payments & Transactions
        print("Generating financial records...")
        for p in projects:
            if p.status == ProjectStatus.COMPLETED and p.hired_editor_id:
                amount = float(p.budget)
                editor_earnings = amount * 0.90 # 10% commission
                
                pay = Payment(
                    project_id=p.id,
                    client_id=p.client_id,
                    editor_id=p.hired_editor_id,
                    amount=amount,
                    status='released',
                    created_at=datetime.now(timezone.utc) - timedelta(days=random.randint(1, 60))
                )
                db.session.add(pay)
                db.session.flush()

                # Deposit
                tx_dep = Transaction(payment_id=pay.id, type='deposit', amount=amount, status='success')
                db.session.add(tx_dep)
                
                # Payout
                tx_pay = Transaction(payment_id=pay.id, type='payout', amount=editor_earnings, status='success')
                db.session.add(tx_pay)
                
                # Review
                r = Review(
                    project_id=p.id,
                    reviewer_id=p.client_id,
                    editor_id=p.hired_editor_id,
                    overall_rating=random.randint(3, 5),
                    comment="Great work!"
                )
                db.session.add(r)
                
        db.session.commit()
        
        print("Seeding complete! Admin email: admin@clipconnect.com | Password: password")

if __name__ == '__main__':
    run_seeder()
