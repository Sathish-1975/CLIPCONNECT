/**
 * ClipConnect - Admin Dashboard JavaScript
 * Fully functional script to populate the Admin Dashboard with live stats, 
 * projects, proposals, activity feeds, users, charts, and polling.
 */

let allProjects = [];
let allProposals = [];
let allUsers = [];

document.addEventListener('DOMContentLoaded', async () => {
    const token = localStorage.getItem('token') || localStorage.getItem('cc_token') || localStorage.getItem('jwt_token');
    const userStr = localStorage.getItem('user') || localStorage.getItem('cc_user');

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

    // Set auth header for API calls if API.js supports it, else we rely on API.js
    
    await loadEverything();

    // Setup Filter Listeners
    document.getElementById('filter-proj-name')?.addEventListener('input', renderProjects);
    document.getElementById('filter-proj-client')?.addEventListener('input', renderProjects);
    document.getElementById('filter-proj-status')?.addEventListener('change', renderProjects);

    // 15-second polling
    setInterval(loadEverything, 15000);
});

async function loadEverything() {
    try {
        await Promise.all([
            loadAdminStats(),
            loadAdminProjects(),
            loadAdminProposals(),
            loadAdminUsers()
        ]);
        
        const el = document.getElementById('last-updated');
        if (el) el.textContent = `Last updated: ${new Date().toLocaleTimeString()}`;
    } catch (err) {
        console.error("Polling error:", err);
    }
}

async function loadAdminStats() {
    try {
        const res = await API.get('/admin/dashboard');
        if (res && res.success) {
            const data = res.data;
            const stats = data.stats;
            
            // 1. Summary Cards
            setTxt('c-users', stats.total_users || 0);
            setTxt('c-clients', stats.total_clients || 0);
            setTxt('c-editors', `${stats.total_editors || 0} / ${stats.active_editors || 0}`);
            setTxt('c-projects', stats.total_projects || 0);
            setTxt('c-completed-proj', stats.completed_projects || 0);
            setTxt('c-hires', `${stats.pending_hire_requests || 0} / ${stats.accepted_hire_requests || 0}`);
            setTxt('c-tx-total', stats.total_transactions || 0);
            
            // 8. Revenue Overview
            setTxt('c-rev-total', formatCurrency(stats.total_revenue));
            setTxt('c-rev-today', formatCurrency(stats.today_revenue));
            setTxt('c-rev-month', formatCurrency(stats.monthly_revenue));
            setTxt('c-pay-pending', stats.pending_payments || 0);
            setTxt('c-pay-completed', stats.completed_payments || 0);

            // 2. Recent Platform Activity
            renderFeed('feed-activity', data.recent_activity || []);

            // 9. Notifications Panel
            renderNotifs('feed-notifs', data.admin_notifications || []);
        }
    } catch (err) {
        console.error('Failed to load admin stats:', err);
    }
}

async function loadAdminProjects() {
    try {
        const res = await API.get('/admin/projects');
        if (res && res.success) {
            allProjects = res.data.projects || [];
            renderProjects();
            renderProjectStatusChart();
        }
    } catch (err) {
        console.error('Failed to load projects:', err);
    }
}

async function loadAdminProposals() {
    try {
        const res = await API.get('/admin/proposals');
        if (res && res.success) {
            allProposals = res.data.proposals || [];
            renderProposals();
        }
    } catch (err) {
        console.error('Failed to load proposals:', err);
    }
}

async function loadAdminUsers() {
    try {
        const res = await API.get('/admin/users?per_page=100'); // Load up to 100 users for demo
        if (res && res.success) {
            allUsers = res.data.items || [];
            renderUsers();
            renderClientActivity();
            renderEditorResponses();
        }
    } catch (err) {
        console.error('Failed to load users:', err);
    }
}

/* --- RENDERERS --- */

function renderProjects() {
    const tbody = document.getElementById('tb-projects');
    if (!tbody) return;

    let filtered = allProjects;
    
    // Apply filters
    const nameFilter = (document.getElementById('filter-proj-name')?.value || '').toLowerCase();
    const clientFilter = (document.getElementById('filter-proj-client')?.value || '').toLowerCase();
    const statusFilter = (document.getElementById('filter-proj-status')?.value || '').toLowerCase();

    if (nameFilter) filtered = filtered.filter(p => (p.title || '').toLowerCase().includes(nameFilter));
    if (clientFilter) filtered = filtered.filter(p => (p.client_name || '').toLowerCase().includes(clientFilter));
    if (statusFilter) filtered = filtered.filter(p => (p.status || '').toLowerCase() === statusFilter);

    if (!filtered.length) {
        tbody.innerHTML = `<tr><td colspan="7" style="text-align:center;color:#9ca3af">No projects found.</td></tr>`;
        return;
    }

    tbody.innerHTML = filtered.map(p => `
        <tr>
            <td>#${p.id}</td>
            <td style="font-weight:600">${escapeHtml(p.title)}</td>
            <td>${escapeHtml(p.client_name)}</td>
            <td>${escapeHtml(p.editor_name)}</td>
            <td><span class="status-badge ${getStatusColor(p.status)}">${formatStatus(p.status)}</span></td>
            <td>
                <div style="width:100%;background:#333;height:6px;border-radius:3px;margin-top:4px;overflow:hidden;">
                    <div style="width:${p.completion_pct || 0}%;background:#10b981;height:100%;"></div>
                </div>
                <small style="color:#9ca3af">${p.completion_pct || 0}%</small>
            </td>
            <td><button class="btn btn-outline btn-sm" onclick="openDetailsModal(${p.id})">Details</button></td>
        </tr>
    `).join('');
}

