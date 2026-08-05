/**
 * notifications.js — Universal notification module for ClipConnect dashboards.
 *
 * Supports:
 *   1. Bell-icon dropdown (topbar) — editor-dashboard & client dashboard
 *   2. Full notification section panel (#notif-section-list) — client dashboard
 *   3. Nav badge (#notif-nav-badge) — client dashboard sidebar
 *   4. Auto-refresh every 60 seconds.
 */

const NOTIF_API = '/api/notifications';

// ─── Icon map per notification type ─────────────────────────────────────────
const TYPE_ICON = {
  proposal_submitted:  '📩',
  proposal_accepted:   '✅',
  proposal_rejected:   '❌',
  project_assigned:    '🎯',
  deadline_near:       '⏰',
  project_completed:   '🎉',
  general:             '🔔',
};

// ─── Color map per notification type ────────────────────────────────────────
const TYPE_COLOR = {
  proposal_submitted:  '#7c3aed',
  proposal_accepted:   '#059669',
  proposal_rejected:   '#dc2626',
  project_assigned:    '#2563eb',
  deadline_near:       '#d97706',
  project_completed:   '#0891b2',
  general:             '#6b7280',
};

// ─── Relative time helper ────────────────────────────────────────────────────
function timeAgo(isoStr) {
  if (!isoStr) return '';
  const diff = Date.now() - new Date(isoStr).getTime();
  const mins  = Math.floor(diff / 60000);
  const hours = Math.floor(diff / 3600000);
  const days  = Math.floor(diff / 86400000);
  if (mins  < 1)  return 'just now';
  if (mins  < 60) return `${mins}m ago`;
  if (hours < 24) return `${hours}h ago`;
  return `${days}d ago`;
}

// ─── Get auth token from localStorage ───────────────────────────────────────
function getToken() {
  return localStorage.getItem('cc_token')
      || localStorage.getItem('jwt_token')
      || localStorage.getItem('token')
      || '';
}

