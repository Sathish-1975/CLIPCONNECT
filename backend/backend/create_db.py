# -*- coding: utf-8 -*-
"""
============================================================
ClipConnect - Create PostgreSQL Database Script
============================================================
Purpose:
    Creates the 'clipconnect' PostgreSQL database using
    credentials from the .env file.

    This script connects to the default 'postgres' database
    first (which always exists), then creates 'clipconnect'.

Usage:
    cd backend
    python create_db.py

Requirements:
    - PostgreSQL must be running
    - Update DB_USERNAME and DB_PASSWORD in .env
============================================================
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

import psycopg2
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def create_database():
    username    = os.environ.get('DB_USERNAME', 'postgres')
    password    = os.environ.get('DB_PASSWORD', '')
    host        = os.environ.get('DB_HOST', 'localhost')
    port        = os.environ.get('DB_PORT', '5432')
    db_name     = os.environ.get('DB_NAME', 'clipconnect')

    print("\n" + "="*55)
    print("  ClipConnect - Database Creator")
    print("="*55)
    print(f"\n  Host     : {host}:{port}")
    print(f"  Username : {username}")
    print(f"  Database : {db_name}")
    print()

    # Step 1: Connect to default 'postgres' database
    try:
        conn = psycopg2.connect(
            host=host,
            port=int(port),
            user=username,
            password=password,
            dbname='postgres'   # Connect to default DB first
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()
        print("  [OK] Connected to PostgreSQL server!")
    except psycopg2.OperationalError as e:
        print(f"  [ERROR] Connection failed: {e}")
        print("\n  Troubleshooting:")
        print("  1. Make sure PostgreSQL is running")
        print("  2. Update DB_PASSWORD in backend/.env")
        print("  3. Make sure the user exists")
        sys.exit(1)

    # Step 2: Check if database already exists
    cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db_name,))
    exists = cur.fetchone()

    if exists:
        print(f"  [INFO] Database '{db_name}' already exists -- skipping creation.")
    else:
        # Step 3: Create the database
        cur.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(db_name)))
        print(f"  [OK] Database '{db_name}' created successfully!")

    cur.close()
    conn.close()

    print("\n" + "="*55)
    print("  [DONE] Next step: python app.py")
    print("="*55 + "\n")


if __name__ == '__main__':
    create_database()

