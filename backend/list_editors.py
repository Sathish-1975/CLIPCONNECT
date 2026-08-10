import os
import sys
import sqlite3

db_path = os.path.join(os.path.dirname(__file__), 'instance', 'clipconnect.db')

conn = sqlite3.connect(db_path)
cur = conn.cursor()

cur.execute("SELECT id, email, role FROM users")
users = cur.fetchall()

for u in users:
    print(u)
