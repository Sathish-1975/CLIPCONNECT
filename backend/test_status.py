import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app
from database import db
from models.project_model import Project, ProjectStatus

with app.app_context():
    project = Project.query.filter_by(title='pro').first()
    print("DB value (raw):", db.session.execute(db.text(f"SELECT status FROM projects WHERE id={project.id}")).scalar())
    print("Python object:", project.status)
    if project.status:
        print("Python object name:", project.status.name)
        print("Python object value:", project.status.value)
    
    print("to_dict():", project.to_dict()['status'])
