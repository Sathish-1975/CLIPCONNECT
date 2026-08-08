/**
 * ============================================================
 * ClipConnect — editor-dashboard.js
 * ============================================================
 * Powers the full editor dashboard:
 *  - Auth guard (editor role only)
 *  - Sidebar section switching
 *  - Load dashboard data from API
 *  - Profile completion ring animation
 *  - Availability toggle (3 states)
 *  - Earnings chart (CSS bars)
 *  - Analytics ring animations
 *  - Requests, Projects, Reviews sections
 * ============================================================
 */
'use strict';

/* ── Config ─────────────────────────────────────────────── */
const API     = 'http://localhost:5000/api';
const UPLOADS = 'http://localhost:5000/uploads';

/* ── State ──────────────────────────────────────────────── */
let dashData        = null;
let currentAvailability = 'available';

/* ── Auth helpers ───────────────────────────────────────── */
const getToken = () => localStorage.getItem('cc_token');
const getUser  = () => { try { return JSON.parse(localStorage.getItem('cc_user')); } catch { return null; } };
const authH    = () => ({ 'Authorization': `Bearer ${getToken()}`, 'Content-Type': 'application/json' });

function authGuard() {
  const token = getToken();
  const user  = getUser();
  if (!token || !user) { window.location.href = 'login.html?redirect=editor-dashboard.html'; return false; }
  if (user.role !== 'editor') {
    toast('This dashboard is for editors only.', 'error');
    setTimeout(() => window.location.href = 'index.html', 2000);
    return false;
  }
  return true;
}

/* ── Toast ──────────────────────────────────────────────── */
function toast(msg, type = 'success') {
  const el = document.getElementById('toast');
  if (!el) return;
  el.textContent = msg;
  el.className   = `toast ${type} show`;
  setTimeout(() => el.classList.remove('show'), 3500);
}

/* ── Sidebar navigation ─────────────────────────────────── */
function initSidebar() {
  const btns     = document.querySelectorAll('.nav-btn[data-section]');
  const sections = document.querySelectorAll('.section');
  const title    = document.getElementById('topbar-title');

  function activate(id) {
    btns.forEach(b => b.classList.toggle('active', b.dataset.section === id));
    sections.forEach(s => s.classList.toggle('active', s.id === `sec-${id}`));
    if (title) {
      const lbl = document.querySelector(`.nav-btn[data-section="${id}"] .nav-lbl`);
      title.textContent = lbl ? lbl.textContent : 'Dashboard';
    }
    closeMobileSidebar();
    // Lazy-load
    if (id === 'requests')  renderRequests();
    if (id === 'projects')  renderProjects();
    if (id === 'saved')     loadSavedProjects();
    if (id === 'earnings')  animateEarningsChart();
    if (id === 'reviews')   renderReviews();
    if (id === 'analytics') animateAnalytics();
  }

  btns.forEach(b => b.addEventListener('click', () => activate(b.dataset.section)));

  const hash = window.location.hash.replace('#', '');
  activate(hash && document.getElementById(`sec-${hash}`) ? hash : 'overview');
}

/* ── Mobile sidebar ─────────────────────────────────────── */
function initMobileSidebar() {
  const sidebar  = document.getElementById('sidebar');
  const overlay  = document.getElementById('sidebar-overlay');
  const menuBtn  = document.getElementById('topbar-menu');
  menuBtn?.addEventListener('click', () => {
    sidebar.classList.add('open');
    overlay.classList.add('visible');
  });
  overlay?.addEventListener('click', closeMobileSidebar);
}
function closeMobileSidebar() {
  document.getElementById('sidebar')?.classList.remove('open');
  document.getElementById('sidebar-overlay')?.classList.remove('visible');
}

/* ── Load dashboard data ─────────────────────────────────── */
async function loadDashboard() {
  try {
    const res  = await fetch(`${API}/users/me/editor-dashboard`, {
      headers: { 'Authorization': `Bearer ${getToken()}` }
    });
    const data = await res.json();
    if (!data.success) { toast('Could not load dashboard data.', 'error'); return; }
    dashData = data.data;
    currentAvailability = dashData.profile.availability_status || 'available';
    renderAll(dashData);
  } catch (e) {
    console.error(e);
    toast('Network error — is the Flask server running?', 'error');
  }
}

