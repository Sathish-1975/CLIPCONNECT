/**
 * ============================================================
 * ClipConnect — dashboard.js
 * ============================================================
 * Powers the complete client dashboard:
 *   - Auth guard + session management
 *   - Sidebar navigation (section switching)
 *   - API calls: dashboard, favorites, notifications, account
 *   - Notification drawer (open/close, mark read, prefs)
 *   - Favorite editors (add via browse, remove)
 *   - Account settings form (name, email, password, bio...)
 *   - Avatar upload
 *   - Real-time UI updates without page reload
 * ============================================================
 */
'use strict';

/* ───────────────────────────────────────────
   Config
─────────────────────────────────────────── */
const API     = 'http://localhost:5001/api';
const UPLOADS = 'http://localhost:5001/uploads';

/* ───────────────────────────────────────────
   State
─────────────────────────────────────────── */
let dashData       = null;   // Full dashboard API response
let allNotifs      = [];     // Notifications list
let favoriteIds    = [];     // Array of editor user_ids
let browseEditors  = [];     // Editors from browse API

/* ───────────────────────────────────────────
   Auth helpers
─────────────────────────────────────────── */
const getToken = () => localStorage.getItem('cc_token');
const getUser  = () => { try { return JSON.parse(localStorage.getItem('cc_user')); } catch { return null; } };
const authH    = (extra = {}) => ({ 'Authorization': `Bearer ${getToken()}`, 'Content-Type': 'application/json', ...extra });

function authGuard() {
  const token = getToken();
  const user  = getUser();
  if (!token || !user) { window.location.href = 'login.html?redirect=dashboard.html'; return false; }
  if (user.role !== 'client') {
    toast('This dashboard is for clients only.', 'error');
    setTimeout(() => window.location.href = 'index.html', 2000);
    return false;
  }
  return true;
}

/* ───────────────────────────────────────────
   Toast
─────────────────────────────────────────── */
function toast(msg, type = 'success') {
  const el = document.getElementById('toast');
  if (!el) return;
  el.textContent = msg;
  el.className = `toast ${type} show`;
  setTimeout(() => el.classList.remove('show'), 3500);
}

/* ───────────────────────────────────────────
   Sidebar navigation
─────────────────────────────────────────── */
function initSidebar() {
  const items    = document.querySelectorAll('.nav-item[data-section]');
  const sections = document.querySelectorAll('.dash-section');
  const topTitle = document.getElementById('topbar-title');

  function activateSection(sectionId) {
    items.forEach(i => i.classList.toggle('active', i.dataset.section === sectionId));
    sections.forEach(s => s.classList.toggle('active', s.id === `section-${sectionId}`));
    if (topTitle) {
      const label = document.querySelector(`.nav-item[data-section="${sectionId}"] .nav-label`);
      topTitle.textContent = label ? label.textContent : 'Dashboard';
    }
    // Lazy-load section data
    if (sectionId === 'favorites')     loadFavorites();
    if (sectionId === 'browse')        loadBrowseEditors();
    if (sectionId === 'notifications') loadNotifications();
    // Close mobile sidebar
    closeMobileSidebar();
  }

  items.forEach(item => {
    item.addEventListener('click', () => activateSection(item.dataset.section));
  });

  // Restore last section from URL hash
  const hash = window.location.hash.replace('#', '');
  if (hash && document.getElementById(`section-${hash}`)) {
    activateSection(hash);
  } else {
    activateSection('overview');
  }
}

/* ───────────────────────────────────────────
   Mobile sidebar
─────────────────────────────────────────── */
function initMobileSidebar() {
  const sidebar = document.getElementById('sidebar');
  const overlay = document.getElementById('sidebar-overlay');
  const btn     = document.getElementById('topbar-menu-btn');

  btn?.addEventListener('click', () => {
    sidebar.classList.add('open');
    overlay.classList.add('visible');
  });
  overlay?.addEventListener('click', closeMobileSidebar);
}

function closeMobileSidebar() {
  document.getElementById('sidebar')?.classList.remove('open');
  document.getElementById('sidebar-overlay')?.classList.remove('visible');
}

