import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend'))

from app import app
from controllers.admin_controller import get_admin_dashboard_stats

with app.app_context():
    # Simulate current_user dict for admin
    current_user = {'user_id': 1, 'role': 'admin'}
    try:
        response, status_code = get_admin_dashboard_stats(current_user)
        print(f"Status Code: {status_code}")
        print(response)
    except Exception as e:
        print(f"Exception: {e}")