/* ── Render everything ───────────────────────────────────── */
function renderAll(d) {
  renderWelcome(d);
  renderCompletion(d.completion);
  renderStats(d.stats);
  renderAvailabilityUI(d.profile.availability_status);
  renderProfileSection(d);
  animateEarningsChart(d.analytics?.earnings_chart || []);
  animateAnalytics(d.analytics);
}

/* Welcome card */
function renderWelcome(d) {
  setTxt('welcome-greeting', d.welcome_message);
  const since = d.user.member_since ? `Member since ${fmtDate(d.user.member_since)}` : 'Welcome back!';
  setTxt('welcome-sub', since);
  setTxt('w-stat-rating',   (d.stats.avg_rating || 0).toFixed(1));
  setTxt('w-stat-projects', d.stats.completed_projects || 0);
  setTxt('w-stat-reviews',  d.stats.total_reviews || 0);

  // Avatars
  const photo = d.profile.profile_photo;
  const name  = d.user.full_name;
  ['sidebar-avatar', 'topbar-avatar', 'profile-avatar'].forEach(id => {
    const el = document.getElementById(id);
    if (!el) return;
    if (photo) el.innerHTML = `<img src="${UPLOADS}/avatars/${photo}" alt="${esc(name)}">`;
    else       el.textContent = initials(name);
  });

  setTxt('sidebar-name',    name);
  setTxt('sidebar-handle', d.profile.username ? `@${d.profile.username}` : 'Set your username');
}

/* Profile completion ring */
function renderCompletion(c) {
  const pct = c?.pct || 0;

  setTxt('comp-pct-ring',  `${pct}%`);
  setTxt('comp-pct-bar',   `${pct}%`);

  // SVG ring: circumference = 2πr = 2π×35 ≈ 220
  const circumference = 220;
  const offset = circumference - (pct / 100) * circumference;
  requestAnimationFrame(() => {
    const fill = document.getElementById('ring-fill');
    if (fill) fill.style.strokeDashoffset = offset;
    const bar = document.getElementById('comp-bar-fill');
    if (bar) bar.style.width = `${pct}%`;
  });

  // Colour ring label
  const color = pct >= 80 ? '#10B981' : pct >= 50 ? '#F59E0B' : '#EF4444';
  document.getElementById('comp-pct-ring')?.style.setProperty('color', color);

  const missingEl = document.getElementById('comp-missing');
  if (missingEl) {
    const missing = c?.missing || [];
    if (!missing.length) {
      missingEl.innerHTML = `<span class="completion-done">✓ Profile fully complete!</span>`;
    } else {
      missingEl.innerHTML = missing.map(m => `<span class="missing-tag">${esc(m)}</span>`).join('');
    }
  }

  setTxt('comp-score', `${c?.score || 0}/${c?.total || 16} items complete`);
}

/* Stat cards */
function renderStats(s) {
  setTxt('stat-requests',   s.incoming_requests);
  setTxt('stat-active',     s.active_projects);
  setTxt('stat-completed',  s.completed_projects);
  setTxt('stat-earnings',   fmtINR(s.monthly_earnings));
  setTxt('stat-pending',    fmtINR(s.pending_payments));
  setTxt('stat-rating',     (s.avg_rating || 0).toFixed(1));
  setTxt('stat-reviews',    s.total_reviews);
  setTxt('stat-total-earn', fmtINR(s.total_earnings));
}

