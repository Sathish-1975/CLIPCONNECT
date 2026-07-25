/**
 * ClipConnect - Admin Dashboard JavaScript
 */

document.addEventListener('DOMContentLoaded', async () => {
    const token = localStorage.getItem('token');
    const userStr = localStorage.getItem('user');

    if (!token || !userStr) {
        window.location.href = 'login.html';
        return;
    }

    const currentUser = JSON.parse(userStr);
    if (currentUser.role !== 'admin') {
        alert('Access denied: Admin privileges required.');
        window.location.href = 'dashboard.html';
        return;
    }

    await loadAdminStats();
    await loadAdminUsers();
    await loadAuditLogs();

    async function loadAdminStats() {
        try {
            const res = await API.get('/admin/stats');
            if (res && res.success) {
                const stats = res.data.stats;
                document.getElementById('stat-total-users').textContent = stats.total_users || 0;
                document.getElementById('stat-active-projects').textContent = stats.active_projects || 0;
                document.getElementById('stat-escrow-balance').textContent = `₹${(stats.escrow_balance || 0).toLocaleString()}`;
                document.getElementById('stat-platform-revenue').textContent = `₹${(stats.platform_revenue || 0).toLocaleString()}`;
            }
        } catch (err) {
            console.error('Failed to load admin stats:', err);
        }
    }

    async function loadAdminUsers() {
        const tbody = document.getElementById('admin-users-tbody');
        try {
            const res = await API.get('/admin/users');
            if (res && res.success) {
                const users = res.data.users || [];
                if (!users.length) {
                    tbody.innerHTML = `<tr><td colspan="6" style="text-align: center; color: #9ca3af;">No users found.</td></tr>`;
                    return;
                }

                tbody.innerHTML = users.map(u => `
                    <tr>
                        <td>#${u.id}</td>
                        <td style="font-weight: 600;">${escapeHtml(u.full_name)}</td>
                        <td>${escapeHtml(u.email)}</td>
                        <td><span style="text-transform: capitalize;">${u.role}</span></td>
                        <td>
                            <span style="color: ${u.is_active ? '#10b981' : '#ef4444'};">
                                ${u.is_active ? 'Active' : 'Suspended'}
                            </span>
                        </td>
                        <td>
                            <button class="${u.is_active ? 'btn-danger' : 'btn-success'}" onclick="toggleUserStatus(${u.id}, ${!u.is_active})">
                                ${u.is_active ? 'Suspend' : 'Activate'}
                            </button>
                        </td>
                    </tr>
                `).join('');
            }
        } catch (err) {
            tbody.innerHTML = `<tr><td colspan="6" style="text-align: center; color: #ef4444;">Error loading users.</td></tr>`;
        }
    }

    window.toggleUserStatus = async function(userId, activate) {
        if (!confirm(`Are you sure you want to ${activate ? 'activate' : 'suspend'} user #${userId}?`)) return;

        try {
            const res = await API.patch(`/admin/users/${userId}/status`, { is_active: activate });
            if (res && res.success) {
                alert(`User status updated.`);
                loadAdminUsers();
                loadAdminStats();
            }
        } catch (err) {
            alert('Failed to update user status.');
        }
    };

    async function loadAuditLogs() {
        const tbody = document.getElementById('admin-logs-tbody');
        try {
            const res = await API.get('/admin/audit-logs');
            if (res && res.success) {
                const logs = res.data.logs || [];
                if (!logs.length) {
                    tbody.innerHTML = `<tr><td colspan="5" style="text-align: center; color: #9ca3af;">No audit logs yet.</td></tr>`;
                    return;
                }

                tbody.innerHTML = logs.map(l => `
                    <tr>
                        <td>${new Date(l.created_at).toLocaleString()}</td>
                        <td>#${l.user_id || 'System'}</td>
                        <td style="font-weight: 600;">${escapeHtml(l.action)}</td>
                        <td>${escapeHtml(l.ip_address || 'N/A')}</td>
                        <td>${escapeHtml(l.details || '')}</td>
                    </tr>
                `).join('');
            }
        } catch (err) {
            tbody.innerHTML = `<tr><td colspan="5" style="text-align: center; color: #ef4444;">Error loading audit logs.</td></tr>`;
        }
    }

    function escapeHtml(text) {
        if (!text) return '';
        return text.replace(/[&<>"']/g, function(m) {
            return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' }[m];
        });
    }
});
