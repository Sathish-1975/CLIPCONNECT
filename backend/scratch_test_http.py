import urllib.request
import json
import sqlite3

def get_token():
    conn = sqlite3.connect('instance/clipconnect.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, email, full_name, role FROM users WHERE role='client' LIMIT 1")
    client = cursor.fetchone()
    if not client:
        return None
        
    # Let's just login
    req = urllib.request.Request('http://localhost:5000/api/auth/login', 
        data=json.dumps({'email': client[1], 'password': 'password123'}).encode('utf-8'),
        headers={'Content-Type': 'application/json'})
    
    try:
        response = urllib.request.urlopen(req)
        data = json.loads(response.read().decode('utf-8'))
        return data['data']['token'], client[0]
    except Exception as e:
        print(f"Login failed: {e}")
        return None, None

def get_editor():
    conn = sqlite3.connect('instance/clipconnect.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE role='editor' LIMIT 1")
    editor = cursor.fetchone()
    return editor[0] if editor else None

def get_project(client_id):
    conn = sqlite3.connect('instance/clipconnect.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM projects WHERE client_id=? LIMIT 1", (client_id,))
    project = cursor.fetchone()
    return project[0] if project else None

token, client_id = get_token()
if not token:
    print("Could not get token")
    exit(1)

editor_id = get_editor()
project_id = get_project(client_id)

print(f"Token: {token[:20]}...")
print(f"Client: {client_id}, Editor: {editor_id}, Project: {project_id}")

req = urllib.request.Request('http://localhost:5000/api/hire',
    data=json.dumps({
        'project_id': project_id,
        'editor_id': editor_id,
        'message': 'Test hire'
    }).encode('utf-8'),
    headers={
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}'
    }
)

try:
    response = urllib.request.urlopen(req)
    print(response.read().decode('utf-8'))
except urllib.error.HTTPError as e:
    print(f"Error {e.code}: {e.read().decode('utf-8')}")