/* Availability UI */
function renderAvailabilityUI(status) {
  currentAvailability = status || 'available';

  // Topbar toggle buttons
  ['available', 'busy', 'on_vacation'].forEach(s => {
    const btn = document.getElementById(`avail-${s}`);
    if (!btn) return;
    btn.className = `avail-toggle-btn${s === currentAvailability ? ` active-${s.replace('_','-')}` : ''}`;
  });

  // Sidebar pill
  const pill = document.getElementById('avail-pill');
  if (pill) {
    const labels = { available: '🟢 Available', busy: '🟡 Busy', on_vacation: '⚪ On Vacation' };
    const cls    = { available: 'avail-pill--available', busy: 'avail-pill--busy', on_vacation: 'avail-pill--vacation' };
    pill.textContent = labels[currentAvailability] || 'Available';
    pill.className   = `avail-pill ${cls[currentAvailability] || ''}`;
  }

  // Overview section buttons
  ['available', 'busy', 'on_vacation'].forEach(s => {
    const btn = document.getElementById(`avail-opt-${s}`);
    if (!btn) return;
    const clsMap = { available: 'sel-available', busy: 'sel-busy', on_vacation: 'sel-vacation' };
    btn.className = `avail-opt${s === currentAvailability ? ` ${clsMap[s]}` : ''}`;
  });
}

/* Profile section */
function renderProfileSection(d) {
  const p = d.profile;
  const u = d.user;

  setTxt('profile-name',    u.full_name);
  setTxt('profile-handle', p.username ? `@${p.username}` : '—');
  setTxt('profile-tagline', p.tagline || 'Add a professional tagline');
  setTxt('profile-exp',    p.experience_years ? `${p.experience_years} years experience` : '—');
  setTxt('profile-loc',    [p.city, p.country].filter(Boolean).join(', ') || '—');
  setTxt('profile-rate',   p.hourly_rate ? `₹${Number(p.hourly_rate).toLocaleString('en-IN')}/hr` : 'Not set');
  setTxt('profile-resp',   p.response_time || 'Within 24 hours');
  setTxt('profile-cat',    p.category ? p.category.replace(/_/g, ' ') : '—');
  setTxt('profile-avail',  { available: 'Available', busy: 'Busy', on_vacation: 'On Vacation' }[p.availability_status] || '—');
  setTxt('profile-port',   `${p.portfolio_images} images · ${p.portfolio_videos} videos`);

  // Skills chips
  const chips = document.getElementById('profile-skills');
  if (chips) {
    const skills = p.skills || [];
    chips.innerHTML = skills.length
      ? skills.map(s => `<span class="skill-chip">${esc(s)}</span>`).join('')
      : `<span style="color:#475569;font-size:.8rem">No skills added yet</span>`;
  }

  // Verified badge
  const badge = document.getElementById('profile-verified');
  if (badge) badge.style.display = p.is_verified ? 'inline-flex' : 'none';
}

/* Earnings chart */
function animateEarningsChart(chartData) {
  const data = chartData || dashData?.analytics?.earnings_chart || [];
  const container = document.getElementById('earnings-chart');
  if (!container) return;

  const maxVal = Math.max(...data.map(d => d.earnings), 1);

  container.innerHTML = data.map(d => {
    const pct = maxVal > 0 ? Math.max((d.earnings / maxVal) * 100, 3) : 3;
    const isEmpty = d.earnings === 0;
    return `
      <div class="chart-bar-wrap">
        <div class="chart-bar ${isEmpty ? 'empty' : ''}"
             style="height:0%;transition:height .7s ease"
             data-target="${pct}%"
             title="₹${Number(d.earnings).toLocaleString('en-IN')}">
        </div>
        <div class="chart-label">${d.month}</div>
      </div>`;
  }).join('');

  // Animate bars
  setTimeout(() => {
    container.querySelectorAll('.chart-bar').forEach(bar => {
      bar.style.height = bar.dataset.target;
    });
  }, 100);

  // Update totals
  const monthly = dashData?.stats?.monthly_earnings || 0;
  const total   = dashData?.stats?.total_earnings || 0;
  const pending = dashData?.stats?.pending_payments || 0;

  setTxt('earn-monthly', fmtINR(monthly));
  setTxt('earn-total',   fmtINR(total));
  setTxt('earn-pending', fmtINR(pending));
}

