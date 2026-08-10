import os
import sys
import sqlite3

db_path = os.path.join(os.path.dirname(__file__), 'instance', 'clipconnect.db')

conn = sqlite3.connect(db_path)
cur = conn.cursor()

cur.execute("SELECT id FROM users WHERE role='EDITOR'")
editors = cur.fetchall()

editor_ids = [str(e[0]) for e in editors]

if editor_ids:
    ids_str = ",".join(editor_ids)
    print(f"Deleting {len(editor_ids)} default editors (IDs: {ids_str})...")

    # Delete related records to respect foreign keys
    cur.execute(f"DELETE FROM profile_views WHERE editor_id IN ({ids_str})")
    cur.execute(f"DELETE FROM portfolio_views WHERE editor_id IN ({ids_str})")
    cur.execute(f"DELETE FROM portfolio_likes WHERE editor_id IN ({ids_str})")
    cur.execute(f"DELETE FROM saved_projects WHERE editor_id IN ({ids_str})")
    cur.execute(f"DELETE FROM proposals WHERE editor_id IN ({ids_str})")
    cur.execute(f"DELETE FROM reviews WHERE editor_id IN ({ids_str})")
    cur.execute(f"DELETE FROM revision_requests WHERE editor_id IN ({ids_str})")
    cur.execute(f"DELETE FROM editor_profiles WHERE user_id IN ({ids_str})")
    
    # Also remove from projects if hired
    cur.execute(f"UPDATE projects SET hired_editor_id = NULL WHERE hired_editor_id IN ({ids_str})")
    
    # Finally, delete the users
    cur.execute(f"DELETE FROM users WHERE id IN ({ids_str})")
    
    conn.commit()
    print("Default editors and their related data successfully deleted.")
else:
    print("No default editors found to delete.")

conn.close()
