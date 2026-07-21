"""
============================================================
ClipConnect - Editor Profile Model
============================================================
Table: editor_profiles
Relationship: One-to-One with users (editor role only)

Fields (all Week 2 requirements):
  Identity   : username, bio, tagline, profile_photo, cover_banner
  Professional: category, experience_years, skills, software_used, languages
  Location   : city, country
  Pricing    : hourly_rate, fixed_price_from, fixed_price_to
  Availability: availability_status, response_time
  Portfolio  : portfolio_videos (JSON), portfolio_images (JSON)
  Documents  : resume_file
  Social     : website, youtube, instagram, linkedin, twitter, behance
  Stats      : avg_rating, total_reviews, completed_projects, total_earnings
  Flags      : is_verified, is_featured
  Timestamps : created_at, updated_at
============================================================
"""

from datetime import datetime, timezone
import enum
from database import db


# ============================================================
# Enums
# ============================================================

class EditorCategory(enum.Enum):
    YOUTUBE         = 'youtube'
    REELS           = 'reels'
    WEDDING         = 'wedding'
    CORPORATE       = 'corporate'
    MOTION_GRAPHICS = 'motion_graphics'
    PODCAST         = 'podcast'
    ECOMMERCE       = 'ecommerce'
    DOCUMENTARY     = 'documentary'
    OTHER           = 'other'


class AvailabilityStatus(enum.Enum):
    AVAILABLE   = 'available'    # Open to new projects
    BUSY        = 'busy'         # Occupied, limited slots
    ON_VACATION = 'on_vacation'  # Not accepting work


# ============================================================
# Model: EditorProfile
# ============================================================

