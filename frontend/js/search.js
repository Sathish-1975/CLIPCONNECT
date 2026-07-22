/**
 * ============================================================
 * ClipConnect — search.js
 * Full search experience:
 *  - Autocomplete dropdown (name/skill/software/city/category)
 *  - Search type tabs (All / Name / Skills / Software / City / Category)
 *  - Keyword highlighting in results
 *  - Recent searches (localStorage)
 *  - Editor card rendering with matched field highlighting
 *  - Pagination + Sort
 * ============================================================
 */
'use strict';

const API     = 'http://localhost:5001/api';
const UPLOADS = 'http://localhost:5001/uploads';
const RECENT_KEY = 'cc_recent_searches';
const MAX_RECENT  = 8;

/* ── State ───────────────────────────────────────────────── */
const state = {
  query:       '',
  searchType:  'all',
  sort:        'rating',
  page:        1,
  perPage:     12,
  total:       0,
  totalPages:  1,
  loading:     false,
  ddOpen:      false,
  ddIndex:     -1,
  ddItems:     [],   // flat list for keyboard nav
};

/* ── Helpers ─────────────────────────────────────────────── */
function esc(s)        { const d=document.createElement('div'); d.textContent=s??''; return d.innerHTML; }
function initials(n)   { return (n||'?').split(' ').map(w=>w[0]).join('').toUpperCase().slice(0,2); }
function fmtINR(v)     { return v ? '₹'+Number(v).toLocaleString('en-IN') : null; }
function debounce(fn,ms){ let t; return (...a)=>{ clearTimeout(t); t=setTimeout(()=>fn(...a),ms); }; }
function highlight(text, query) {
  if (!query || !text) return esc(text || '');
  const safe = query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  return esc(text).replace(new RegExp(`(${safe})`, 'gi'), '<mark>$1</mark>');
}

const CATEGORY_LABELS = {
  youtube:'YouTube', reels:'Reels & Shorts', wedding:'Wedding',
  corporate:'Corporate', motion_graphics:'Motion Graphics',
  podcast:'Podcast', ecommerce:'E-Commerce', documentary:'Documentary', other:'Other',
};
const CATEGORY_ICONS = {
  youtube:'▶️', reels:'🎬', wedding:'💍', corporate:'💼',
  motion_graphics:'✨', podcast:'🎙️', ecommerce:'🛒', documentary:'🎥', other:'🎞️',
};

/* ── Toast ───────────────────────────────────────────────── */
function toast(msg, type='success') {
  const el = document.getElementById('toast');
  el.textContent = msg; el.className = `toast ${type} show`;
  clearTimeout(el._t); el._t = setTimeout(()=>el.classList.remove('show'), 3500);
}

/* ══════════════════════════════════════
   AUTOCOMPLETE DROPDOWN
══════════════════════════════════════ */
const suggestDebounced = debounce(fetchSuggestions, 280);

async function fetchSuggestions(q) {
  if (!q || q.length < 2) { closeDd(); return; }
  try {
    const res  = await fetch(`${API}/users/search/suggest?q=${encodeURIComponent(q)}&limit=5`);
    const data = await res.json();
    if (!data.success) { closeDd(); return; }
    renderSuggestions(data.data.groups, q);
  } catch { closeDd(); }
}

