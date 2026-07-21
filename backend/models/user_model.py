"""
============================================================
ClipConnect - User Model
============================================================
Purpose:
    Defines the User database table using SQLAlchemy ORM.
    Each instance of this class represents one row in the 'users' table.

Database Table: users

Roles:
    - client  : Hires freelance editors for video projects
    - editor  : Freelance video editor offering services
    - admin   : Platform administrator with full access

Relationships (to be added in Week 2+):
    - One User (editor) -> Many Gig listings
    - One User (client) -> Many Orders
    - One User -> Many Reviews
============================================================
"""

from datetime import datetime, timezone
import enum

from database import db


# ============================================================
# Enum: UserRole
# ============================================================
class UserRole(enum.Enum):
    """
    Defines the three possible roles for a ClipConnect user.
    Using Python Enum ensures only valid values are stored.
    PostgreSQL will create a native ENUM type for this.
    """
    CLIENT = 'client'    # Clients hire editors
    EDITOR = 'editor'    # Editors offer services
    ADMIN = 'admin'      # Platform admins


# ============================================================
# Model: User
# ============================================================
class User(db.Model):
    """
    SQLAlchemy User Model
    =====================
    Maps to the 'users' table in PostgreSQL.
    
    This model handles:
        - User identity (name, email)
        - Authentication (hashed password)
        - Role-based access control
        - Profile management (profile image)
        - Timestamps (created_at, updated_at)
    """

    # PostgreSQL table name
    __tablename__ = 'users'

    # --------------------------------------------------------
    # Columns
    # --------------------------------------------------------

    id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True,
        comment='Unique identifier for each user'
    )

    full_name = db.Column(
        db.String(150),
        nullable=False,
        comment='User\'s full name (2 to 150 characters)'
    )

    email = db.Column(
        db.String(255),
        unique=True,
        nullable=False,
        index=True,     # Index for fast email lookups during login
        comment='Unique email address used for login'
    )

    password = db.Column(
        db.String(255),
        nullable=False,
        comment='bcrypt hashed password (never stored as plain text)'
    )

    role = db.Column(
        db.Enum(UserRole),
        nullable=False,
        default=UserRole.CLIENT,
        comment='User role: client, editor, or admin'
    )

    profile_image = db.Column(
        db.String(500),
        nullable=True,
        default=None,
        comment='URL or file path to the user\'s profile picture'
    )

    is_active = db.Column(
        db.Boolean,
        nullable=False,
        default=True,
        comment='Soft delete / account activation flag'
    )

    is_verified = db.Column(
        db.Boolean,
        nullable=False,
        default=False,
        comment='Email verification status (for future email verification feature)'
    )

    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        comment='Timestamp of account creation (UTC)'
    )

    updated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        comment='Timestamp of last profile update (UTC)'
    )

    # --------------------------------------------------------
    # Constructor
    # --------------------------------------------------------

    def __init__(self, full_name, email, password, role=UserRole.CLIENT, profile_image=None):
        """
        Initialize a new User instance.
        
        Args:
            full_name (str): User's full name
            email (str): User's email address
            password (str): ALREADY HASHED password (hash before passing in!)
            role (UserRole): User's role (default: CLIENT)
            profile_image (str): Optional URL to profile image
        """
        self.full_name = full_name
        self.email = email.lower().strip()  # Normalize email to lowercase
        self.password = password
        self.role = role
        self.profile_image = profile_image

    # --------------------------------------------------------
    # Instance Methods
    # --------------------------------------------------------

    def to_dict(self, include_sensitive=False):
        """
        Serialize User object to a Python dictionary.
        Used to convert User to JSON in API responses.
        
        Args:
            include_sensitive (bool): If True, includes fields like password.
                                      NEVER set to True in API responses!
        
        Returns:
            dict: User data safe for JSON serialization
        """
        user_dict = {
            'id': self.id,
            'full_name': self.full_name,
            'email': self.email,
            'role': self.role.value,     # Return 'client', 'editor', or 'admin'
            'profile_image': self.profile_image,
            'is_active': self.is_active,
            'is_verified': self.is_verified,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

        # Only include password hash if explicitly requested (for internal use)
        if include_sensitive:
            user_dict['password'] = self.password

        return user_dict

    def __repr__(self):
        """
        String representation for debugging.
        Example: <User id=1 email='john@example.com' role='client'>
        """
        return f"<User id={self.id} email='{self.email}' role='{self.role.value}'>"