function renderProposals() {
    const tbody = document.getElementById('tb-hires');
    if (!tbody) return;
    
    if (!allProposals.length) {
        tbody.innerHTML = `<tr><td colspan="6" style="text-align:center;color:#9ca3af">No hire requests found.</td></tr>`;
        return;
    }

    tbody.innerHTML = allProposals.map(p => `
        <tr>
            <td style="font-weight:600">${escapeHtml(p.project_title)}</td>
            <td>${escapeHtml(p.client_name)}</td>
            <td>${escapeHtml(p.editor_name)}</td>
            <td><span style="color:${p.status==='accepted'?'#10b981':p.status==='rejected'?'#ef4444':'#f59e0b'}">${formatStatus(p.status)}</span></td>
            <td>${formatDate(p.sent_date)}</td>
            <td>${p.status !== 'pending' && p.status !== 'invited' ? formatDate(p.accepted_date || p.declined_date) : '--'}</td>
        </tr>
    `).join('');
}

function renderClientActivity() {
    const tbody = document.getElementById('tb-clients');
    if (!tbody) return;
    
    const clients = allUsers.filter(u => u.role === 'client' && u.client_stats);
    if (!clients.length) {
        tbody.innerHTML = `<tr><td colspan="5" style="text-align:center;color:#9ca3af">No client data.</td></tr>`;
        return;
    }

    tbody.innerHTML = clients.map(c => {
        const st = c.client_stats;
        return `
        <tr>
            <td style="font-weight:600">${escapeHtml(c.full_name)}</td>
            <td>${st.projects_posted || 0}</td>
            <td>${st.projects_active || 0}</td>
            <td>${st.projects_completed || 0}</td>
            <td>${formatCurrency(st.total_amount_spent || 0)}</td>
        </tr>`;
    }).join('');
}

function renderEditorResponses() {
    const tbody = document.getElementById('tb-editors');
    if (!tbody) return;
    
    const editors = allUsers.filter(u => u.role === 'editor' && u.editor_stats);
    if (!editors.length) {
        tbody.innerHTML = `<tr><td colspan="7" style="text-align:center;color:#9ca3af">No editor data.</td></tr>`;
        return;
    }

    tbody.innerHTML = editors.map(e => {
        const st = e.editor_stats;
        return `
        <tr>
            <td style="font-weight:600">${escapeHtml(e.full_name)}</td>
            <td>${st.projects_assigned || 0}</td>
            <td>${st.projects_accepted || 0}</td>
            <td>${st.projects_declined || 0}</td>
            <td>${st.projects_completed || 0}</td>
            <td style="color:#3b82f6">${st.acceptance_rate || '0%'}</td>
            <td style="color:#10b981">${st.completion_rate || '0%'}</td>
        </tr>`;
    }).join('');
}

function renderUsers() {
    const tbody = document.getElementById('tb-users');
    if (!tbody) return;
    
    if (!allUsers.length) {
        tbody.innerHTML = `<tr><td colspan="6" style="text-align:center;color:#9ca3af">No users.</td></tr>`;
        return;
    }

    tbody.innerHTML = allUsers.map(u => `
        <tr>
            <td>#${u.id}</td>
            <td style="font-weight: 600;">${escapeHtml(u.full_name)}</td>
            <td>${escapeHtml(u.email)}</td>
            <td><span style="text-transform: capitalize; padding:2px 8px; border-radius:4px; background:rgba(255,255,255,0.1); font-size:0.8rem;">${u.role}</span></td>
            <td><span style="color: ${u.is_active ? '#10b981' : '#ef4444'};">${u.is_active ? 'Active' : 'Suspended'}</span></td>
            <td><button class="btn ${u.is_active ? 'btn-danger' : 'btn-success'} btn-sm" onclick="toggleUserStatus(${u.id}, ${!u.is_active})">${u.is_active ? 'Suspend' : 'Activate'}</button></td>
        </tr>
    `).join('');
}

