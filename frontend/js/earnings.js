/**
 * ClipConnect - Earnings Dashboard JavaScript
 */

document.addEventListener('DOMContentLoaded', async () => {
    const token = localStorage.getItem('token');
    if (!token) {
        window.location.href = 'login.html';
        return;
    }

    await loadPaymentHistory();

    async function loadPaymentHistory() {
        const tbody = document.getElementById('transactions-tbody');
        try {
            const res = await API.get('/payments/history');
            if (res && res.success) {
                const payments = res.data.payments || [];
                
                let totalRev = 0;
                let escrowAmt = 0;
                let pendingAmt = 0;

                payments.forEach(p => {
                    if (p.status === 'escrow_held') escrowAmt += p.amount;
                    if (p.status === 'released' || p.status === 'paid') totalRev += p.amount;
                });

                document.getElementById('total-revenue').textContent = `₹${totalRev.toLocaleString()}`;
                document.getElementById('escrow-funds').textContent = `₹${escrowAmt.toLocaleString()}`;
                document.getElementById('pending-payouts').textContent = `₹${pendingAmt.toLocaleString()}`;

                if (!payments.length) {
                    tbody.innerHTML = `<tr><td colspan="6" style="text-align: center; color: #9ca3af;">No payment transactions recorded yet.</td></tr>`;
                    return;
                }

                tbody.innerHTML = payments.map(p => `
                    <tr>
                        <td>#${p.id}</td>
                        <td style="font-weight: 600;">${p.project_title ? escapeHtml(p.project_title) : 'Direct Service'}</td>
                        <td style="font-weight: bold; color: #fff;">₹${p.amount.toLocaleString()}</td>
                        <td>
                            <span class="${p.status === 'escrow_held' ? 'badge-escrow' : 'badge-completed'}">
                                ${p.status === 'escrow_held' ? 'Escrow Held' : (p.status === 'paid' ? 'Paid' : 'Released')}
                            </span>
                        </td>
                        <td>${new Date(p.created_at).toLocaleDateString()}</td>
                        <td>
                            <button onclick="downloadInvoice(${p.id})" style="background: rgba(255,255,255,0.08); border: 1px solid rgba(255,255,255,0.12); color: #fff; padding: 4px 10px; border-radius: 6px; cursor: pointer;">
                                📄 Invoice
                            </button>
                        </td>
                    </tr>
                `).join('');
            }
        } catch (err) {
            tbody.innerHTML = `<tr><td colspan="6" style="text-align: center; color: #ef4444;">Failed to load transaction history.</td></tr>`;
        }
    }

    window.downloadInvoice = async function(paymentId) {
        try {
            const res = await API.get(`/payments/invoice/${paymentId}`);
            if (res && res.success) {
                const inv = res.data.invoice;
                alert(`Invoice Details:\nInvoice #: ${inv.invoice_number}\nAmount: ₹${inv.total_amount}\nTax: ₹${inv.tax_amount}\nFee: ₹${inv.platform_fee}`);
            }
        } catch (err) {
            alert('Failed to fetch invoice details.');
        }
    };

    function escapeHtml(text) {
        if (!text) return '';
        return text.replace(/[&<>"']/g, function(m) {
            return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' }[m];
        });
    }
});