/* ───────────────────────────────────────────
   Notification drawer
─────────────────────────────────────────── */
function initNotifDrawer() {
  const bell    = document.getElementById('notif-bell');
  const drawer  = document.getElementById('notif-drawer');
  const overlay = document.getElementById('drawer-overlay');
  const close   = document.getElementById('notif-close');
  const readAll = document.getElementById('notif-read-all');

  bell?.addEventListener('click', () => {
    drawer.classList.add('open');
    overlay.classList.add('visible');
    loadNotifications(true);  // load into drawer
  });

  close?.addEventListener('click', closeDrawer);
  overlay?.addEventListener('click', closeDrawer);

  readAll?.addEventListener('click', async () => {
    try {
      await fetch(`${API}/users/me/notifications/read-all`, {
        method: 'POST', headers: { 'Authorization': `Bearer ${getToken()}` }
      });
      allNotifs.forEach(n => n.read = true);
      renderDrawerNotifs();
      updateNotifBadge(0);
      toast('All notifications marked as read.');
    } catch { toast('Failed to mark read.', 'error'); }
  });
}

function closeDrawer() {
  document.getElementById('notif-drawer')?.classList.remove('open');
  document.getElementById('drawer-overlay')?.classList.remove('visible');
}

/* ───────────────────────────────────────────
   Data Loaders
─────────────────────────────────────────── */

async function loadDashboard() {
  try {
    const res  = await fetch(`${API}/users/me/dashboard`, { headers: { 'Authorization': `Bearer ${getToken()}` } });
    const data = await res.json();
    if (!data.success) { toast('Could not load dashboard.', 'error'); return; }
    dashData   = data.data;
    favoriteIds = (dashData.favorite_editors || []).map(e => e.user_id);
    renderDashboard(dashData);
  } catch (e) {
    console.error(e);
    toast('Network error. Is the server running?', 'error');
  }
}

async function loadNotifications(forDrawer = false) {
  try {
    const res  = await fetch(`${API}/users/me/notifications`, { headers: { 'Authorization': `Bearer ${getToken()}` } });
    const data = await res.json();
    if (!data.success) return;
    allNotifs = data.data.notifications || [];
    updateNotifBadge(data.data.unread_count || 0);
    if (forDrawer) {
      renderDrawerNotifs();
    } else {
      renderNotificationsSection();
    }
  } catch {}
}

async function loadFavorites() {
  const grid = document.getElementById('favorites-grid');
  if (!grid) return;
  grid.innerHTML = `<div class="skeleton" style="height:160px;border-radius:12px"></div>`.repeat(4);
  try {
    const res  = await fetch(`${API}/users/me/favorites`, { headers: { 'Authorization': `Bearer ${getToken()}` } });
    const data = await res.json();
    if (!data.success) return;
    const favs = data.data.favorites || [];
    favoriteIds = favs.map(f => f.user_id);
    renderFavoritesGrid(favs, grid);
  } catch { grid.innerHTML = `<p style="color:#475569">Failed to load favorites.</p>`; }
}

async function loadBrowseEditors() {
  const grid = document.getElementById('browse-grid');
  if (!grid) return;
  grid.innerHTML = `<div class="skeleton" style="height:180px;border-radius:12px"></div>`.repeat(6);
  try {
    const res  = await fetch(`${API}/users/editors?per_page=12&sort=rating`);
    const data = await res.json();
    if (!data.success) return;
    browseEditors = data.data || [];
    renderBrowseGrid(browseEditors, grid);
  } catch {}
}

/* ───────────────────────────────────────────
   Renderers
─────────────────────────────────────────── */

