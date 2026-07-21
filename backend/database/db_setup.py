"""
============================================================
ClipConnect - Database Setup Script
============================================================
Purpose:
    Standalone script to:
    1. Create all database tables from SQLAlchemy models
    2. Seed an initial admin user (optional)

When to use:
    - First-time setup on a fresh database
    - After adding new models (before using Flask-Migrate)
    - In CI/CD pipelines for database initialization

Usage:
    cd backend
    python database/db_setup.py

    Or with seed admin:
    python database/db_setup.py --seed
============================================================
"""

import sys
import os

# Add the backend directory to Python path so we can import our modules
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

import bcrypt
from dotenv import load_dotenv

# Load environment variables
load_dotenv(os.path.join(backend_dir, '.env'))


def create_tables():
    """
    Create all database tables defined in SQLAlchemy models.
    Safe to run multiple times — skips existing tables.
    """
    from app import create_app
    from database import db
    from models.user_model import User  # noqa: F401 — must import to register model

    print("\n" + "="*55)
    print("  🎬 ClipConnect — Database Setup")
    print("="*55)

    app = create_app()

    with app.app_context():
        print("\n📦 Connecting to database...")
        db_url = app.config.get('SQLALCHEMY_DATABASE_URI', 'N/A')
        # Mask password in output for security
        if '@' in db_url:
            parts = db_url.split('@')
            masked = parts[0].split(':')
            masked_url = f"{masked[0]}:****@{'@'.join(parts[1:])}"
        else:
            masked_url = db_url

        print(f"   URL: {masked_url}")

        try:
            # Test connection
            db.session.execute(db.text('SELECT 1'))
            print("   ✅ Connected successfully!\n")
        except Exception as e:
            print(f"   ❌ Connection FAILED: {str(e)}")
            print("\n   👉 Check your DATABASE_URL in backend/.env")
            print("   👉 Make sure PostgreSQL is running")
            print("   👉 Make sure the 'clipconnect' database exists")
            print("\n   Run this SQL to create the database:")
            print("   psql -U postgres -c \"CREATE DATABASE clipconnect;\"")
            sys.exit(1)

        print("🏗️  Creating database tables...")
        db.create_all()
        print("   ✅ Tables created (or already existed):\n")

        # List created tables
        inspector = db.inspect(db.engine)
        tables = inspector.get_table_names()
        for table in tables:
            print(f"   📋 {table}")

        return app, db


def seed_admin_user(app, db):
    """
    Create a default admin user for testing.
    Skips if admin already exists.
    """
    from models.user_model import User, UserRole

    print("\n🌱 Seeding admin user...")

    with app.app_context():
        admin_email = 'admin@clipconnect.com'
        existing = User.query.filter_by(email=admin_email).first()

        if existing:
            print(f"   ⏭️  Admin already exists: {admin_email}")
            return

        # Hash admin password
        admin_password = 'AdminPass@123'
        hashed = bcrypt.hashpw(
            admin_password.encode('utf-8'),
            bcrypt.gensalt(rounds=12)
        ).decode('utf-8')

        admin = User(
            full_name='ClipConnect Admin',
            email=admin_email,
            password=hashed,
            role=UserRole.ADMIN
        )
        admin.is_verified = True

        db.session.add(admin)
        db.session.commit()

        print(f"   ✅ Admin user created:")
        print(f"      Email   : {admin_email}")
        print(f"      Password: {admin_password}")
        print(f"      Role    : admin")
        print(f"   ⚠️  Change this password before deploying to production!")

    # Also seed a test client and editor
    with app.app_context():
        test_users = [
            {
                'full_name': 'Test Client',
                'email': 'client@test.com',
                'password': 'Client@123',
                'role': UserRole.CLIENT
            },
            {
                'full_name': 'Test Editor',
                'email': 'editor@test.com',
                'password': 'Editor@123',
                'role': UserRole.EDITOR
            }
        ]

        print("\n🌱 Seeding test users...")
        for u in test_users:
            if User.query.filter_by(email=u['email']).first():
                print(f"   ⏭️  User already exists: {u['email']}")
                continue

            hashed = bcrypt.hashpw(
                u['password'].encode('utf-8'),
                bcrypt.gensalt(rounds=12)
            ).decode('utf-8')

            user = User(
                full_name=u['full_name'],
                email=u['email'],
                password=hashed,
                role=u['role']
            )
            db.session.add(user)
            print(f"   ✅ Created: {u['email']} ({u['role'].value}) | Pass: {u['password']}")

        db.session.commit()


def print_summary():
    print("\n" + "="*55)
    print("  ✅ Database setup complete!")
    print("="*55)
    print("\n🚀 Next steps:")
    print("   1. Run: python app.py")
    print("   2. Open: http://localhost:5000/api/health")
    print("   3. Open: frontend/index.html in browser")
    print("\n📡 API Endpoints ready:")
    print("   POST  /api/auth/register")
    print("   POST  /api/auth/login")
    print("   GET   /api/auth/me  (requires Bearer token)")
    print("="*55 + "\n")


if __name__ == '__main__':
    # Check if --seed flag was passed
    should_seed = '--seed' in sys.argv

    app, db = create_tables()

    if should_seed:
        seed_admin_user(app, db)

    print_summary()
