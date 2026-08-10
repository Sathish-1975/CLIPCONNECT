"""
============================================================
ClipConnect - Invoice Controller
============================================================
Handles HTML invoice rendering for completed projects.
"""
from flask import render_template_string
from database import db
from models.payment_model import Invoice, Payment
from utils.response_helper import error_response

INVOICE_HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Invoice {{ invoice.invoice_number }}</title>
    <style>
        body { font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; padding: 40px; color: #333; max-width: 800px; margin: auto; }
        .header { display: flex; justify-content: space-between; border-bottom: 2px solid #eee; padding-bottom: 20px; margin-bottom: 30px; }
        .logo { font-size: 24px; font-weight: bold; color: #6366f1; }
        .invoice-details { text-align: right; }
        .section { margin-bottom: 30px; }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #eee; }
        th { background-color: #f8fafc; }
        .total-row { font-weight: bold; font-size: 1.2rem; }
        .print-btn { padding: 10px 20px; background: #6366f1; color: #fff; border: none; border-radius: 6px; cursor: pointer; float: right; }
        @media print { .print-btn { display: none; } body { padding: 0; } }
    </style>
</head>
<body>
    <button class="print-btn" onclick="window.print()">Print / Save PDF</button>
    
    <div class="header">
        <div>
            <div class="logo">ClipConnect</div>
            <p>123 Freelance Blvd, Tech City<br>contact@clipconnect.com</p>
        </div>
        <div class="invoice-details">
            <h2>INVOICE</h2>
            <p><strong>Invoice #:</strong> {{ invoice.invoice_number }}</p>
            <p><strong>Date:</strong> {{ invoice.created_at.strftime('%B %d, %Y') }}</p>
            <p><strong>Status:</strong> PAID</p>
        </div>
    </div>

    <div class="section" style="display: flex; justify-content: space-between;">
        <div>
            <h3>Billed To (Client):</h3>
            <p><strong>{{ client_name }}</strong></p>
        </div>
        <div style="text-align: right;">
            <h3>Editor / Payee:</h3>
            <p><strong>{{ editor_name }}</strong></p>
        </div>
    </div>

    <div class="section">
        <h3>Project Details</h3>
        <p><strong>Project:</strong> {{ project_title }}</p>
    </div>

    <table>
        <thead>
            <tr>
                <th>Description</th>
                <th style="text-align: right">Amount (INR)</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>Video Editing Services - Final Delivery</td>
                <td style="text-align: right">₹{{ amount }}</td>
            </tr>
            <tr class="total-row">
                <td style="text-align: right; border-bottom: none;">Total Paid:</td>
                <td style="text-align: right; border-bottom: none; color: #10b981;">₹{{ amount }}</td>
            </tr>
        </tbody>
    </table>
    
    <div style="margin-top: 50px; text-align: center; color: #64748b; font-size: 0.9rem;">
        <p>Thank you for using ClipConnect!</p>
        <p>This is a computer-generated invoice and does not require a physical signature.</p>
    </div>
</body>
</html>
"""

def generate_invoice_html(current_user: dict, project_id: int):
    """
    GET /api/invoices/<project_id>/download
    Returns an HTML page that acts as the invoice. 
    Can be printed to PDF by the user.
    """
    payment = Payment.query.filter(Payment.project_id==project_id, Payment.status.in_(['paid', 'released'])).first()
    if not payment:
        return "<h1>Payment record not found</h1>", 404
        
    invoice = Invoice.query.filter_by(payment_id=payment.id).first()
    if not invoice:
        return "<h1>Invoice not found</h1>", 404

    # Authorization: only client, editor, or admin can view
    user_id = current_user['user_id']
    role = current_user.get('role')
    if role != 'admin' and user_id not in [invoice.client_id, invoice.editor_id]:
        return "<h1>Unauthorized</h1>", 403

    html = render_template_string(
        INVOICE_HTML_TEMPLATE,
        invoice=invoice,
        client_name=payment.client.full_name,
        editor_name=payment.editor.full_name,
        project_title=payment.project.title,
        amount=f"{invoice.amount:,.2f}"
    )
    
    return html
