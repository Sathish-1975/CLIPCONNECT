import os
import sys
import sqlite3

db_path = os.path.join(os.path.dirname(__file__), 'instance', 'clipconnect.db')

conn = sqlite3.connect(db_path)
cur = conn.cursor()

cur.execute("SELECT id, title, status, payment_status FROM projects ORDER BY id DESC LIMIT 5")
projects = cur.fetchall()

for p in projects:
    print(p)