function renderSuggestions(groups, q) {
  const dd    = document.getElementById('suggestions-dd');
  const types = Object.keys(groups);

  if (!types.length) {
    dd.innerHTML = `<div class="suggestion-no-result">No suggestions for "<strong>${esc(q)}</strong>"</div>`;
    openDd(); state.ddItems = []; return;
  }

  const typeLabels = { name:'Editors', skill:'Skills', software:'Software', city:'Cities', category:'Categories' };
  const typeBadge  = { name:'badge-name', skill:'badge-skill', software:'badge-software', city:'badge-city', category:'badge-category' };
  const typeBadgeTxt = { name:'Name', skill:'Skill', software:'Software', city:'City', category:'Category' };

  let html = '';
  state.ddItems = [];

  for (const [type, items] of Object.entries(groups)) {
    if (!items.length) continue;
    html += `<div class="suggestion-group">
      <div class="suggestion-group-label">${typeLabels[type] || type}</div>`;
    items.forEach(item => {
      state.ddItems.push(item);
      const idx = state.ddItems.length - 1;
      html += `
        <div class="suggestion-item" data-idx="${idx}">
          <div class="suggestion-item__icon">${item.icon}</div>
          <div class="suggestion-item__body">
            <div class="suggestion-item__label">${highlight(item.label, q)}</div>
            <div class="suggestion-item__sub">${esc(item.sub || '')}</div>
          </div>
          <span class="suggestion-item__badge ${typeBadge[type]||''}">${typeBadgeTxt[type]||type}</span>
        </div>`;
    });
    html += '</div>';
  }

  html += `<div class="suggestion-view-all" id="dd-view-all">
    🔍 Search all results for "<strong>${esc(q)}</strong>"
  </div>`;

  dd.innerHTML = html;

  // Events
  dd.querySelectorAll('.suggestion-item').forEach(el => {
    el.addEventListener('mousedown', e => {
      e.preventDefault();
      const item = state.ddItems[el.dataset.idx];
      applySuggestion(item);
    });
  });
  document.getElementById('dd-view-all')?.addEventListener('mousedown', e => {
    e.preventDefault(); runSearch();
  });

  openDd();
}

function applySuggestion(item) {
  const input = document.getElementById('search-input');
  if (!input) return;

  // Set query and search type based on suggestion type
  input.value = item.value;
  state.query = item.value;

  const typeMap = { name:'name', skill:'skills', software:'software', city:'city', category:'category' };
  state.searchType = typeMap[item.type] || 'all';
  updateTabUI();
  closeDd();
  updateClearBtn();
  runSearch();
}

function openDd()  { document.getElementById('suggestions-dd').classList.add('open'); state.ddOpen = true; state.ddIndex = -1; }
function closeDd() { document.getElementById('suggestions-dd').classList.remove('open'); state.ddOpen = false; state.ddIndex = -1; }

function handleKeyboardNav(e) {
  if (!state.ddOpen) return;
  const items = document.querySelectorAll('.suggestion-item');
  if (e.key === 'ArrowDown') {
    e.preventDefault();
    state.ddIndex = Math.min(state.ddIndex + 1, items.length - 1);
    updateKbActive(items);
  } else if (e.key === 'ArrowUp') {
    e.preventDefault();
    state.ddIndex = Math.max(state.ddIndex - 1, 0);
    updateKbActive(items);
  } else if (e.key === 'Enter') {
    if (state.ddIndex >= 0 && state.ddItems[state.ddIndex]) {
      e.preventDefault();
      applySuggestion(state.ddItems[state.ddIndex]);
    } else {
      closeDd(); runSearch();
    }
  } else if (e.key === 'Escape') {
    closeDd();
  }
}

function updateKbActive(items) {
  items.forEach((el, i) => el.classList.toggle('keyboard-active', i === state.ddIndex));
}

/* ══════════════════════════════════════
   SEARCH EXECUTION
══════════════════════════════════════ */
async function runSearch(fromHint = null) {
  const input = document.getElementById('search-input');
  const q = fromHint ?? (input?.value.trim() || '');
  if (!q) return;

  state.query = q;
  if (input) input.value = q;
  updateClearBtn();
  closeDd();
  saveRecentSearch(q);
  showResultsArea();

  await fetchResults();
}

