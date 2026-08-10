import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app
from database import db
from models.project_model import Project

with app.app_context():
    project = Project.query.get(102)
    print("DB raw:", db.session.execute(db.text(f"SELECT status FROM projects WHERE id=102")).scalar())
    print("Python object status:", project.status)
    if project.status:
        try:
            print("Python object name:", project.status.name)
            print("Python object value:", project.status.value)
        except:
            print("Not an enum")
    
    print("to_dict():", project.to_dict()['status'])
