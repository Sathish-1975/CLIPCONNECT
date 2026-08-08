import sqlite3
import json

conn = sqlite3.connect('instance/clipconnect.db')
cursor = conn.cursor()

# Get schema of projects table
cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='projects'")
schema = cursor.fetchone()[0]

print("Projects Table Schema:")
print(schema)

conn.close()