async function fetchResults() {
  if (state.loading) return;
  state.loading = true;
  showSkeletons();

  const params = new URLSearchParams({
    search:      state.query,
    search_type: state.searchType,
    sort:        state.sort,
    page:        state.page,
    per_page:    state.perPage,
  });

  try {
    const res  = await fetch(`${API}/users/editors?${params}`);
    const data = await res.json();
    if (!data.success) { renderEmpty(); state.loading = false; return; }

    const meta = data.meta?.pagination || {};
    state.total      = meta.total || 0;
    state.totalPages = meta.pages || 1;

    renderResults(data.data || []);
    renderPagination();
    updateResultsHeader();
  } catch (e) {
    console.error(e); renderEmpty();
  }
  state.loading = false;
}

/* ══════════════════════════════════════
   RENDER CARDS
══════════════════════════════════════ */
function renderResults(editors) {
  const grid = document.getElementById('results-grid');
  if (!editors.length) { renderEmpty(); return; }
  grid.innerHTML = editors.map(e => buildCard(e)).join('');

  // Events
  grid.querySelectorAll('.editor-card').forEach(card => {
    card.addEventListener('click', () => window.open(`editor-profile.html?id=${card.dataset.id}`, '_blank'));
  });
  grid.querySelectorAll('.btn-hire').forEach(btn => {
    btn.addEventListener('click', e => { e.stopPropagation(); toast(`Hiring flow coming soon! (${btn.dataset.name})`, 'info'); });
  });
}