/* Analytics arc charts */
function animateAnalytics(analytics) {
  const a = analytics || dashData?.analytics || {};

  const metrics = [
    { id: 'arc-response',    val: a.response_rate    || 100, color: '#0EA5E9', label: `${a.response_rate || 100}%` },
    { id: 'arc-acceptance',  val: a.acceptance_rate  || 100, color: '#10B981', label: `${a.acceptance_rate || 100}%` },
    { id: 'arc-delivery',    val: a.on_time_delivery || 100, color: '#8B5CF6', label: `${a.on_time_delivery || 100}%` },
    { id: 'arc-completion',  val: a.profile_completion || 0, color: '#F59E0B', label: `${a.profile_completion || 0}%` },
  ];

  // SVG arc circumference = 2π×27 ≈ 169.6
  const C = 169.6;

  metrics.forEach(m => {
    const fillEl = document.getElementById(`${m.id}-fill`);
    const textEl = document.getElementById(`${m.id}-text`);
    if (fillEl) {
      fillEl.style.stroke = m.color;
      setTimeout(() => {
        fillEl.style.strokeDashoffset = C - (m.val / 100) * C;
      }, 200);
    }
    if (textEl) {
      textEl.style.color = m.color;
      textEl.textContent = m.label;
    }
  });

  setTxt('analytics-views',   a.profile_views || 0);
  setTxt('analytics-repeat',  a.repeat_clients || 0);
}

/* Requests section */
function renderRequests() {
  const tbody = document.getElementById('requests-tbody');
  const empty = document.getElementById('requests-empty');
  if (!tbody) return;

  const requests = dashData?.recent_requests || [];
  if (!requests.length) {
    tbody.innerHTML = '';
    if (empty) empty.style.display = 'block';
    return;
  }
  if (empty) empty.style.display = 'none';
  tbody.innerHTML = requests.map((r, i) => `
    <tr>
      <td>#${String(i+1).padStart(3,'0')}</td>
      <td>
        <div style="font-weight:600;color:var(--text-1)">${esc(r.title)}</div>
        <div style="font-size:.75rem;color:var(--text-3)">${esc(r.client_name)}</div>
      </td>
      <td>${esc(r.category || '—')}</td>
      <td>${fmtINR(r.budget || 0)}</td>
      <td><span class="badge badge--new"><span class="badge__dot"></span>New</span></td>
      <td>${timeAgo(r.created_at)}</td>
      <td>
        <div style="display:flex;gap:6px">
          <button class="btn btn-success btn-sm" onclick="acceptRequest(${r.id})">Accept</button>
          <button class="btn btn-danger btn-sm" onclick="declineRequest(${r.id})">Decline</button>
        </div>
      </td>
    </tr>`).join('');
}

/* Projects section */
function renderProjects() {
  const tbody = document.getElementById('projects-tbody');
  const empty = document.getElementById('projects-empty');
  if (!tbody) return;

  const projects = dashData?.recent_projects || [];
  if (!projects.length) {
    tbody.innerHTML = '';
    if (empty) empty.style.display = 'block';
    return;
  }
  if (empty) empty.style.display = 'none';
  tbody.innerHTML = projects.map(p => `
    <tr>
      <td><div style="font-weight:600;color:var(--text-1)">${esc(p.title)}</div></td>
      <td>${esc(p.client_name)}</td>
      <td><span class="badge badge--${p.status}"><span class="badge__dot"></span>${p.status}</span></td>
      <td>${p.due_date ? fmtDate(p.due_date) : '—'}</td>
      <td>${fmtINR(p.price || 0)}</td>
      <td><button class="btn btn-secondary btn-sm" onclick="openEditorProjectModal(${p.id})">View</button></td>
    </tr>`).join('');
}

