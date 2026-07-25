"""
============================================================
ClipConnect - Models Package Initialization
============================================================
Registers ALL SQLAlchemy models so db.create_all() creates
every table. Import order matters for FK resolution.
============================================================
"""

# Week 1
from models.user_model import User, UserRole

# Week 2
from models.editor_profile_model import EditorProfile, EditorCategory, AvailabilityStatus
from models.client_profile_model import ClientProfile

# Week 3 & 4 Models
from models.project_model import Project, BudgetType, ProjectVisibility, ProjectPriority, ProjectStatus
from models.proposal_model import Proposal
from models.saved_project_model import SavedProject
from models.notification_model import Notification
from models.review_model import Review
from models.revision_model import RevisionRequest
from models.message_model import Message, MessageAttachment
from models.payment_model import Payment, Transaction, Invoice
from models.analytics_model import ProfileView, PortfolioView, PortfolioLike
from models.user_settings_model import UserSettings
from models.email_log_model import EmailLog

__all__ = [
    'User',
    'EditorProfile', 'EditorCategory', 'AvailabilityStatus',
    'ClientProfile',
    'Project', 'BudgetType', 'ProjectVisibility', 'ProjectPriority', 'ProjectStatus',
    'Proposal',
    'SavedProject',
    'Notification',
    'Review',
    'RevisionRequest',
    'Message', 'MessageAttachment',
    'Payment', 'Transaction', 'Invoice',
    'ProfileView', 'PortfolioView', 'PortfolioLike',
    'UserSettings',
    'EmailLog',
]

