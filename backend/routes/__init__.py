"""
============================================================
ClipConnect - Routes Package Initialization
============================================================
Registers all Flask Blueprints with their URL prefixes.
Add each new feature blueprint here as the project grows.
============================================================
"""

from routes.auth_routes import auth_bp
from routes.user_routes import user_bp
from routes.api_routes import api_bp
from routes.project_routes import project_bp
from routes.notification_routes import notification_bp
from routes.payment_routes import payment_bp
from routes.ai_routes import ai_bp
from routes.admin_routes import admin_bp
from routes.chat_routes import chat_bp
from routes.invoice_routes import invoice_bp

def register_all_blueprints(app):
    """
    Register all route blueprints with the Flask application.

    URL Prefixes:
        /api/auth          → auth_bp         (register, login, me)
        /api/users         → user_bp         (editor profiles, uploads, browse)
        /api/projects      → project_bp      (project posting system)
        /api/notifications → notification_bp (user notifications system)
        /api/payments      → payment_bp      (escrow, transactions, razorpay)
        /api/ai            → ai_bp           (ai matching & description generator)
        /api/admin         → admin_bp        (platform stats, moderation, audit)
        /api/chat          → chat_bp         (real-time 1-on-1 messaging)
        /api/invoices      → invoice_bp      (invoice HTML endpoints)
        /api               → api_bp          (simplified REST API endpoints)
    """
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(user_bp, url_prefix='/api/users')
    app.register_blueprint(project_bp, url_prefix='/api/projects')
    app.register_blueprint(notification_bp, url_prefix='/api/notifications')
    app.register_blueprint(payment_bp, url_prefix='/api/payments')
    app.register_blueprint(ai_bp, url_prefix='/api/ai')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    app.register_blueprint(chat_bp, url_prefix='/api/chat')
    app.register_blueprint(invoice_bp, url_prefix='/api/invoices')
    app.register_blueprint(api_bp, url_prefix='/api')

    app.logger.info("[OK] All blueprints registered successfully.")
