import os
import sys

# Add the parent directory to the path so we can import app modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app
from database import db
from models.user_model import User, UserRole
from models.editor_profile_model import EditorProfile, EditorCategory, AvailabilityStatus

def complete_profile():
    with app.app_context():
        user = User.query.filter_by(email="sam474@gmail.com").first()
        if not user:
            print("User sam474@gmail.com not found!")
            return
            
        if user.role != UserRole.EDITOR:
            print("User is not an editor!")
            return

        profile = EditorProfile.query.filter_by(user_id=user.id).first()
        if not profile:
            profile = EditorProfile(user_id=user.id)
            db.session.add(profile)
            
        profile.username = "sathish_edits"
        profile.tagline = "Professional Video Editor & Motion Graphics Artist"
        profile.bio = "Hi! I am Sathish, a highly skilled video editor with 5+ years of experience in Premiere Pro and After Effects. I specialize in YouTube content, commercial edits, and engaging reels."
        profile.category = EditorCategory.YOUTUBE
        profile.experience_years = 5
        profile.skills = ["Premiere Pro", "After Effects", "Color Grading", "Sound Design"]
        profile.software_used = ["Premiere Pro", "After Effects", "DaVinci Resolve"]
        profile.city = "Chennai"
        profile.country = "India"
        profile.hourly_rate = 30.00
        profile.availability_status = AvailabilityStatus.AVAILABLE
        profile.is_verified = True
        profile.is_featured = True
        
        # Adding some dummy portfolio links just to make the profile look good
        profile.portfolio_videos = [
            {"title": "Awesome YouTube Vlog", "url": "https://youtube.com/watch?v=demo1"},
            {"title": "Corporate Promo", "url": "https://vimeo.com/demo2"}
        ]

        db.session.commit()
        print(f"Profile for {user.full_name} ({user.email}) successfully completed!")

if __name__ == '__main__':
    complete_profile()
