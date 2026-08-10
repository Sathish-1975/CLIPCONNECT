import os
import sys
from dotenv import load_dotenv
import psycopg2

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
load_dotenv()

def update_schema():
    username = os.environ.get('DB_USERNAME', 'postgres')
    password = os.environ.get('DB_PASSWORD', '')
    host     = os.environ.get('DB_HOST', 'localhost')
    port     = os.environ.get('DB_PORT', '5432')
    db_name  = os.environ.get('DB_NAME', 'clipconnect')

    try:
        conn = psycopg2.connect(
            host=host,
            port=int(port),
            user=username,
            password=password,
            dbname=db_name
        )
        conn.autocommit = True
        cur = conn.cursor()

        # Add payment_status to projects
        try:
            cur.execute("ALTER TABLE projects ADD COLUMN payment_status VARCHAR(50) NOT NULL DEFAULT 'pending'")
            print("[OK] Added payment_status to projects")
        except psycopg2.errors.DuplicateColumn:
            print("[INFO] payment_status already exists on projects")

        # Add paid_at to payments
        try:
            cur.execute("ALTER TABLE payments ADD COLUMN paid_at TIMESTAMP WITH TIME ZONE")
            print("[OK] Added paid_at to payments")
        except psycopg2.errors.DuplicateColumn:
            print("[INFO] paid_at already exists on payments")

        cur.close()
        conn.close()
        print("Schema update complete.")

    except Exception as e:
        print(f"[ERROR] {e}")

if __name__ == '__main__':
    update_schema()