// ─── Fetch notifications from API ───────────────────────────────────────────
async function fetchNotifications() {
  const token = getToken();
  if (!token) return null;
  try {
    const res = await fetch(NOTIF_API, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    const result = await res.json();
    if (!res.ok || !result.success) return null;
    return result.data;
  } catch (err) {
    console.warn('[Notifications] Fetch error:', err);
    return null;
  }
}

// ─── Mark one notification as read ──────────────────────────────────────────
async function markOneRead(id) {
  const token = getToken();
  await fetch(`${NOTIF_API}/${id}/read`, {
    method: 'PATCH',
    headers: { 'Authorization': `Bearer ${token}` }
  });
}

// ─── Mark all notifications as read ─────────────────────────────────────────
async function markAllRead() {
  const token = getToken();
  await fetch(`${NOTIF_API}/read-all`, {
    method: 'PATCH',
    headers: { 'Authorization': `Bearer ${token}` }
  });
}

// ─── Render bell dropdown list ───────────────────────────────────────────────
function renderDropdown(dropdown, notifications, unreadCount, dot) {
  const notifDot = document.getElementById('notif-dot') || dot;
  if (notifDot) {
    notifDot.style.display = unreadCount > 0 ? 'block' : 'none';
  }
  if (!dropdown) return;

  let html = `
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;padding-bottom:8px;border-bottom:1px solid rgba(255,255,255,0.1)">
      <strong style="font-size:0.95rem;color:#fff">Notifications
        ${unreadCount > 0 ? `<span style="background:#ff4757;color:#fff;border-radius:10px;padding:1px 7px;font-size:0.72rem;margin-left:6px">${unreadCount}</span>` : ''}
      </strong>
      ${unreadCount > 0 ? `<button id="bell-mark-all-btn" style="background:none;border:none;color:#a78bfa;cursor:pointer;font-size:0.8rem;padding:0">Mark all read</button>` : ''}
    </div>
  `;

  if (notifications.length === 0) {
    html += `<div style="text-align:center;padding:24px 12px;color:#666;font-size:0.85rem">
      <div style="font-size:2rem;margin-bottom:8px">🔕</div>
      No notifications yet
    </div>`;
  } else {
    html += `<div style="display:flex;flex-direction:column;gap:6px">`;
    notifications.slice(0, 15).forEach(n => {
      const bg     = n.is_read ? 'rgba(255,255,255,0.03)' : 'rgba(167,139,250,0.1)';
      const border = n.is_read ? 'transparent' : (TYPE_COLOR[n.type] || '#a78bfa');
      const icon   = TYPE_ICON[n.type] || '🔔';
      html += `
        <div class="notif-item" data-id="${n.id}" style="background:${bg};border-left:3px solid ${border};padding:9px 10px;border-radius:7px;font-size:0.83rem;cursor:pointer;transition:background 0.2s">
          <div style="display:flex;align-items:flex-start;gap:7px">
            <span style="font-size:1rem;flex-shrink:0">${icon}</span>
            <div style="flex:1;min-width:0">
              <div style="font-weight:600;color:${n.is_read ? '#ccc' : '#fff'};margin-bottom:2px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${n.title}</div>
              <div style="color:#9ca3af;font-size:0.78rem;margin-bottom:3px;line-height:1.3">${n.message}</div>
              <div style="color:#6b7280;font-size:0.73rem">${timeAgo(n.created_at)}</div>
            </div>
            ${!n.is_read ? `<span style="width:7px;height:7px;background:${TYPE_COLOR[n.type] || '#a78bfa'};border-radius:50%;flex-shrink:0;margin-top:4px"></span>` : ''}
          </div>
        </div>`;
    });
    html += `</div>`;
    if (notifications.length > 15) {
      html += `<div style="text-align:center;margin-top:8px;color:#a78bfa;font-size:0.8rem">${notifications.length - 15} more notifications</div>`;
    }
  }

  dropdown.innerHTML = html;

  // Bind mark-all
  const markAllBtn = document.getElementById('bell-mark-all-btn');
  if (markAllBtn) {
    markAllBtn.addEventListener('click', async (e) => {
      e.stopPropagation();
      await markAllRead();
      refreshAll();
    });
  }

  // Bind individual read
  dropdown.querySelectorAll('.notif-item').forEach(item => {
    item.addEventListener('click', async (e) => {
      e.stopPropagation();
      if (!item.dataset.id) return;
      await markOneRead(item.dataset.id);
      refreshAll();
    });
  });
}

// ─── Render full-page notification section ───────────────────────────────────
function renderSection(notifications, unreadCount) {
  // Client dashboard sidebar nav badge
  const navBadge = document.getElementById('notif-nav-badge');
  if (navBadge) {
    if (unreadCount > 0) {
      navBadge.textContent = unreadCount > 99 ? '99+' : unreadCount;
      navBadge.style.display = 'inline-flex';
    } else {
      navBadge.style.display = 'none';
    }
  }

  const listEl = document.getElementById('notif-section-list');
  if (!listEl) return;

  if (notifications.length === 0) {
    listEl.innerHTML = `
      <div style="text-align:center;padding:60px 24px;color:#6b7280">
        <div style="font-size:3.5rem;margin-bottom:16px">🔕</div>
        <div style="font-size:1.1rem;font-weight:600;color:#9ca3af;margin-bottom:8px">No notifications yet</div>
        <div style="font-size:0.875rem">You'll see updates here when there's project activity.</div>
      </div>`;
    return;
  }

  let html = `<div style="display:flex;flex-direction:column;gap:10px">`;
  notifications.forEach(n => {
    const icon   = TYPE_ICON[n.type]  || '🔔';
    const color  = TYPE_COLOR[n.type] || '#6b7280';
    const bg     = n.is_read ? 'var(--panel-bg, rgba(255,255,255,0.04))' : 'rgba(167,139,250,0.07)';
    const border = n.is_read ? '1px solid rgba(255,255,255,0.07)' : `1px solid ${color}40`;

    html += `
      <div class="notif-section-item" data-id="${n.id}" style="
        background:${bg};
        border:${border};
        border-radius:12px;
        padding:14px 16px;
        display:flex;
        gap:14px;
        align-items:flex-start;
        cursor:pointer;
        transition:background 0.2s;
        ${!n.is_read ? `box-shadow:0 0 0 1px ${color}30` : ''}
      ">
        <div style="
          width:40px;height:40px;border-radius:10px;
          background:${color}22;
          display:flex;align-items:center;justify-content:center;
          font-size:1.2rem;flex-shrink:0;
        ">${icon}</div>
        <div style="flex:1;min-width:0">
          <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:8px;margin-bottom:4px">
            <div style="font-weight:${n.is_read ? '500' : '700'};color:${n.is_read ? '#9ca3af' : '#f3f4f6'};font-size:0.9rem">${n.title}</div>
            <div style="font-size:0.75rem;color:#6b7280;flex-shrink:0;margin-top:1px">${timeAgo(n.created_at)}</div>
          </div>
          <div style="font-size:0.83rem;color:#9ca3af;line-height:1.4">${n.message}</div>
        </div>
        ${!n.is_read ? `<span style="width:9px;height:9px;background:${color};border-radius:50%;flex-shrink:0;margin-top:6px"></span>` : ''}
      </div>`;
  });
  html += `</div>`;
  listEl.innerHTML = html;

  // Bind item click to mark read
  listEl.querySelectorAll('.notif-section-item').forEach(item => {
    item.addEventListener('click', async () => {
      await markOneRead(item.dataset.id);
      refreshAll();
    });
  });

  // Bind "Mark All Read" button in section header
  const readAllBtn = document.getElementById('notif-read-all');
  if (readAllBtn && !readAllBtn._bound) {
    readAllBtn._bound = true;
    readAllBtn.addEventListener('click', async () => {
      await markAllRead();
      refreshAll();
    });
  }
}

// ─── Master refresh (fetches + updates everything) ───────────────────────────
let _dropdown = null;
let _dot = null;

async function refreshAll() {
  const data = await fetchNotifications();
  if (!data) return;

  const { notifications = [], unread_count = 0 } = data;

  // Update bell dot
  const dot = document.getElementById('notif-dot') || _dot;
  if (dot) dot.style.display = unread_count > 0 ? 'block' : 'none';

  // Update dropdown if visible
  if (_dropdown) {
    renderDropdown(_dropdown, notifications, unread_count, dot);
  }

  // Update full section list
  renderSection(notifications, unread_count);
}
window.refreshAll = refreshAll;

// ─── Initialize bell dropdown ────────────────────────────────────────────────
function initBellDropdown() {
  const bell = document.getElementById('notif-bell');
  if (!bell) return;

  // Create dropdown
  let dropdown = document.getElementById('notif-dropdown');
  if (!dropdown) {
    dropdown = document.createElement('div');
    dropdown.id = 'notif-dropdown';
    Object.assign(dropdown.style, {
      display:       'none',
      position:      'absolute',
      top:           '52px',
      right:         '0',
      width:         '320px',
      maxHeight:     '420px',
      overflowY:     'auto',
      background:    'rgba(15, 15, 25, 0.97)',
      backdropFilter:'blur(18px)',
      border:        '1px solid rgba(255,255,255,0.12)',
      borderRadius:  '14px',
      boxShadow:     '0 16px 48px rgba(0,0,0,0.7)',
      zIndex:        '9999',
      padding:       '14px',
      color:         '#e0e0e0',
      fontFamily:    'Inter, sans-serif',
    });
    // Ensure parent has position:relative
    const parent = bell.closest('.topbar-notif, header, [style]') || bell.parentElement;
    parent.style.position = 'relative';
    parent.appendChild(dropdown);
  }

  _dropdown = dropdown;
  _dot = document.getElementById('notif-dot');

  // Initial load
  fetchNotifications().then(data => {
    if (!data) return;
    const { notifications = [], unread_count = 0 } = data;
    renderDropdown(dropdown, notifications, unread_count, _dot);
    renderSection(notifications, unread_count);
  });

  // Toggle on bell click
  bell.addEventListener('click', async (e) => {
    e.stopPropagation();
    const isVisible = dropdown.style.display === 'block';
    dropdown.style.display = isVisible ? 'none' : 'block';
    if (!isVisible) {
      await refreshAll();
    }
  });

  // Close on outside click
  document.addEventListener('click', (e) => {
    if (dropdown && !dropdown.contains(e.target) && !bell.contains(e.target)) {
      dropdown.style.display = 'none';
    }
  });
}

// ─── Initialize section read-all button ──────────────────────────────────────
function initSectionReadAll() {
  // Client dashboard uses id="notif-section-read-all" which triggers notif-read-all click
  // We bind the actual logic here
  const readAllBtn = document.getElementById('notif-read-all');
  if (readAllBtn) {
    readAllBtn.addEventListener('click', async () => {
      await markAllRead();
      await refreshAll();
    });
  }
  const sectionBtn = document.getElementById('notif-section-read-all');
  if (sectionBtn && sectionBtn !== readAllBtn) {
    sectionBtn.addEventListener('click', async () => {
      await markAllRead();
      await refreshAll();
    });
  }
}

// ─── Boot ────────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  initBellDropdown();
  initSectionReadAll();

  // Auto-refresh every 60 seconds
  setInterval(refreshAll, 60_000);
});