/* Reviews section */
function renderReviews() {
  const stats = dashData?.stats || {};
  const reviews = dashData?.recent_reviews || [];

  setTxt('review-avg-big',   (stats.avg_rating || 0).toFixed(1));
  setTxt('review-total-cnt', `Based on ${stats.total_reviews || 0} reviews`);

  // Star display
  const starEl = document.getElementById('review-stars-big');
  if (starEl) {
    const full  = Math.floor(stats.avg_rating || 0);
    const half  = (stats.avg_rating || 0) % 1 >= 0.5;
    starEl.textContent = '★'.repeat(full) + (half ? '½' : '') + '☆'.repeat(Math.max(0, 5 - full - (half ? 1 : 0)));
  }

  // Review cards
  const list = document.getElementById('review-list');
  const emptyR = document.getElementById('reviews-empty');
  if (list) {
    if (!reviews.length) {
      list.innerHTML = '';
      if (emptyR) emptyR.style.display = 'block';
    } else {
      if (emptyR) emptyR.style.display = 'none';
      list.innerHTML = reviews.map(r => `
        <div class="review-card">
          <div class="review-card__header">
            <div class="review-card__avatar">${initials(r.client_name)}</div>
            <div>
              <div class="review-card__name">${esc(r.client_name)}</div>
              <div class="review-card__stars">${'★'.repeat(r.rating)}${'☆'.repeat(5-r.rating)}</div>
            </div>
            <div class="review-card__date">${timeAgo(r.created_at)}</div>
          </div>
          <div class="review-card__text">${esc(r.comment)}</div>
        </div>`).join('');
    }
  }
}

/* ── Availability toggle ─────────────────────────────────── */
function initAvailabilityToggle() {
  // All buttons that can change availability
  const allBtns = document.querySelectorAll('[data-avail]');
  allBtns.forEach(btn => {
    btn.addEventListener('click', () => setAvailability(btn.dataset.avail));
  });
}

async function setAvailability(status) {
  try {
    const res  = await fetch(`${API}/users/me/availability`, {
      method: 'PUT', headers: authH(),
      body: JSON.stringify({ availability_status: status })
    });
    const data = await res.json();
    if (data.success) {
      currentAvailability = status;
      renderAvailabilityUI(status);
      toast(`Status: ${data.data.label} ✓`);
    } else {
      toast(data.message || 'Could not update status.', 'error');
    }
  } catch { toast('Network error.', 'error'); }
}

/* ── Logout ──────────────────────────────────────────────── */
function initLogout() {
  document.getElementById('logout-btn')?.addEventListener('click', () => {
    if (!confirm('Log out of ClipConnect?')) return;
    localStorage.removeItem('cc_token');
    localStorage.removeItem('cc_user');
    window.location.href = 'login.html';
  });
}

/* ── Utility ─────────────────────────────────────────────── */
function setTxt(id, val)  { const e = document.getElementById(id); if (e) e.textContent = val ?? ''; }
function initials(name)   { return (name||'?').split(' ').map(w=>w[0]).join('').toUpperCase().slice(0,2); }
function esc(s)           { const d=document.createElement('div'); d.textContent=s; return d.innerHTML; }
function fmtINR(val)      { if (!val) return '₹0'; return '₹'+Number(val).toLocaleString('en-IN'); }
function fmtDate(iso)     { if (!iso) return '—'; return new Date(iso).toLocaleDateString('en-IN',{year:'numeric',month:'short',day:'numeric'}); }
function timeAgo(iso) {
  if (!iso) return '';
  const diff = (Date.now()-new Date(iso))/1000;
  if (diff < 60)      return 'just now';
  if (diff < 3600)    return `${Math.floor(diff/60)}m ago`;
  if (diff < 86400)   return `${Math.floor(diff/3600)}h ago`;
  if (diff < 2592000) return `${Math.floor(diff/86400)}d ago`;
  return fmtDate(iso);
}

/* ── Boot ────────────────────────────────────────────────── */
async function init() {
  if (!authGuard()) return;

  // Quick fill from cache
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
  initAvailabilityToggle();
  initLogout();

  await loadDashboard();

  // 15-second polling for real-time dashboard updates
  setInterval(async () => {
    await loadDashboard();
    if (typeof refreshAll === 'function') await refreshAll();
  }, 15000);
}