function buildCard(e) {
  const q       = state.query.toLowerCase();
  const cat     = (e.category||'other').toLowerCase();
  const avail   = e.availability_status || 'available';
  const rating  = parseFloat(e.avg_rating||0).toFixed(1);
  const photo   = e.profile_photo ? `${UPLOADS}/avatars/${e.profile_photo}` : null;
  const banner  = e.cover_banner  ? `${UPLOADS}/banners/${e.cover_banner}`  : null;

  const skills   = (e.skills || []).slice(0, 5);
  const software = (e.software_used || []).slice(0, 3);

  const availCls = { available:'card-avail--available', busy:'card-avail--busy', on_vacation:'card-avail--vacation' }[avail] || 'card-avail--available';

  // Determine which field matched (for highlight)
  const matchedFields = [];
  if (e.full_name?.toLowerCase().includes(q))   matchedFields.push({ label: 'Name', cls: 'badge-name' });
  if ((e.skills||[]).some(s => s.toLowerCase().includes(q))) matchedFields.push({ label: 'Skill', cls: 'badge-skill' });
  if ((e.software_used||[]).some(s => s.toLowerCase().includes(q))) matchedFields.push({ label: 'Software', cls: 'badge-software' });
  if (e.city?.toLowerCase().includes(q))         matchedFields.push({ label: 'City', cls: 'badge-city' });
  if (e.category?.toLowerCase().includes(q))     matchedFields.push({ label: 'Category', cls: 'badge-category' });

  const matchBadges = state.searchType === 'all' && matchedFields.length
    ? matchedFields.map(m => `<span class="match-badge ${m.cls}">${m.label} match</span>`).join('')
    : '';

  return `
    <div class="editor-card" data-id="${e.user_id}">
      <div class="card-banner ${banner ? '' : `banner--${cat}`}">
        ${banner ? `<img src="${banner}" alt="" loading="lazy">` : ''}
        <div class="card-avail ${availCls}">
          <span class="card-avail__dot"></span>
          ${avail==='available' ? 'Available' : avail==='busy' ? 'Busy' : 'On Vacation'}
        </div>
      </div>

      <div class="card-profile">
        <div class="card-avatar">
          ${photo ? `<img src="${photo}" alt="${esc(e.full_name)}" loading="lazy">` : `<span>${initials(e.full_name)}</span>`}
        </div>
        <div class="card-name-block">
          <div class="card-name">${highlight(e.full_name, state.searchType==='name'||state.searchType==='all' ? q : '')}${matchBadges}</div>
          <div class="card-handle">${e.username ? `@${e.username}` : ''}</div>
        </div>
      </div>

      <div class="card-body">
        <div style="margin-bottom:8px">
          <span class="cat-badge cat--${cat}">
            ${CATEGORY_ICONS[cat]||'🎞️'} ${CATEGORY_LABELS[cat]||cat}
          </span>
        </div>
        <div class="card-tagline">${esc(e.tagline||'Professional video editor ready to bring your vision to life.')}</div>

        <div class="card-stats">
          <div class="card-rating">
            <span class="card-rating__star">★</span>
            <span class="card-rating__val">${rating}</span>
            <span class="card-rating__cnt">(${e.total_reviews||0})</span>
          </div>
          <div class="card-price">${e.hourly_rate ? `${fmtINR(e.hourly_rate)}<span>/hr</span>` : '<span>Contact</span>'}</div>
        </div>

        <div class="card-info">
          ${e.experience_years ? `<span class="info-pill">⏱ ${e.experience_years}yr exp</span>` : ''}
          ${e.city ? `<span class="info-pill${(state.searchType==='city'||state.searchType==='all') && e.city.toLowerCase().includes(q) ? ' matched' : ''}">📍 ${highlight(e.city, state.searchType==='city'||state.searchType==='all' ? q : '')}</span>` : ''}
          ${e.completed_projects ? `<span class="info-pill">✅ ${e.completed_projects} done</span>` : ''}
        </div>

        ${software.length ? `
        <div class="card-chips">
          ${software.map(s => `<span class="sw-chip${(state.searchType==='software'||state.searchType==='all') && s.toLowerCase().includes(q) ? ' matched' : ''}">${esc(s)}</span>`).join('')}
        </div>` : ''}

        ${skills.length ? `
        <div class="card-chips">
          ${skills.map(s => `<span class="skill-chip${(state.searchType==='skills'||state.searchType==='all') && s.toLowerCase().includes(q) ? ' matched' : ''}">${esc(s)}</span>`).join('')}
          ${(e.skills||[]).length > 5 ? `<span class="skill-chip" style="color:var(--text-3);background:rgba(255,255,255,.04)">+${e.skills.length-5}</span>` : ''}
        </div>` : ''}
      </div>

      <div class="card-divider"></div>
      <div class="card-actions">
        <button class="btn btn-primary btn-hire"
                data-id="${e.user_id}" data-name="${esc(e.full_name)}"
                ${avail!=='available' ? 'disabled style="opacity:.5;cursor:not-allowed"' : ''}>
          ${avail==='available' ? '⚡ Hire Now' : '🔒 Unavailable'}
        </button>
        <a href="editor-profile.html?id=${e.user_id}" class="btn btn-outline" onclick="event.stopPropagation()" target="_blank">View</a>
      </div>
    </div>`;
}

function showSkeletons() {
  const grid = document.getElementById('results-grid');
  grid.innerHTML = Array(6).fill(0).map(() => `
    <div style="background:#0E0E1A;border:1px solid rgba(255,255,255,.07);border-radius:20px;overflow:hidden">
      <div class="skel" style="height:80px;border-radius:0"></div>
      <div style="padding:12px 16px">
        <div class="skel" style="height:56px;width:56px;border-radius:50%;margin-top:-28px;margin-bottom:10px"></div>
        <div class="skel" style="height:14px;width:65%;margin-bottom:8px"></div>
        <div class="skel" style="height:11px;width:40%;margin-bottom:14px"></div>
        <div class="skel" style="height:10px;width:85%;margin-bottom:6px"></div>
        <div class="skel" style="height:10px;width:60%;margin-bottom:14px"></div>
        <div style="display:flex;gap:6px;margin-bottom:10px">
          <div class="skel" style="height:20px;width:70px;border-radius:20px"></div>
          <div class="skel" style="height:20px;width:80px;border-radius:20px"></div>
        </div>
        <div style="display:flex;gap:8px;margin-top:14px">
          <div class="skel" style="height:36px;flex:1;border-radius:10px"></div>
          <div class="skel" style="height:36px;flex:1;border-radius:10px"></div>
        </div>
      </div>
    </div>`).join('');
}