function renderDashboard(d) {
  // Welcome card
  setTxt('welcome-greeting',  d.welcome_message || 'Welcome back!');
  setTxt('welcome-subtitle',  `Member since ${fmtDate(d.user.member_since)}`);
  setTxt('stat-active',    d.stats.active_projects);
  setTxt('stat-completed', d.stats.completed_projects);
  setTxt('stat-pending',   d.stats.pending_requests);
  setTxt('stat-favorites', d.stats.favorite_editors);

  // Sidebar user
  setTxt('sidebar-name', d.user.full_name);
  const sAvatar = document.getElementById('sidebar-avatar');
  if (sAvatar) {
    if (d.user.profile_photo) {
      sAvatar.innerHTML = `<img src="${UPLOADS}/avatars/${d.user.profile_photo}" alt="">`;
    } else {
      sAvatar.textContent = initials(d.user.full_name);
    }
  }

  // Topbar avatar
  const tAvatar = document.getElementById('topbar-avatar');
  if (tAvatar) {
    if (d.user.profile_photo) {
      tAvatar.innerHTML = `<img src="${UPLOADS}/avatars/${d.user.profile_photo}" alt="">`;
    } else {
      tAvatar.textContent = initials(d.user.full_name);
    }
  }

  // Favorite editors on overview
  renderFavSnippets(d.favorite_editors || []);

  // Activity feed
  renderActivity(d.recent_activity || []);

  // Notification badge
  updateNotifBadge(d.unread_notifications || 0);

  // Pre-fill account settings
  prefillAccount(d.user);
}

function renderFavSnippets(editors) {
  const el = document.getElementById('fav-editors-overview');
  if (!el) return;
  if (!editors.length) {
    el.innerHTML = `
      <div class="empty-state">
        <div class="empty-state__icon">❤️</div>
        <div class="empty-state__title">No favorites yet</div>
        <div class="empty-state__desc">Browse editors and save your top picks here.</div>
        <button class="btn btn-primary btn-sm" onclick="gotoSection('browse')">Browse Editors</button>
      </div>`;
    return;
  }
  el.innerHTML = editors.slice(0, 4).map(e => buildEditorCard(e, true)).join('');
  attachRemoveFavHandlers(el);
}

function renderFavoritesGrid(editors, container) {
  if (!editors.length) {
    container.innerHTML = `
      <div class="empty-state" style="grid-column:1/-1">
        <div class="empty-state__icon">❤️</div>
        <div class="empty-state__title">No saved editors</div>
        <div class="empty-state__desc">Go to Browse to discover and save editors you love.</div>
        <button class="btn btn-primary" onclick="gotoSection('browse')">Browse Editors</button>
      </div>`;
    return;
  }
  container.innerHTML = editors.map(e => buildEditorCard(e, true)).join('');
  attachRemoveFavHandlers(container);
}

function renderBrowseGrid(editors, container) {
  if (!editors.length) {
    container.innerHTML = `<div class="empty-state" style="grid-column:1/-1"><div class="empty-state__icon">🔍</div><div class="empty-state__title">No editors found</div></div>`;
    return;
  }
  container.innerHTML = editors.map(e => buildEditorCard(e, false)).join('');
  attachAddFavHandlers(container);
}

function buildEditorCard(e, isFav) {
  const avgRating = Number(e.avg_rating || 0).toFixed(1);
  const rate      = e.hourly_rate ? `₹${Number(e.hourly_rate).toLocaleString('en-IN')}/hr` : 'Contact';
  const avail     = e.availability || e.availability_status || 'available';
  const availCls  = avail === 'available' ? 'status-badge--completed' : avail === 'busy' ? 'status-badge--pending' : 'status-badge--cancelled';
  const availLabel = { available:'Available', busy:'Busy', on_vacation:'On Vacation' }[avail] || avail;
  const photoUrl  = e.profile_photo ? `${UPLOADS}/avatars/${e.profile_photo}` : null;
  const isFaved   = favoriteIds.includes(e.user_id);

  return `
    <div class="editor-card" data-editor-id="${e.user_id}">
      <div class="editor-card__top">
        <div class="editor-card__avatar">
          ${photoUrl ? `<img src="${photoUrl}" alt="${e.full_name}">` : `<span>${initials(e.full_name)}</span>`}
        </div>
        <div class="editor-card__info">
          <div class="editor-card__name">${esc(e.full_name)}</div>
          <div class="editor-card__handle">${e.username ? '@'+e.username : ''}</div>
        </div>
        ${isFav
          ? `<button class="editor-card__remove remove-fav-btn" data-id="${e.user_id}" title="Remove">✕</button>`
          : `<button class="btn btn-sm ${isFaved ? 'btn-danger' : 'btn-secondary'} add-fav-btn" data-id="${e.user_id}" title="${isFaved ? 'Unfavorite' : 'Favorite'}" style="flex-shrink:0">
              ${isFaved ? '♥' : '♡'}
            </button>`
        }
      </div>
      ${e.tagline ? `<div class="editor-card__tagline">${esc(e.tagline)}</div>` : ''}
      <div class="editor-card__meta">
        <div class="editor-card__rating">⭐ ${avgRating} <span style="color:#64748B">(${e.total_reviews || 0})</span></div>
        <div class="editor-card__rate">${rate}</div>
      </div>
      <div style="margin-bottom:12px">
        <span class="status-badge ${availCls}">
          <span class="status-badge__dot"></span>${availLabel}
        </span>
        ${e.city ? `<span style="font-size:0.75rem;color:#475569;margin-left:8px">📍 ${esc(e.city)}</span>` : ''}
      </div>
      <div class="editor-card__actions">
        <a href="editor-profile.html?id=${e.user_id}" class="btn btn-secondary btn-sm" style="flex:1;justify-content:center">View Profile</a>
        <button class="btn btn-primary btn-sm" onclick="toast('Hiring flow coming soon!','info')">Hire</button>
      </div>
    </div>`;
}

