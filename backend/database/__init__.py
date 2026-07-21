"""
============================================================
ClipConnect - Database Package Initialization
============================================================
Purpose:
    Creates and exports the single SQLAlchemy instance (db).
    This is the ONLY place where SQLAlchemy is instantiated.

Why a single instance?
    SQLAlchemy uses the "Application Factory" pattern.
    db is created here without being bound to any Flask app.
    It gets bound to the actual Flask app in app.py via db.init_app(app).
    This prevents circular imports and allows testing with different configs.

Usage:
    from database import db
============================================================
"""

from flask_sqlalchemy import SQLAlchemy

# Create the SQLAlchemy instance WITHOUT binding it to a Flask app yet.
# It will be initialized with the app in app.py using db.init_app(app)
db = SQLAlchemy()