function renderEmpty() {
  document.getElementById('results-grid').innerHTML = `
    <div class="empty-state">
      <div class="empty-state__icon">🔍</div>
      <div class="empty-state__title">No editors found for "${esc(state.query)}"</div>
      <div class="empty-state__desc">Try a different keyword, check the spelling, or search by a different field.</div>
    </div>`;
}

function updateResultsHeader() {
  const typeLabels = { all:'across all fields', name:'by name', skills:'by skill', software:'by software', city:'by city', category:'by category' };
  const el = document.getElementById('results-title');
  const meta = document.getElementById('results-meta');
  if (el) el.innerHTML = `Results for <span style="color:var(--accent)">"${esc(state.query)}"</span>`;
  if (meta) meta.textContent = `${state.total} editor${state.total!==1?'s':''} found — searching ${typeLabels[state.searchType]||''}`;
}

function showResultsArea() {
  document.getElementById('search-hints').style.display = 'none';
  const ra = document.getElementById('results-area');
  ra.classList.add('visible');
}

/* ══════════════════════════════════════
   PAGINATION
══════════════════════════════════════ */
function renderPagination() {
  const wrap = document.getElementById('pagination');
  if (!wrap || state.totalPages <= 1) { if (wrap) wrap.innerHTML = ''; return; }
  const p = state.page, t = state.totalPages;
  let html = `<button class="page-btn" onclick="gotoPage(${p-1})" ${p===1?'disabled':''}>←</button>`;
  for (let i = 1; i <= t; i++) {
    if (i===1||i===t||(i>=p-1&&i<=p+1)) html += `<button class="page-btn ${i===p?'active':''}" onclick="gotoPage(${i})">${i}</button>`;
    else if (i===p-2||i===p+2) html += `<span style="color:var(--text-3);padding:0 4px">…</span>`;
  }
  html += `<button class="page-btn" onclick="gotoPage(${p+1})" ${p===t?'disabled':''}>→</button>`;
  wrap.innerHTML = html;
}

window.gotoPage = function(p) {
  if (!p||p<1||p>state.totalPages) return;
  state.page = p; fetchResults();
  window.scrollTo({ top: 0, behavior: 'smooth' });
};

/* ══════════════════════════════════════
   SEARCH TYPE TABS
══════════════════════════════════════ */
function initTabs() {
  document.querySelectorAll('.search-tab').forEach(tab => {
    tab.addEventListener('click', () => {
      state.searchType = tab.dataset.type;
      updateTabUI();
      if (state.query) { state.page = 1; fetchResults(); }
    });
  });
}

function updateTabUI() {
  document.querySelectorAll('.search-tab').forEach(t => t.classList.toggle('active', t.dataset.type === state.searchType));
}

/* ══════════════════════════════════════
   RECENT SEARCHES
══════════════════════════════════════ */
function getRecent() { try { return JSON.parse(localStorage.getItem(RECENT_KEY)) || []; } catch { return []; } }

function saveRecentSearch(q) {
  let recent = getRecent().filter(r => r !== q);
  recent.unshift(q);
  recent = recent.slice(0, MAX_RECENT);
  localStorage.setItem(RECENT_KEY, JSON.stringify(recent));
  renderRecent();
}

function renderRecent() {
  const wrap = document.getElementById('recent-chips');
  if (!wrap) return;
  const recent = getRecent();
  if (!recent.length) { document.getElementById('recent-section').style.display = 'none'; return; }
  document.getElementById('recent-section').style.display = 'block';
  wrap.innerHTML = recent.map(r => `
    <div class="hint-chip" onclick="runSearch('${esc(r)}')">
      <span>🕐</span>${esc(r)}
      <span class="hint-remove" onclick="event.stopPropagation();removeRecent('${esc(r)}')">✕</span>
    </div>`).join('');
}