function renderFeed(id, items) {
    const el = document.getElementById(id);
    if (!el) return;
    if (!items.length) { el.innerHTML = '<div style="color:#9ca3af">No activity yet.</div>'; return; }
    
    el.innerHTML = items.map(item => `
        <div class="feed-item">
            <div class="feed-time">${formatDate(item.date)}</div>
            <div class="feed-title">${escapeHtml(item.type)}</div>
            <div class="feed-desc">${escapeHtml(item.text)}</div>
        </div>
    `).join('');
}

function renderNotifs(id, items) {
    const el = document.getElementById(id);
    if (!el) return;
    if (!items.length) { el.innerHTML = '<div style="color:#9ca3af">No notifications.</div>'; return; }
    
    el.innerHTML = items.map(item => `
        <div class="feed-item">
            <div class="feed-time">${formatDate(item.created_at)}</div>
            <div class="feed-title" style="color: ${item.type==='error'?'#ef4444':'#e5e7eb'}">${escapeHtml(item.title)}</div>
            <div class="feed-desc">${escapeHtml(item.message)}</div>
        </div>
    `).join('');
}

/* --- CHARTS --- */

function renderProjectStatusChart() {
    const chart = document.getElementById('chart-proj-status');
    if (!chart) return;
    
    const counts = { pending: 0, in_progress: 0, completed: 0, cancelled: 0 };
    allProjects.forEach(p => {
        if (p.status === 'pending' || p.status === 'under_review') counts.pending++;
        else if (p.status === 'in_progress') counts.in_progress++;
        else if (p.status === 'completed') counts.completed++;
        else if (p.status === 'cancelled') counts.cancelled++;
    });
    
    const max = Math.max(1, counts.pending, counts.in_progress, counts.completed, counts.cancelled);
    
    const drawBar = (label, val, color) => {
        const pct = Math.max(5, (val / max) * 100);
        return `
            <div class="css-bar-wrapper">
                <div class="css-bar-val">${val}</div>
                <div class="css-bar" style="height:${pct}%; background:${color};"></div>
                <div class="css-bar-label">${label}</div>
            </div>
        `;
    };
    
    chart.innerHTML = 
        drawBar('Pending', counts.pending, '#f59e0b') +
        drawBar('Active', counts.in_progress, '#3b82f6') +
        drawBar('Done', counts.completed, '#10b981') +
        drawBar('Cancel', counts.cancelled, '#ef4444');
}

/* --- MODAL --- */

window.openDetailsModal = function(projectId) {
    const proj = allProjects.find(p => p.id === projectId);
    if (!proj) return;
    
    document.getElementById('mdl-title').textContent = `Project #${proj.id} - ${proj.title}`;
    
    const row = (label, val) => `<div class="modal-detail-row"><div class="modal-detail-label">${label}</div><div class="modal-detail-val">${escapeHtml(String(val||'--'))}</div></div>`;
    
    let html = '';
    html += row('Client Name', proj.client_name);
    html += row('Hired Editor', proj.editor_name !== 'Unknown' ? proj.editor_name : 'None yet');
    html += row('Status', formatStatus(proj.status));
    html += row('Budget', formatCurrency(proj.budget));
    html += row('Created Date', formatDate(proj.created_at));
    html += row('Deadline', formatDate(proj.deadline));
    html += row('Description', proj.description);
    
    document.getElementById('mdl-body').innerHTML = html;
    document.getElementById('details-modal').style.display = 'flex';
};

window.closeDetailsModal = function() {
    document.getElementById('details-modal').style.display = 'none';
};

/* --- UTILS --- */

window.toggleUserStatus = async function(userId, activate) {
    if (!confirm(`Are you sure you want to ${activate ? 'activate' : 'suspend'} user #${userId}?`)) return;
    try {
        const res = await API.patch(`/admin/users/${userId}/status`, { action: activate ? 'activate' : 'suspend' });
        if (res && res.success) {
            loadAdminUsers();
        }
    } catch (err) { alert('Failed to update user status.'); }
};

function setTxt(id, val) { const el = document.getElementById(id); if (el) el.textContent = val; }
function escapeHtml(text) {
    if (!text) return '';
    return String(text).replace(/[&<>"']/g, m => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' }[m]));
}
function formatCurrency(val) {
    if (!val) return '₹0';
    return `₹${parseFloat(val).toLocaleString('en-IN')}`;
}
function formatDate(iso) {
    if (!iso) return 'N/A';
    const d = new Date(iso);
    return d.toLocaleString('en-IN', { month:'short', day:'numeric', hour:'numeric', minute:'2-digit' });
}
function formatStatus(st) {
    if (!st) return 'Unknown';
    return st.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
}
function getStatusColor(st) {
    if (st === 'completed') return 'status-badge--completed';
    if (st === 'cancelled') return 'status-badge--cancelled';
    if (st === 'in_progress') return 'status-badge--pending'; // Usually blue or orange
    return '';
}