function attachRemoveFavHandlers(container) {
  container.querySelectorAll('.remove-fav-btn').forEach(btn => {
    btn.addEventListener('click', async (e) => {
      e.stopPropagation();
      const editorId = parseInt(btn.dataset.id);
      await removeFavorite(editorId, btn.closest('.editor-card'));
    });
  });
}

function attachAddFavHandlers(container) {
  container.querySelectorAll('.add-fav-btn').forEach(btn => {
    btn.addEventListener('click', async (e) => {
      e.stopPropagation();
      const editorId = parseInt(btn.dataset.id);
      if (favoriteIds.includes(editorId)) {
        await removeFavoriteById(editorId, btn);
      } else {
        await addFavorite(editorId, btn);
      }
    });
  });
}

async function addFavorite(editorId, btn) {
  try {
    const res  = await fetch(`${API}/users/me/favorites/${editorId}`, {
      method: 'POST', headers: { 'Authorization': `Bearer ${getToken()}` }
    });
    const data = await res.json();
    if (data.success) {
      favoriteIds.push(editorId);
      if (btn) { btn.textContent = '♥'; btn.classList.replace('btn-secondary', 'btn-danger'); }
      toast('Added to favorites! ❤️');
      updateStatCard('stat-favorites', favoriteIds.length);
    } else {
      toast(data.message || 'Could not add to favorites.', 'error');
    }
  } catch { toast('Network error.', 'error'); }
}

async function removeFavorite(editorId, cardEl) {
  try {
    const res  = await fetch(`${API}/users/me/favorites/${editorId}`, {
      method: 'DELETE', headers: { 'Authorization': `Bearer ${getToken()}` }
    });
    const data = await res.json();
    if (data.success) {
      favoriteIds = favoriteIds.filter(id => id !== editorId);
      cardEl?.remove();
      toast('Removed from favorites.');
      updateStatCard('stat-favorites', favoriteIds.length);
    } else {
      toast(data.message || 'Could not remove.', 'error');
    }
  } catch { toast('Network error.', 'error'); }
}

async function removeFavoriteById(editorId, btn) {
  try {
    const res  = await fetch(`${API}/users/me/favorites/${editorId}`, {
      method: 'DELETE', headers: { 'Authorization': `Bearer ${getToken()}` }
    });
    const data = await res.json();
    if (data.success) {
      favoriteIds = favoriteIds.filter(id => id !== editorId);
      if (btn) { btn.textContent = '♡'; btn.classList.replace('btn-danger', 'btn-secondary'); }
      toast('Removed from favorites.');
      updateStatCard('stat-favorites', favoriteIds.length);
    }
  } catch {}
}

