import os
import sys

# Add backend directory to sys.path
sys.path.append(os.path.abspath('backend'))

from backend.app import create_app
from backend.database import db
from backend.models.user_model import User, UserRole
from backend.models.project_model import Project, ProjectStatus
from backend.utils.jwt_helper import generate_token
import json

app = create_app()

with app.app_context():
    # 1. get a client user
    client = User.query.filter_by(role=UserRole.CLIENT).first()
    if not client:
        print("No client found")
        sys.exit(0)
    
    # 2. get an editor user
    editor = User.query.filter_by(role=UserRole.EDITOR).first()
    if not editor:
        print("No editor found")
        sys.exit(0)
    
    # 3. get a project belonging to client
    project = Project.query.filter_by(client_id=client.id).first()
    if not project:
        print("No project found for client")
        sys.exit(0)

    # 4. generate token for client
    token = generate_token(client)
    
    # 5. create test client
    with app.test_client() as c:
        response = c.post('/api/hire', json={
            'project_id': project.id,
            'editor_id': editor.id,
            'message': 'Test hire'
        }, headers={'Authorization': f'Bearer {token}'})
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json}")
