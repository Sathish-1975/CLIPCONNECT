"""
============================================================
ClipConnect - Transactional Email Helper
============================================================
Why this file exists:
  Provides automated HTML email template generation and dispatching for transactional events
  (Registration, Email Verification, Password Reset, Hire Requests, Payments, Reviews).

What it does:
  - Generates responsive HTML email templates with ClipConnect branding.
  - Sends emails using SMTP or logs to stdout when SMTP is unconfigured.
  - Automatically records every sent/failed email in the `EmailLog` database table.

How it integrates with the rest of the application:
  - Invoked by `auth_controller.py`, `hire_controller.py`, `payment_controller.py`,
    and `review_controller.py` on state transitions.
============================================================
"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timezone

from database import db
from models.email_log_model import EmailLog

# Configuration from environment
SMTP_HOST = os.getenv('SMTP_HOST', 'smtp.gmail.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
SMTP_USER = os.getenv('SMTP_USER', '')
SMTP_PASS = os.getenv('SMTP_PASS', '')
SENDER_EMAIL = os.getenv('SENDER_EMAIL', 'no-reply@clipconnect.com')


def _render_base_html(title: str, content_html: str) -> str:
    """Wrap email content in a dark-themed, glassmorphic HTML email template."""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <title>{title}</title>
      <style>
        body {{ font-family: 'Helvetica Neue', Arial, sans-serif; background-color: #0f172a; color: #f8fafc; margin: 0; padding: 20px; }}
        .container {{ max-width: 600px; margin: 0 auto; background: #1e293b; border-radius: 12px; padding: 32px; border: 1px solid rgba(255,255,255,0.1); }}
        .brand {{ font-size: 24px; font-weight: 700; color: #a78bfa; margin-bottom: 24px; text-align: center; }}
        .content {{ font-size: 15px; line-height: 1.6; color: #cbd5e1; }}
        .btn {{ display: inline-block; background: linear-gradient(135deg, #7c3aed, #6366f1); color: #ffffff !important; padding: 12px 24px; border-radius: 8px; text-decoration: none; font-weight: 600; margin-top: 20px; }}
        .footer {{ margin-top: 32px; font-size: 12px; color: #64748b; text-align: center; border-top: 1px solid rgba(255,255,255,0.08); padding-top: 16px; }}
      </style>
    </head>
    <body>
      <div class="container">
        <div class="brand">✂ Clip<span>Connect</span></div>
        <div class="content">
          {content_html}
        </div>
        <div class="footer">
          © {datetime.now().year} ClipConnect. All rights reserved.<br>
          Connecting Creators with World-Class Editors.
        </div>
      </div>
    </body>
    </html>
    """


def send_email(recipient_email: str, subject: str, body_html: str, template_name: str = 'general') -> bool:
    """
    Dispatches an HTML email and logs the result to database.
    """
    full_html = _render_base_html(subject, body_html)
    status = 'sent'
    err_msg = None

    if SMTP_USER and SMTP_PASS:
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From']    = f"ClipConnect <{SENDER_EMAIL}>"
            msg['To']      = recipient_email
            msg.attach(MIMEText(full_html, 'html'))

            server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(SENDER_EMAIL, [recipient_email], msg.as_string())
            server.quit()
        except Exception as e:
            status = 'failed'
            err_msg = str(e)
            print(f"[EMAIL ERROR] Failed to send email to {recipient_email}: {err_msg}")
    else:
        # Development mode simulation log
        print(f"[EMAIL SIMULATION] To: {recipient_email} | Subject: {subject}")

    # Record log entry in DB
    try:
        log_entry = EmailLog(
            recipient_email=recipient_email,
            subject=subject,
            template_name=template_name,
            status=status,
            error_message=err_msg
        )
        db.session.add(log_entry)
        db.session.commit()
    except Exception as db_err:
        db.session.rollback()
        print(f"[EMAIL DB LOG ERROR] {db_err}")

    return status == 'sent'


# ── Specific Transactional Email Functions ──────────────────────────────────

def send_welcome_email(user_email: str, full_name: str, role: str):
    subject = "Welcome to ClipConnect! 🎉"
    html = f"""
    <h2>Welcome aboard, {full_name}!</h2>
    <p>Your account as a <strong>{role.title()}</strong> has been successfully created.</p>
    <p>You can now browse editors, post video projects, manage orders, and connect with creators across India.</p>
    <a href="http://localhost:5001/login.html" class="btn">Log In to Your Account</a>
    """
    send_email(user_email, subject, html, 'welcome')


def send_hire_request_email(editor_email: str, editor_name: str, client_name: str, project_title: str):
    subject = f"✨ New Hire Request from {client_name}!"
    html = f"""
    <h2>Hello {editor_name},</h2>
    <p><strong>{client_name}</strong> has invited you to work on their project: <strong>"{project_title}"</strong>.</p>
    <p>Log in to your dashboard to view the request details and accept or reject the proposal.</p>
    <a href="http://localhost:5001/editor-dashboard.html" class="btn">View Hire Request</a>
    """
    send_email(editor_email, subject, html, 'hire_request')


def send_payment_success_email(client_email: str, client_name: str, project_title: str, amount: float, invoice_num: str):
    subject = f"Payment Confirmed (Invoice #{invoice_num})"
    html = f"""
    <h2>Payment Successful!</h2>
    <p>Hi {client_name}, your payment of <strong>₹{amount:,.2f}</strong> for project <strong>"{project_title}"</strong> has been safely deposited into ClipConnect Escrow.</p>
    <p>Your project status is now <strong>In Progress</strong>.</p>
    <a href="http://localhost:5001/dashboard.html" class="btn">View Project Dashboard</a>
    """
    send_email(client_email, subject, html, 'payment_success')