function renderActivity(activity) {
  const el = document.getElementById('activity-list');
  if (!el) return;
  if (!activity.length) {
    el.innerHTML = `
      <div class="empty-state">
        <div class="empty-state__icon">📋</div>
        <div class="empty-state__title">No activity yet</div>
        <div class="empty-state__desc">Your project activity will appear here once you start working with editors.</div>
        <button class="btn btn-primary btn-sm" onclick="gotoSection('browse')">Find an Editor</button>
      </div>`;
    return;
  }
  el.innerHTML = activity.map(a => `
    <div class="activity-item">
      <div class="activity-icon activity-icon--${a.type || 'project'}">${a.icon || '📌'}</div>
      <div class="activity-item__body">
        <div class="activity-item__title">${esc(a.title)}</div>
        <div class="activity-item__desc">${esc(a.description || '')}</div>
      </div>
      <div class="activity-item__time">${timeAgo(a.created_at)}</div>
    </div>`).join('');
}

/* ── Notifications ─────────────────────────────────────────── */

function renderDrawerNotifs() {
  const el = document.getElementById('drawer-notif-list');
  if (!el) return;
  if (!allNotifs.length) {
    el.innerHTML = `<div class="empty-state"><div class="empty-state__icon">🔔</div><div class="empty-state__title">All caught up!</div></div>`;
    return;
  }
  el.innerHTML = allNotifs.map(n => `
    <div class="notif-item ${n.read ? '' : 'unread'}" data-id="${n.id}">
      <div class="notif-item__icon">${notifIcon(n.type)}</div>
      <div class="notif-item__body">
        <div class="notif-item__title">${esc(n.title)}</div>
        <div class="notif-item__msg">${esc(n.message || '')}</div>
      </div>
      <div class="notif-item__time">${timeAgo(n.created_at)}</div>
    </div>`).join('');

  // Click → mark read
  el.querySelectorAll('.notif-item').forEach(item => {
    item.addEventListener('click', async () => {
      const id = item.dataset.id;
      if (!item.classList.contains('unread')) return;
      item.classList.remove('unread');
      await fetch(`${API}/users/me/notifications/${id}`, {
        method: 'PATCH', headers: { 'Authorization': `Bearer ${getToken()}` }
      });
      const unread = allNotifs.filter(n => !n.read).length - 1;
      updateNotifBadge(Math.max(0, unread));
    });
  });
}

function renderNotificationsSection() {
  const el = document.getElementById('notif-section-list');
  if (!el) return;
  if (!allNotifs.length) {
    el.innerHTML = `<div class="empty-state"><div class="empty-state__icon">🔔</div><div class="empty-state__title">No notifications</div></div>`;
    return;
  }
  el.innerHTML = allNotifs.map(n => `
    <div class="notif-item ${n.read ? '' : 'unread'}" data-id="${n.id}" style="padding:16px;border-radius:12px;background:var(--bg-card);border:1px solid var(--border);margin-bottom:10px">
      <div class="notif-item__icon">${notifIcon(n.type)}</div>
      <div class="notif-item__body">
        <div class="notif-item__title" style="font-size:0.92rem">${esc(n.title)}</div>
        <div class="notif-item__msg">${esc(n.message || '')}</div>
      </div>
      <div class="notif-item__time">${timeAgo(n.created_at)}</div>
    </div>`).join('');
}

function notifIcon(type) {
  const icons = { welcome: '🎉', project: '📁', complete: '✅', review: '⭐', message: '💬', favorite: '❤️', payment: '💳' };
  return icons[type] || '🔔';
}

/* ── Notification Prefs ─────────────────────────────────────── */

function initNotifPrefs() {
  ['notif-email', 'notif-projects', 'notif-messages'].forEach(id => {
    const toggle = document.getElementById(id);
    if (!toggle) return;
    toggle.addEventListener('change', async () => {
      try {
        await fetch(`${API}/users/me/notifications/prefs`, {
          method: 'PUT',
          headers: authH(),
          body: JSON.stringify({ [id.replace('-', '_')]: toggle.checked })
        });
        toast('Preferences saved.');
      } catch {}
    });
  });
}

/* ── Account Settings ───────────────────────────────────────── */

function prefillAccount(user) {
  setVal('acc-name',    user.full_name || '');
  setVal('acc-email',   user.email || '');
  // Avatar
  const circle = document.getElementById('acc-avatar-circle');
  if (circle) {
    if (user.profile_photo) {
      circle.innerHTML = `<img src="${UPLOADS}/avatars/${user.profile_photo}" alt="">`;
    } else {
      circle.textContent = initials(user.full_name);
    }
  }
}

