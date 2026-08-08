import sys
import os

# Add the backend directory to sys.path so we can import from it
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import create_app
from database import db
from models.user_model import User
from models.project_model import Project, ProjectStatus, BudgetType, ProjectPriority, ProjectVisibility
from models.editor_profile_model import EditorCategory
from datetime import datetime, timezone

app = create_app()

with app.app_context():
    # 1. Get client1 and editor1
    client = User.query.filter_by(email="client1@example.com").first()
    editor = User.query.filter_by(email="editor1@example.com").first()

    if not client or not editor:
        print("Could not find client1@example.com or editor1@example.com in DB.")
        sys.exit(1)

    # 2. Create an "Accepted" project
    proj_accepted = Project(
        client_id=client.id,
        hired_editor_id=editor.id,
        title="Test Project - ACCEPTED",
        category=EditorCategory.YOUTUBE,
        description="This project is already accepted by the editor.",
        budget=5000.0,
        budget_type=BudgetType.FIXED,
        required_skills=["Premiere Pro"],
        priority=ProjectPriority.MEDIUM,
        visibility=ProjectVisibility.PUBLIC,
        status=ProjectStatus.ACCEPTED
    )
    db.session.add(proj_accepted)

    # 3. Create an "Under Review" project
    proj_review = Project(
        client_id=client.id,
        hired_editor_id=editor.id,
        title="Test Project - UNDER REVIEW",
        category=EditorCategory.YOUTUBE,
        description="This project has been submitted and is waiting for your approval.",
        budget=8500.0,
        budget_type=BudgetType.FIXED,
        required_skills=["Premiere Pro"],
        priority=ProjectPriority.HIGH,
        visibility=ProjectVisibility.PUBLIC,
        status=ProjectStatus.UNDER_REVIEW,
        project_files=[{
            'filename': 'final_cut_v1.mp4',
            'url': '/uploads/project_submissions/dummy_file.mp4',
            'uploaded_by': editor.id,
            'notes': 'Here is the final cut as requested.',
            'created_at': datetime.now(timezone.utc).isoformat()
        }]
    )
    db.session.add(proj_review)

    # 4. Create a "Revision Requested" project
    proj_rev = Project(
        client_id=client.id,
        hired_editor_id=editor.id,
        title="Test Project - REVISION REQUESTED",
        category=EditorCategory.YOUTUBE,
        description="This project has a revision requested by the client.",
        budget=3200.0,
        budget_type=BudgetType.FIXED,
        required_skills=["Premiere Pro"],
        priority=ProjectPriority.LOW,
        visibility=ProjectVisibility.PUBLIC,
        status=ProjectStatus.REVISION_REQUESTED
    )
    db.session.add(proj_rev)

    db.session.commit()

    print("Successfully created test projects!")