/* ── Saved Projects ─────────────────────────────────────── */
async function loadSavedProjects() {
  const tbody = document.getElementById('saved-tbody');
  const empty = document.getElementById('saved-empty');
  if (!tbody) return;

  try {
    const token = localStorage.getItem('cc_token') || localStorage.getItem('jwt_token') || localStorage.getItem('token');
    const res = await fetch(`${API}/projects/saved`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    const result = await res.json();

    if (!res.ok || !result.success || !result.data.projects || result.data.projects.length === 0) {
      tbody.innerHTML = '';
      if (empty) empty.style.display = 'block';
      return;
    }

    if (empty) empty.style.display = 'none';
    const projects = result.data.projects;

    tbody.innerHTML = projects.map(p => `
      <tr>
        <td>
          <a href="project-details.html?id=${p.id}" style="font-weight:600;color:var(--text-heading,#fff)">${esc(p.title || 'Untitled')}</a>
        </td>
        <td>${esc(p.category || 'General')}</td>
        <td>${p.budget ? '₹' + Number(p.budget).toLocaleString('en-IN') : 'Negotiable'}</td>
        <td>${fmtDate(p.saved_at)}</td>
        <td>
          <a href="project-details.html?id=${p.id}" class="btn btn-secondary btn-sm" style="text-decoration:none;margin-right:6px">View</a>
          <button class="btn btn-danger btn-sm" onclick="removeSavedProject(${p.id})">Remove</button>
        </td>
      </tr>
    `).join('');
  } catch (err) {
    console.error('Error loading saved projects:', err);
    if (empty) empty.style.display = 'block';
  }
}

async function removeSavedProject(projectId) {
  if (!confirm('Remove this project from your saved list?')) return;

  try {
    const token = localStorage.getItem('cc_token') || localStorage.getItem('jwt_token') || localStorage.getItem('token');
    const res = await fetch(`${API}/projects/${projectId}/save`, {
      method: 'DELETE',
      headers: { 'Authorization': `Bearer ${token}` }
    });
    const result = await res.json();

    if (res.ok && result.success) {
      toast('Project removed from saved list.', 'success');
      loadSavedProjects();
    } else {
      toast(result.message || 'Failed to remove saved project.', 'error');
    }
  } catch (err) {
    console.error('Error removing saved project:', err);
    toast('Server error removing saved project.', 'error');
  }
}
window.removeSavedProject = removeSavedProject;

async function acceptRequest(proposalId) {
  try {
    const res = await fetch(`${API}/hire/accept`, {
      method: 'PUT',
      headers: authH(),
      body: JSON.stringify({ proposal_id: proposalId })
    });
    const data = await res.json();
    if (data.success) {
      toast('Project accepted successfully!', 'success');
      await loadDashboard(); // refresh dashboard data
    } else {
      toast(data.message || 'Failed to accept request.', 'error');
    }
  } catch (err) {
    toast('Network error.', 'error');
  }
}
window.acceptRequest = acceptRequest;

async function declineRequest(proposalId) {
  if (!confirm('Are you sure you want to decline this request?')) return;
  try {
    const res = await fetch(`${API}/hire/reject`, {
      method: 'PUT',
      headers: authH(),
      body: JSON.stringify({ proposal_id: proposalId, reason: 'Declined by editor.' })
    });
    const data = await res.json();
    if (data.success) {
      toast('Request declined.', 'success');
      await loadDashboard(); // refresh dashboard data
    } else {
      toast(data.message || 'Failed to decline request.', 'error');
    }
  } catch (err) {
    toast('Network error.', 'error');
  }
}
window.declineRequest = declineRequest;

document.addEventListener('DOMContentLoaded', init);


/* ── Editor Project Modal ────────────────────────────────── */
let currentViewProjectId = null;

async function openEditorProjectModal(projectId) {
  currentViewProjectId = projectId;
  const modal = document.getElementById('editor-project-modal');
  if (!modal) return;
  
  // Find project data from dashData
  let project = dashData?.recent_projects?.find(p => p.id === projectId);
  if (!project) {
    toast('Project not found in cache. Fetching...', 'info');
    try {
      const res = await fetch(`${API}/projects/${projectId}`, { headers: authH() });
      const data = await res.json();
      if (data.success) {
        project = data.data.project;
      } else {
        toast('Failed to load project details.', 'error');
        return;
      }
    } catch (e) {
      toast('Network error fetching project.', 'error');
      return;
    }
  }

  setTxt('epm-title', project.title);
  setTxt('epm-client', project.client_name);
  setTxt('epm-budget', fmtINR(project.price || project.budget_max || project.budget_min || 0));
  setTxt('epm-deadline', project.due_date ? fmtDate(project.due_date) : (project.deadline ? fmtDate(project.deadline) : '—'));
  setTxt('epm-skills', project.required_skills?.join(', ') || '—');
  setTxt('epm-status', project.status.replace('_', ' ').toUpperCase());
  setTxt('epm-desc', project.description || 'No description provided.');

  const filesContainer = document.getElementById('epm-files');
  if (project.project_files && project.project_files.length > 0) {
    filesContainer.innerHTML = project.project_files.map(f => `<a href="${f.url}" target="_blank" style="color:#0ea5e9;">${esc(f.filename)}</a>`).join('<br>');
  } else {
    filesContainer.innerHTML = 'No files attached.';
  }

  // Handle Progress Dropdown
  const select = document.getElementById('epm-progress-select');
  if (['pending', 'accepted', 'in_progress'].includes(project.status.toLowerCase())) {
    select.value = project.status.toLowerCase();
    select.disabled = false;
    document.getElementById('epm-update-btn').disabled = false;
  } else {
    select.innerHTML = `<option value="${project.status.toLowerCase()}">${project.status}</option>`;
    select.disabled = true;
    document.getElementById('epm-update-btn').disabled = true;
  }

  // Handle Revision Section
  const revSection = document.getElementById('epm-revision-section');
  if (project.status === 'revision_requested') {
    revSection.style.display = 'block';
    // Fetch latest revision
    try {
      const revRes = await fetch(`${API}/projects/${projectId}/revisions`, { headers: authH() });
      const revData = await revRes.json();
      if (revData.success && revData.data.revisions.length > 0) {
        document.getElementById('epm-revision-notes').textContent = revData.data.revisions[0].comments;
      } else {
        document.getElementById('epm-revision-notes').textContent = 'Please check with client for details.';
      }
    } catch (e) {
      document.getElementById('epm-revision-notes').textContent = 'Could not load revision details.';
    }
  } else {
    revSection.style.display = 'none';
  }

  modal.style.display = 'flex';
}

function closeEditorProjectModal() {
  const modal = document.getElementById('editor-project-modal');
  if (modal) modal.style.display = 'none';
  currentViewProjectId = null;
}

document.getElementById('epm-update-btn')?.addEventListener('click', async () => {
  if (!currentViewProjectId) return;
  const status = document.getElementById('epm-progress-select').value;
  
  try {
    const res = await fetch(`${API}/projects/${currentViewProjectId}/editor-progress`, {
      method: 'PATCH',
      headers: authH(),
      body: JSON.stringify({ status })
    });
    const data = await res.json();
    if (data.success) {
      toast('Project progress updated!', 'success');
      closeEditorProjectModal();
      loadDashboard();
    } else {
      toast(data.message || 'Failed to update progress.', 'error');
    }
  } catch (e) {
    toast('Network error.', 'error');
  }
});

document.getElementById('epm-submit-btn')?.addEventListener('click', async () => {
  if (!currentViewProjectId) return;
  
  const fileInput = document.getElementById('epm-submit-file');
  const notes = document.getElementById('epm-submit-notes').value;
  
  const formData = new FormData();
  formData.append('notes', notes);
  if (fileInput.files.length > 0) {
    formData.append('file', fileInput.files[0]);
  }
  
  const btn = document.getElementById('epm-submit-btn');
  btn.textContent = 'Submitting...';
  btn.disabled = true;
  
  try {
    const token = getToken();
    const res = await fetch(`${API}/projects/${currentViewProjectId}/submit`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${token}` }, // Do not set Content-Type for FormData
      body: formData
    });
    const data = await res.json();
    if (data.success) {
      toast('Project submitted successfully!', 'success');
      closeEditorProjectModal();
      loadDashboard();
    } else {
      toast(data.message || 'Failed to submit project.', 'error');
    }
  } catch (e) {
    toast('Network error.', 'error');
  } finally {
    btn.textContent = 'Submit Project';
    btn.disabled = false;
  }
});