function initAccountSettings() {
  // Save profile form
  document.getElementById('acc-save-btn')?.addEventListener('click', async () => {
    const btn = document.getElementById('acc-save-btn');
    btn.textContent = 'Saving...'; btn.disabled = true;

    const payload = {
      full_name: getVal('acc-name'),
      email:     getVal('acc-email'),
      phone:     getVal('acc-phone'),
      company:   getVal('acc-company'),
      bio:       getVal('acc-bio'),
      city:      getVal('acc-city'),
      country:   getVal('acc-country'),
      website:   getVal('acc-website'),
    };

    try {
      const res  = await fetch(`${API}/users/me/account`, { method: 'PUT', headers: authH(), body: JSON.stringify(payload) });
      const data = await res.json();
      if (data.success) {
        // Update local storage
        const user = getUser();
        if (user) { user.full_name = data.data.user.full_name; user.email = data.data.user.email; localStorage.setItem('cc_user', JSON.stringify(user)); }
        toast('Account settings saved! ✓');
        setTxt('sidebar-name', data.data.user.full_name);
      } else {
        toast(data.message || 'Save failed.', 'error');
      }
    } catch { toast('Network error.', 'error'); }
    finally  { btn.textContent = 'Save Changes'; btn.disabled = false; }
  });

  // Change password
  document.getElementById('pwd-save-btn')?.addEventListener('click', async () => {
    const btn = document.getElementById('pwd-save-btn');
    const cur = getVal('acc-cur-pwd');
    const nw  = getVal('acc-new-pwd');
    const cf  = getVal('acc-confirm-pwd');

    if (!cur || !nw) { toast('Please fill in both password fields.', 'error'); return; }
    if (nw !== cf)   { toast('New passwords do not match.', 'error'); return; }
    if (nw.length < 8) { toast('Password must be at least 8 characters.', 'error'); return; }

    btn.textContent = 'Changing...'; btn.disabled = true;
    try {
      const res  = await fetch(`${API}/users/me/account`, {
        method: 'PUT', headers: authH(),
        body: JSON.stringify({ current_password: cur, new_password: nw })
      });
      const data = await res.json();
      if (data.success) {
        toast('Password changed successfully!');
        setVal('acc-cur-pwd', ''); setVal('acc-new-pwd', ''); setVal('acc-confirm-pwd', '');
      } else {
        toast(data.message || 'Could not change password.', 'error');
      }
    } catch { toast('Network error.', 'error'); }
    finally  { btn.textContent = 'Change Password'; btn.disabled = false; }
  });

  // Avatar upload
  const avatarInput = document.getElementById('acc-avatar-input');
  avatarInput?.addEventListener('change', async () => {
    const file = avatarInput.files[0];
    if (!file) return;
    const fd = new FormData(); fd.append('avatar', file);
    try {
      const res  = await fetch(`${API}/users/me/client-avatar`, {
        method: 'POST', headers: { 'Authorization': `Bearer ${getToken()}` }, body: fd
      });
      const data = await res.json();
      if (data.success) {
        const url = `${UPLOADS}/avatars/${data.data.filename}`;
        document.getElementById('acc-avatar-circle').innerHTML = `<img src="${url}" alt="">`;
        document.getElementById('sidebar-avatar').innerHTML   = `<img src="${url}" alt="">`;
        document.getElementById('topbar-avatar').innerHTML    = `<img src="${url}" alt="">`;
        toast('Profile photo updated!');
      } else { toast(data.message || 'Upload failed.', 'error'); }
    } catch { toast('Upload failed.', 'error'); }
  });
}

/* ── Browse Editors Search ──────────────────────────────────── */