class EditorProfile(db.Model):
    """
    One-to-one extension of the User model for editors.
    Created when an editor completes their profile setup.
    """

    __tablename__ = 'editor_profiles'

    # ----------------------------------------------------------
    # Primary Key
    # ----------------------------------------------------------
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    # ----------------------------------------------------------
    # Foreign Key — links to users table (one-to-one)
    # ----------------------------------------------------------
    user_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id', ondelete='CASCADE'),
        unique=True,        # Each user gets exactly one profile
        nullable=False,
        index=True
    )

    # ----------------------------------------------------------
    # Identity Fields
    # ----------------------------------------------------------
    username = db.Column(
        db.String(50),
        unique=True,
        nullable=True,
        index=True,
        comment='Unique @handle for the editor (e.g. @sarahchen)'
    )

    tagline = db.Column(
        db.String(150),
        nullable=True,
        comment='Short professional headline shown under name'
    )

    bio = db.Column(
        db.Text,
        nullable=True,
        comment='Full professional bio (up to ~1000 chars)'
    )

    # ----------------------------------------------------------
    # Media — profile photo & cover banner
    # ----------------------------------------------------------
    profile_photo = db.Column(
        db.String(500),
        nullable=True,
        default=None,
        comment='Filename of uploaded profile photo (stored in uploads/avatars/)'
    )

    cover_banner = db.Column(
        db.String(500),
        nullable=True,
        default=None,
        comment='Filename of uploaded cover banner (stored in uploads/banners/)'
    )

    # ----------------------------------------------------------
    # Professional Details
    # ----------------------------------------------------------
    category = db.Column(
        db.Enum(EditorCategory),
        nullable=True,
        default=EditorCategory.OTHER,
        comment='Primary editing specialization'
    )

    experience_years = db.Column(
        db.Integer,
        nullable=True,
        default=0,
        comment='Years of professional video editing experience'
    )

    # JSON arrays stored as PostgreSQL JSON columns
    # Example: ["Adobe Premiere Pro", "After Effects", "DaVinci Resolve"]
    skills = db.Column(
        db.JSON,
        nullable=True,
        default=list,
        comment='List of skills/techniques the editor knows'
    )

    # Example: ["Adobe Premiere Pro", "DaVinci Resolve", "Final Cut Pro"]
    software_used = db.Column(
        db.JSON,
        nullable=True,
        default=list,
        comment='Video editing software the editor uses'
    )

    # Example: ["English", "Hindi", "Tamil"]
    languages = db.Column(
        db.JSON,
        nullable=True,
        default=list,
        comment='Languages the editor can communicate in'
    )

    # ----------------------------------------------------------
    # Location
    # ----------------------------------------------------------
    city = db.Column(db.String(100), nullable=True)
    country = db.Column(db.String(100), nullable=True)

    # ----------------------------------------------------------
    # Pricing
    # ----------------------------------------------------------
    hourly_rate = db.Column(
        db.Numeric(10, 2),
        nullable=True,
        default=None,
        comment='Hourly rate in INR'
    )

    fixed_price_from = db.Column(
        db.Numeric(10, 2),
        nullable=True,
        default=None,
        comment='Minimum fixed project price in INR'
    )

    fixed_price_to = db.Column(
        db.Numeric(10, 2),
        nullable=True,
        default=None,
        comment='Maximum fixed project price in INR'
    )

    # ----------------------------------------------------------
    # Availability
    # ----------------------------------------------------------
    availability_status = db.Column(
        db.Enum(AvailabilityStatus),
        nullable=False,
        default=AvailabilityStatus.AVAILABLE,
        comment='Current work availability'
    )

    response_time = db.Column(
        db.String(50),
        nullable=True,
        default='Within 24 hours',
        comment='Typical response time to client messages'
    )

    # ----------------------------------------------------------
    # Portfolio
    # ----------------------------------------------------------
    # JSON array of video objects:
    # [{ "title": "...", "url": "https://youtube.com/...", "thumbnail": "...", "description": "..." }]
    portfolio_videos = db.Column(
        db.JSON,
        nullable=True,
        default=list,
        comment='List of portfolio video entries (YouTube/Vimeo links)'
    )

    # JSON array of image objects:
    # [{ "title": "...", "filename": "...", "description": "..." }]
    portfolio_images = db.Column(
        db.JSON,
        nullable=True,
        default=list,
        comment='List of uploaded portfolio image entries'
    )

    # ----------------------------------------------------------
    # Documents
    # ----------------------------------------------------------
    resume_file = db.Column(
        db.String(500),
        nullable=True,
        default=None,
        comment='Filename of uploaded resume PDF (stored in uploads/resumes/)'
    )

    # ----------------------------------------------------------
    # Social Media Links
    # ----------------------------------------------------------
    website_url   = db.Column(db.String(500), nullable=True)
    youtube_url   = db.Column(db.String(500), nullable=True)
    instagram_url = db.Column(db.String(500), nullable=True)
    linkedin_url  = db.Column(db.String(500), nullable=True)
    twitter_url   = db.Column(db.String(500), nullable=True)
    behance_url   = db.Column(db.String(500), nullable=True)

    # ----------------------------------------------------------
    # Stats (updated by order/review system later)
    # ----------------------------------------------------------
    avg_rating = db.Column(
        db.Numeric(3, 2),
        nullable=False,
        default=0.00,
        comment='Average rating from client reviews (0.00 - 5.00)'
    )

    total_reviews = db.Column(
        db.Integer,
        nullable=False,
        default=0,
        comment='Total number of reviews received'
    )

    completed_projects = db.Column(
        db.Integer,
        nullable=False,
        default=0,
        comment='Total number of completed orders/projects'
    )

    total_earnings = db.Column(
        db.Numeric(12, 2),
        nullable=False,
        default=0.00,
        comment='Cumulative earnings from completed orders (INR)'
    )

    # ----------------------------------------------------------
    # Platform Flags
    # ----------------------------------------------------------
    is_verified = db.Column(
        db.Boolean,
        nullable=False,
        default=False,
        comment='Admin-verified editor badge'
    )

    is_featured = db.Column(
        db.Boolean,
        nullable=False,
        default=False,
        comment='Featured on homepage and search results'
    )

    # ----------------------------------------------------------
    # Timestamps
    # ----------------------------------------------------------
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )

    updated_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    # ----------------------------------------------------------
    # Relationship — back-reference to the User object
    # ----------------------------------------------------------
    user = db.relationship(
        'User',
        backref=db.backref('editor_profile', uselist=False, lazy='joined'),
        lazy='joined'
    )

    # ----------------------------------------------------------
    # Constructor
    # ----------------------------------------------------------
    def __init__(self, user_id, username=None, **kwargs):
        self.user_id = user_id
        self.username = username
        # Apply any extra keyword arguments as attributes
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

    # ----------------------------------------------------------
    # Serialization
    # ----------------------------------------------------------
    def to_dict(self, include_user=True, public=True):
        """
        Convert EditorProfile to a JSON-serializable dictionary.

        Args:
            include_user (bool): Whether to embed the user's basic info
            public (bool): If True, omits sensitive/internal fields

        Returns:
            dict: Safe-to-serialize profile data
        """
        data = {
            'id':                   self.id,
            'user_id':              self.user_id,
            'username':             self.username,
            'tagline':              self.tagline,
            'bio':                  self.bio,
            'profile_photo':        self.profile_photo,
            'cover_banner':         self.cover_banner,
            'category':             self.category.value if self.category else None,
            'experience_years':     self.experience_years,
            'skills':               self.skills or [],
            'software_used':        self.software_used or [],
            'languages':            self.languages or [],
            'city':                 self.city,
            'country':              self.country,
            'hourly_rate':          float(self.hourly_rate) if self.hourly_rate else None,
            'fixed_price_from':     float(self.fixed_price_from) if self.fixed_price_from else None,
            'fixed_price_to':       float(self.fixed_price_to) if self.fixed_price_to else None,
            'availability_status':  self.availability_status.value if self.availability_status else 'available',
            'response_time':        self.response_time,
            'portfolio_videos':     self.portfolio_videos or [],
            'portfolio_images':     self.portfolio_images or [],
            'resume_file':          self.resume_file,
            'website_url':          self.website_url,
            'youtube_url':          self.youtube_url,
            'instagram_url':        self.instagram_url,
            'linkedin_url':         self.linkedin_url,
            'twitter_url':          self.twitter_url,
            'behance_url':          self.behance_url,
            'avg_rating':           float(self.avg_rating) if self.avg_rating else 0.0,
            'total_reviews':        self.total_reviews,
            'completed_projects':   self.completed_projects,
            'is_verified':          self.is_verified,
            'is_featured':          self.is_featured,
            'created_at':           self.created_at.isoformat() if self.created_at else None,
            'updated_at':           self.updated_at.isoformat() if self.updated_at else None,
        }

        # Embed basic user info (name, email, role)
        if include_user and self.user:
            data['user'] = {
                'id':           self.user.id,
                'full_name':    self.user.full_name,
                'email':        self.user.email if not public else None,
                'role':         self.user.role.value,
                'is_verified':  self.user.is_verified,
            }
            # Remove None email in public view
            if public:
                data['user'].pop('email', None)

        # Internal-only fields
        if not public:
            data['total_earnings'] = float(self.total_earnings) if self.total_earnings else 0.0

        return data

    def __repr__(self):
        return f"<EditorProfile user_id={self.user_id} username='{self.username}'>"