window.removeRecent = function(q) {
  let recent = getRecent().filter(r => r !== q);
  localStorage.setItem(RECENT_KEY, JSON.stringify(recent));
  renderRecent();
};

/* ══════════════════════════════════════
   SORT
══════════════════════════════════════ */
function initSort() {
  document.getElementById('sort-select')?.addEventListener('change', function() {
    state.sort = this.value; state.page = 1; fetchResults();
  });
}

/* ══════════════════════════════════════
   CLEAR BUTTON
══════════════════════════════════════ */
function updateClearBtn() {
  const btn = document.getElementById('search-clear');
  if (btn) btn.classList.toggle('visible', !!state.query);
}

/* ══════════════════════════════════════
   URL params (deep-link)
══════════════════════════════════════ */
function readURLParams() {
  const p = new URLSearchParams(window.location.search);
  const q = p.get('q') || p.get('search') || '';
  const t = p.get('type') || 'all';
  if (q) { state.query = q; state.searchType = t; }
}

/* ══════════════════════════════════════
   POPULAR CATEGORY CARDS
══════════════════════════════════════ */
function initCategoryCards() {
  document.querySelectorAll('.cat-card').forEach(card => {
    card.addEventListener('click', () => {
      state.searchType = 'category';
      state.query = card.dataset.cat;
      const input = document.getElementById('search-input');
      if (input) input.value = CATEGORY_LABELS[card.dataset.cat] || card.dataset.cat;
      updateTabUI();
      updateClearBtn();
      runSearch(CATEGORY_LABELS[card.dataset.cat] || card.dataset.cat);
    });
  });
}

/* ══════════════════════════════════════
   NAV LINKS
══════════════════════════════════════ */
function initNav() {
  const user = (() => { try { return JSON.parse(localStorage.getItem('cc_user')); } catch { return null; } })();
  const navRight = document.getElementById('nav-right');
  if (!navRight) return;
  if (user) {
    const dash = user.role === 'editor' ? 'editor-dashboard.html' : 'dashboard.html';
    navRight.innerHTML = `<a href="${dash}" class="btn btn-primary btn-sm">My Dashboard</a>`;
  } else {
    navRight.innerHTML = `
      <a href="login.html"    class="btn btn-outline btn-sm">Log In</a>
      <a href="register.html" class="btn btn-primary  btn-sm">Join Free</a>`;
  }
}

/* ══════════════════════════════════════
   BOOT
══════════════════════════════════════ */
async function init() {
  initNav();
  initTabs();
  initSort();
  initCategoryCards();
  renderRecent();

  const input = document.getElementById('search-input');

  // Typing → suggest
  input?.addEventListener('input', () => {
    const q = input.value.trim();
    state.query = q;
    updateClearBtn();
    if (q.length >= 2) suggestDebounced(q);
    else closeDd();
  });

  // Keyboard nav in dropdown
  input?.addEventListener('keydown', handleKeyboardNav);
  input?.addEventListener('keydown', e => { if (e.key === 'Enter' && !state.ddOpen) runSearch(); });

  // Click outside → close dd
  document.addEventListener('click', e => {
    if (!e.target.closest('.search-bar-wrap')) closeDd();
  });

  // Clear button
  document.getElementById('search-clear')?.addEventListener('click', () => {
    if (input) input.value = '';
    state.query = ''; closeDd(); updateClearBtn();
    document.getElementById('search-hints').style.display = 'block';
    document.getElementById('results-area').classList.remove('visible');
  });

  // Read URL params and auto-search if query present
  readURLParams();
  if (state.query) {
    const input2 = document.getElementById('search-input');
    if (input2) input2.value = state.query;
    updateTabUI(); updateClearBtn();
    showResultsArea();
    await fetchResults();
  }
}

document.addEventListener('DOMContentLoaded', init);