function initBrowseSearch() {
  const input  = document.getElementById('browse-search');
  const catSel = document.getElementById('browse-cat');
  const sortSel= document.getElementById('browse-sort');

  async function doSearch() {
    const grid = document.getElementById('browse-grid');
    if (!grid) return;
    const q    = input?.value?.trim() || '';
    const cat  = catSel?.value || '';
    const sort = sortSel?.value || 'rating';
    const params = new URLSearchParams({ per_page: 20, sort });
    if (q)   params.set('search', q);
    if (cat) params.set('category', cat);

    grid.innerHTML = `<div class="skeleton" style="height:180px;border-radius:12px"></div>`.repeat(6);
    try {
      const res  = await fetch(`${API}/users/editors?${params}`);
      const data = await res.json();
      browseEditors = data.data || [];
      renderBrowseGrid(browseEditors, grid);
    } catch {}
  }

  input?.addEventListener('input',  debounce(doSearch, 400));
  catSel?.addEventListener('change', doSearch);
  sortSel?.addEventListener('change', doSearch);
}

/* ── Projects tab ───────────────────────────────────────────── */

function renderProjectsSection() {
  const el = document.getElementById('projects-table-body');
  if (!el) return;
  // No orders yet — show beautiful empty state
  el.innerHTML = '';
  const wrap = document.getElementById('projects-empty');
  if (wrap) wrap.style.display = 'block';
}

/* ── Notification badge ─────────────────────────────────────── */

function updateNotifBadge(count) {
  const dot  = document.getElementById('notif-dot');
  const badge= document.getElementById('notif-nav-badge');
  if (dot)   dot.classList.toggle('visible', count > 0);
  if (badge) { badge.textContent = count > 99 ? '99+' : count; badge.style.display = count > 0 ? 'flex' : 'none'; }
}

function updateStatCard(id, val) {
  const el = document.getElementById(id);
  if (el) el.textContent = val;
}

/* ── Utility ─────────────────────────────────────────────────── */

function gotoSection(id) {
  const btn = document.querySelector(`.nav-item[data-section="${id}"]`);
  if (btn) btn.click();
}
window.gotoSection = gotoSection;

function setTxt(id, val) { const e = document.getElementById(id); if (e) e.textContent = val ?? ''; }
function setVal(id, val) { const e = document.getElementById(id); if (e) e.value = val ?? ''; }
function getVal(id)      { return document.getElementById(id)?.value?.trim() || ''; }
function initials(name)  { return (name || '?').split(' ').map(w => w[0]).join('').toUpperCase().slice(0,2); }
function esc(s)          { const d = document.createElement('div'); d.textContent = s; return d.innerHTML; }

function fmtDate(iso) {
  if (!iso) return 'recently';
  return new Date(iso).toLocaleDateString('en-IN', { year: 'numeric', month: 'short' });
}

function timeAgo(iso) {
  if (!iso) return '';
  const diff = (Date.now() - new Date(iso)) / 1000;
  if (diff < 60)      return 'just now';
  if (diff < 3600)    return `${Math.floor(diff/60)}m ago`;
  if (diff < 86400)   return `${Math.floor(diff/3600)}h ago`;
  if (diff < 2592000) return `${Math.floor(diff/86400)}d ago`;
  return fmtDate(iso);
}

function debounce(fn, delay) {
  let t; return (...args) => { clearTimeout(t); t = setTimeout(() => fn(...args), delay); };
}

/* ── Logout ──────────────────────────────────────────────────── */

function initLogout() {
  document.getElementById('logout-btn')?.addEventListener('click', () => {
    if (!confirm('Log out of ClipConnect?')) return;
    localStorage.removeItem('cc_token');
    localStorage.removeItem('cc_user');
    window.location.href = 'login.html';
  });
}

/* ───────────────────────────────────────────
   Boot
─────────────────────────────────────────── */
async function init() {
  if (!authGuard()) return;

  // Nav user quick fill from local cache while API loads
  const user = getUser();
  if (user) {
    setTxt('sidebar-name', user.full_name);
    const av = document.getElementById('topbar-avatar');
    if (av) av.textContent = initials(user.full_name);
    const sav = document.getElementById('sidebar-avatar');
    if (sav) sav.textContent = initials(user.full_name);
  }

  initSidebar();
  initMobileSidebar();
  initNotifDrawer();
  initAccountSettings();
  initBrowseSearch();
  initNotifPrefs();
  initLogout();

  // Load main data
  await loadDashboard();

  // Preload notifications badge
  await loadNotifications(false);

  // Render projects tab
  renderProjectsSection();
}

document.addEventListener('DOMContentLoaded', init);
