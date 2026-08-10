import os
import sys
import sqlite3
import json

db_path = os.path.join(os.path.dirname(__file__), 'instance', 'clipconnect.db')

conn = sqlite3.connect(db_path)
cur = conn.cursor()

cur.execute("SELECT id, title, status FROM projects ORDER BY id DESC LIMIT 5")
projects = cur.fetchall()

print("Recent projects from DB:")
for p in projects:
    print(f"ID: {p[0]}, Title: '{p[1]}', Status: '{p[2]}'")
