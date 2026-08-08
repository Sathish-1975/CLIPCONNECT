/**
 * ============================================================
 * ClipConnect — browse-editors.js
 * Full marketplace logic: filter, search, sort, paginate,
 * favorites, hire flow, editor cards.
 * ============================================================
 */
'use strict';

const API     = window.location.origin.includes(':5000') ? '/api' : 'http://localhost:5000/api';
const UPLOADS = window.location.origin.includes(':5000') ? '/uploads' : 'http://localhost:5000/uploads';

/* ── State ─────────────────────────────────────────────── */
const state = {
  page:        1,
  perPage:     12,
  totalPages:  1,
  total:       0,
  loading:     false,
  editors:     [],
  filters: {
    search:        '',
    category:      '',
    sort:          'rating',
    available:     false,
    minRating:     0,
    minRate:       0,
    maxRate:       0,
    city:          '',
    minExperience: 0,
    software:      '',
    language:      '',
  },
  favoriteIds: [],
};

/* ── Auth ───────────────────────────────────────────────── */
const getToken = () => localStorage.getItem('cc_token');
const getUser  = () => { try { return JSON.parse(localStorage.getItem('cc_user')); } catch { return null; } };

function isLoggedIn() { return !!getToken() && !!getUser(); }

/* ── Toast ──────────────────────────────────────────────── */
function toast(msg, type = 'success') {
  const el = document.getElementById('toast');
  if (!el) return;
  el.textContent = msg;
  el.className   = `toast ${type} show`;
  clearTimeout(el._t);
  el._t = setTimeout(() => el.classList.remove('show'), 3500);
}

/* ── Debounce ───────────────────────────────────────────── */
function debounce(fn, ms) {
  let t; return (...args) => { clearTimeout(t); t = setTimeout(() => fn(...args), ms); };
}

/* ── Helpers ────────────────────────────────────────────── */
function initials(name) { return (name||'?').split(' ').map(w=>w[0]).join('').toUpperCase().slice(0,2); }
function esc(s) { const d=document.createElement('div'); d.textContent=s; return d.innerHTML; }

const CATEGORY_ICONS = {
  wedding: '💍', youtube: '▶️', gaming: '🎮', reels: '🎬',
  podcast: '🎙️', documentary: '🎥', short_film: '🎞️',
  motion_graphics: '✨', vfx: '🔮', colorist: '�',
  thumbnail_designer: '�️', audio_editor: '🎵',
  subtitle_editor: '📝', ai_video_editor: '🤖', other: '🎞️'
};
const CATEGORY_LABELS = {
  wedding: 'Wedding', youtube: 'YouTube', gaming: 'Gaming', reels: 'Reels',
  podcast: 'Podcast', documentary: 'Documentary', short_film: 'Short Film',
  motion_graphics: 'Motion Graphics', vfx: 'VFX', colorist: 'Colorist',
  thumbnail_designer: 'Thumbnail Designer', audio_editor: 'Audio Editor',
  subtitle_editor: 'Subtitle Editor', ai_video_editor: 'AI Video Editor', other: 'Other'
};
const AVAIL_LABELS = { available: '🟢 Available', busy: '🟡 Busy', on_vacation: '⚪ On Vacation' };

/* ── API Fetch ──────────────────────────────────────────── */
async function fetchEditors() {
  if (state.loading) return;
  state.loading = true;
  showSkeletons();

  const f = state.filters;
  const params = new URLSearchParams({
    page:     state.page,
    per_page: state.perPage,
    sort:     f.sort,
  });

  if (f.search)    params.set('search',    f.search);
  if (f.category)  params.set('category',  f.category);
  if (f.available) params.set('available', 'true');
  if (f.minRating) params.set('min_rating', f.minRating);
  if (f.maxRate)   params.set('max_rate',   f.maxRate);
  if (f.minRate)   params.set('min_rate',   f.minRate);
  if (f.city)      params.set('city',       f.city);
  if (f.minExperience) params.set('min_experience', f.minExperience);
  if (f.software)  params.set('software',  f.software);
  if (f.language)  params.set('language',  f.language);

  try {
    const res  = await fetch(`${API}/users/editors?${params}`);
    const data = await res.json();

    if (!data.success) { toast('Failed to load editors.', 'error'); renderEmpty(); state.loading = false; return; }

    const meta = data.meta?.pagination || {};
    state.editors    = data.data || [];
    state.total      = meta.total || 0;
    state.totalPages = meta.pages || 1;

    renderEditors(state.editors);
    renderPagination();
    updateResultsBar();
  } catch (e) {
    console.error(e);
    toast('Network error — is the server running?', 'error');
    renderEmpty();
  }

  state.loading = false;
}

/* ── Render ─────────────────────────────────────────────── */
function renderEditors(editors) {
  const grid = document.getElementById('editors-grid');
  if (!editors.length) { renderEmpty(); return; }

  grid.innerHTML = editors.map(e => buildCard(e)).join('');

  // Attach button events
  grid.querySelectorAll('.btn-hire').forEach(btn => {
    btn.addEventListener('click', e => { e.stopPropagation(); handleHire(btn.dataset.id, btn.dataset.name); });
  });
  grid.querySelectorAll('.btn-fav').forEach(btn => {
    btn.addEventListener('click', e => { e.stopPropagation(); handleFavorite(btn, parseInt(btn.dataset.id)); });
  });
  // Card click → profile
  grid.querySelectorAll('.editor-card').forEach(card => {
    card.addEventListener('click', () => {
      window.open(`editor-profile.html?id=${card.dataset.id}`, '_blank');
    });
  });
}

function buildCard(e) {
  const cat        = (e.category || 'other').toLowerCase().replace(' ', '_');
  const avail      = e.availability_status || 'available';
  const rating     = parseFloat(e.avg_rating || 0).toFixed(1);
  const reviews    = e.total_reviews || 0;
  const price      = e.hourly_rate ? `₹${Number(e.hourly_rate).toLocaleString('en-IN')}<span>/hr</span>` : '<span>Contact</span>';
  const skills     = (e.skills || []).slice(0, 4);
  const moreSkills = (e.skills || []).length > 4 ? `<span class="skill-chip skill-chip--more">+${e.skills.length - 4}</span>` : '';
  const software   = (e.software_used || []).slice(0, 3);
  const photoUrl   = e.profile_photo ? `${UPLOADS}/avatars/${e.profile_photo}` : null;
  const bannerUrl  = e.cover_banner  ? `${UPLOADS}/banners/${e.cover_banner}`  : null;
  const isFav      = state.favoriteIds.includes(e.user_id);
  const exp        = e.experience_years ? `${e.experience_years}yr exp` : null;
  const city       = e.city || null;
  const stars      = generateStars(parseFloat(e.avg_rating || 0));

  const availCls = { available: 'card-avail--available', busy: 'card-avail--busy', on_vacation: 'card-avail--vacation' }[avail] || 'card-avail--available';
  const userRole = getUser()?.role;

  return `
    <div class="editor-card" data-id="${e.user_id}">

      <!-- Banner -->
      <div class="card-banner ${bannerUrl ? '' : `banner--${cat}`}">
        ${bannerUrl ? `<img src="${bannerUrl}" alt="" loading="lazy">` : ''}
        <div class="card-avail ${availCls}">
          <span class="card-avail__dot"></span>
          ${avail === 'available' ? 'Available' : avail === 'busy' ? 'Busy' : 'On Vacation'}
        </div>
      </div>

      <!-- Avatar row -->
      <div class="card-profile">
        <div class="card-avatar">
          ${photoUrl ? `<img src="${photoUrl}" alt="${esc(e.full_name)}" loading="lazy">` : `<span>${initials(e.full_name)}</span>`}
        </div>
        <div class="card-name-block">
          <div class="card-name">${esc(e.full_name)}</div>
          <div class="card-handle">${e.username ? `@${e.username}` : ''}</div>
        </div>
        ${e.is_verified ? `<div class="card-verified"><span class="verified-badge">✓ Verified</span></div>` : ''}
      </div>

      <div class="card-body">

        <!-- Category + tagline -->
        <div style="margin-bottom:8px">
          <span class="cat-badge cat--${cat}">
            ${CATEGORY_ICONS[cat] || '🎞️'} ${CATEGORY_LABELS[cat] || cat}
          </span>
        </div>
        <div class="card-tagline">${esc(e.tagline || 'Professional video editor ready to bring your vision to life.')}</div>

        <!-- Stats: rating + price -->
        <div class="card-stats">
          <div class="card-rating">
            <span class="card-rating__star">${stars}</span>
            <span class="card-rating__val">${rating}</span>
            <span class="card-rating__cnt">(${reviews})</span>
          </div>
          <div class="card-price">${price}</div>
        </div>

        <!-- Info pills: exp, city, projects -->
        <div class="card-info">
          ${exp        ? `<span class="info-pill"><span class="info-pill__icon">⏱</span>${esc(exp)}</span>` : ''}
          ${city       ? `<span class="info-pill"><span class="info-pill__icon">📍</span>${esc(city)}</span>` : ''}
          ${e.completed_projects ? `<span class="info-pill"><span class="info-pill__icon">✅</span>${e.completed_projects} projects</span>` : ''}
        </div>

        <!-- Software -->
        ${software.length ? `
        <div class="card-software">
          ${software.map(s => `<span class="sw-chip">${esc(s)}</span>`).join('')}
        </div>` : ''}

        <!-- Skills -->
        ${skills.length ? `
        <div class="card-skills">
          ${skills.map(s => `<span class="skill-chip">${esc(s)}</span>`).join('')}${moreSkills}
        </div>` : ''}

      </div>

      <div class="card-divider"></div>

      <!-- Actions -->
      <div class="card-actions">
        <button class="btn btn-primary btn-hire"
                data-id="${e.user_id}"
                data-name="${esc(e.full_name)}"
                ${avail !== 'available' ? 'disabled style="opacity:.5;cursor:not-allowed"' : ''}>
          ${avail === 'available' ? '⚡ Hire Now' : '🔒 Unavailable'}
        </button>
        <a href="editor-profile.html?id=${e.user_id}"
           class="btn btn-outline"
           onclick="event.stopPropagation()"
           target="_blank">View</a>
        ${userRole === 'client' ? `
        <button class="btn btn-outline btn-fav btn-sm"
                data-id="${e.user_id}"
                title="${isFav ? 'Remove from favourites' : 'Save to favourites'}"
                style="flex:0;padding:9px 12px;font-size:1rem">
          ${isFav ? '❤️' : '🤍'}
        </button>` : ''}
      </div>

    </div>`;
}

function generateStars(rating) {
  const full = Math.floor(rating);
  const half = rating % 1 >= 0.5;
  return '★'.repeat(full) + (half ? '½' : '') + '☆'.repeat(Math.max(0, 5 - full - (half ? 1 : 0)));
}

function showSkeletons() {
  const grid = document.getElementById('editors-grid');
  grid.innerHTML = Array(6).fill(0).map(() => `
    <div class="skeleton-card">
      <div class="skel" style="height:80px;border-radius:0"></div>
      <div style="padding:12px 16px">
        <div class="skel" style="height:56px;width:56px;border-radius:50%;margin-top:-28px;margin-bottom:10px"></div>
        <div class="skel" style="height:14px;width:60%;margin-bottom:8px"></div>
        <div class="skel" style="height:11px;width:40%;margin-bottom:14px"></div>
        <div class="skel" style="height:10px;width:80%;margin-bottom:6px"></div>
        <div class="skel" style="height:10px;width:60%;margin-bottom:14px"></div>
        <div style="display:flex;gap:6px;margin-bottom:12px">
          <div class="skel" style="height:22px;width:70px;border-radius:20px"></div>
          <div class="skel" style="height:22px;width:80px;border-radius:20px"></div>
        </div>
        <div style="display:flex;gap:8px;margin-top:16px">
          <div class="skel" style="height:36px;flex:1;border-radius:10px"></div>
          <div class="skel" style="height:36px;flex:1;border-radius:10px"></div>
        </div>
      </div>
    </div>`).join('');
}

function renderEmpty() {
  const f = state.filters;
  const hasFilters = f.search || f.category || f.available || f.minRating || f.maxRate || f.minExperience || f.software || f.language || f.city;
  document.getElementById('editors-grid').innerHTML = `
    <div class="empty-state">
      <div class="empty-state__icon">🎬</div>
      <div class="empty-state__title">${hasFilters ? 'No editors match your filters' : 'No editors yet'}</div>
      <div class="empty-state__desc">${hasFilters ? 'Try adjusting your search or filters to find more editors.' : 'Be the first to create an editor profile on ClipConnect!'}</div>
      ${hasFilters ? `<button class="btn btn-outline" onclick="clearAllFilters()">Clear Filters</button>` : ''}
    </div>`;
}

/* ── Results bar ────────────────────────────────────────── */
function updateResultsBar() {
  const el = document.getElementById('results-count');
  const sub = document.getElementById('results-sub');
  if (el) el.textContent = `${state.total} Editor${state.total !== 1 ? 's' : ''} Found`;
  if (sub) {
    const f = state.filters;
    const parts = [];
    if (f.category)  parts.push(CATEGORY_LABELS[f.category] || f.category);
    if (f.available) parts.push('Available only');
    if (f.minRating) parts.push(`${f.minRating}+ stars`);
    if (f.city)      parts.push(f.city);
    if (f.minExperience) parts.push(`${f.minExperience}+ years exp`);
    if (f.software)  parts.push(f.software);
    if (f.language)  parts.push(f.language);
    sub.textContent = parts.length ? `Filtered: ${parts.join(' · ')}` : 'All editors on ClipConnect';
  }
  const navCount = document.getElementById('nav-count');
  if (navCount) navCount.innerHTML = `<strong>${state.total}</strong> editors`;

  renderActiveChips();
}

function renderActiveChips() {
  const wrap = document.getElementById('active-filters');
  if (!wrap) return;
  const f = state.filters;
  const chips = [];

  if (f.search)    chips.push({ label: `"${f.search}"`,         key: 'search' });
  if (f.category)  chips.push({ label: CATEGORY_LABELS[f.category], key: 'category' });
  if (f.available) chips.push({ label: 'Available only',        key: 'available' });
  if (f.minRating) chips.push({ label: `${f.minRating}★+`,     key: 'minRating' });
  if (f.maxRate)   chips.push({ label: `≤₹${Number(f.maxRate).toLocaleString('en-IN')}/hr`, key: 'maxRate' });
  if (f.city)      chips.push({ label: `📍${f.city}`,          key: 'city' });
  if (f.minExperience) chips.push({ label: `${f.minExperience}+ years`, key: 'minExperience' });
  if (f.software)  chips.push({ label: f.software,             key: 'software' });
  if (f.language)  chips.push({ label: f.language,             key: 'language' });

  wrap.innerHTML = chips.map(c => `
    <button class="filter-chip" onclick="removeChip('${c.key}')">
      ${esc(c.label)} <span class="filter-chip__remove">✕</span>
    </button>`).join('');
}

window.removeChip = function(key) {
  if (key === 'available') state.filters.available = false;
  else if (key === 'minRating') state.filters.minRating = 0;
  else if (key === 'maxRate') state.filters.maxRate = 0;
  else if (key === 'minExperience') state.filters.minExperience = 0;
  else state.filters[key] = '';

  syncUIToState();
  resetAndFetch();
};

window.clearAllFilters = function() {
  state.filters = { search: '', category: '', sort: 'rating', available: false, minRating: 0, minRate: 0, maxRate: 0, city: '', minExperience: 0, software: '', language: '' };
  syncUIToState();
  resetAndFetch();
};

/* ── Pagination ─────────────────────────────────────────── */
function renderPagination() {
  const wrap = document.getElementById('pagination');
  if (!wrap || state.totalPages <= 1) { if (wrap) wrap.innerHTML = ''; return; }

  const pages = [];
  const p = state.page;
  const t = state.totalPages;

  pages.push({ label: '←', page: p - 1, disabled: p === 1 });

  for (let i = 1; i <= t; i++) {
    if (i === 1 || i === t || (i >= p - 1 && i <= p + 1)) {
      pages.push({ label: i, page: i, active: i === p });
    } else if (i === p - 2 || i === p + 2) {
      pages.push({ label: '…', page: null });
    }
  }

  pages.push({ label: '→', page: p + 1, disabled: p === t });

  wrap.innerHTML = pages.map(pg => {
    if (pg.label === '…') return `<span class="page-ellipsis">…</span>`;
    return `<button class="page-btn ${pg.active ? 'active' : ''}" ${pg.disabled ? 'disabled' : ''}
      onclick="gotoPage(${pg.page})">${pg.label}</button>`;
  }).join('');
}

window.gotoPage = function(p) {
  if (!p || p < 1 || p > state.totalPages) return;
  state.page = p;
  fetchEditors();
  window.scrollTo({ top: 0, behavior: 'smooth' });
};

function resetAndFetch() { state.page = 1; fetchEditors(); }

/* ── Filter: Category pills ─────────────────────────────── */
function initCategoryBar() {
  document.querySelectorAll('.cat-pill').forEach(pill => {
    pill.addEventListener('click', () => {
      const cat = pill.dataset.cat;
      state.filters.category = state.filters.category === cat ? '' : cat;
      document.querySelectorAll('.cat-pill').forEach(p => p.classList.remove('active'));
      if (state.filters.category) pill.classList.add('active');
      // Also sync sidebar checkbox
      syncCategoryCheckboxes();
      resetAndFetch();
    });
  });
}

function syncCategoryCheckboxes() {
  document.querySelectorAll('.cat-check').forEach(cb => {
    cb.checked = cb.value === state.filters.category;
  });
}

/* ── Filter: Sidebar ────────────────────────────────────── */
function initSidebarFilters() {

  // Category checkboxes
  document.querySelectorAll('.cat-check').forEach(cb => {
    cb.addEventListener('change', () => {
      state.filters.category = cb.checked ? cb.value : '';
      document.querySelectorAll('.cat-check').forEach(c => { if (c !== cb) c.checked = false; });
      syncCategoryPills();
      resetAndFetch();
    });
  });

  // Available only checkbox
  const availCb = document.getElementById('filter-available');
  availCb?.addEventListener('change', () => {
    state.filters.available = availCb.checked;
    resetAndFetch();
  });

  // Rating options
  document.querySelectorAll('.star-opt').forEach(opt => {
    opt.addEventListener('click', () => {
      const val = parseFloat(opt.dataset.rating);
      state.filters.minRating = state.filters.minRating === val ? 0 : val;
      document.querySelectorAll('.star-opt').forEach(o => o.classList.toggle('active', parseFloat(o.dataset.rating) === state.filters.minRating));
      resetAndFetch();
    });
  });

  // Max rate slider
  const rateSlider = document.getElementById('filter-max-rate');
  const rateLabel  = document.getElementById('filter-rate-label');
  rateSlider?.addEventListener('input', () => {
    const val = parseInt(rateSlider.value);
    state.filters.maxRate = val === parseInt(rateSlider.max) ? 0 : val;
    rateLabel.textContent = val === parseInt(rateSlider.max) ? 'Any' : `₹${Number(val).toLocaleString('en-IN')}`;
    debouncedFetch();
  });

  // City input
  const cityInput = document.getElementById('filter-city');
  cityInput?.addEventListener('input', debounce(() => {
    state.filters.city = cityInput.value.trim();
    resetAndFetch();
  }, 500));

  // Experience radio buttons
  document.querySelectorAll('input[name="experience"]').forEach(radio => {
    radio.addEventListener('change', () => {
      state.filters.minExperience = parseInt(radio.value);
      resetAndFetch();
    });
  });

  // Software input
  const softwareInput = document.getElementById('filter-software');
  softwareInput?.addEventListener('input', debounce(() => {
    state.filters.software = softwareInput.value.trim();
    resetAndFetch();
  }, 500));

  // Language input
  const languageInput = document.getElementById('filter-language');
  languageInput?.addEventListener('input', debounce(() => {
    state.filters.language = languageInput.value.trim();
    resetAndFetch();
  }, 500));
}

const debouncedFetch = debounce(resetAndFetch, 400);

function syncCategoryPills() {
  document.querySelectorAll('.cat-pill').forEach(p => {
    p.classList.toggle('active', p.dataset.cat === state.filters.category);
  });
}

/* ── Search bar ─────────────────────────────────────────── */
function initSearch() {
  const navInput = document.getElementById('nav-search-input');
  const navSearch = debounce(() => {
    state.filters.search = navInput.value.trim();
    resetAndFetch();
  }, 400);
  navInput?.addEventListener('input', navSearch);
  navInput?.addEventListener('keydown', e => { if (e.key === 'Escape') { navInput.value = ''; state.filters.search = ''; resetAndFetch(); }});
}

/* ── Sort ───────────────────────────────────────────────── */
function initSort() {
  const sel = document.getElementById('sort-select');
  sel?.addEventListener('change', () => { state.filters.sort = sel.value; resetAndFetch(); });
}

/* ── Sync UI → State ─────────────────────────────────────── */
function syncUIToState() {
  const f = state.filters;
  const navInput = document.getElementById('nav-search-input');
  if (navInput) navInput.value = f.search;
  const availCb = document.getElementById('filter-available');
  if (availCb) availCb.checked = f.available;
  const sortSel = document.getElementById('sort-select');
  if (sortSel) sortSel.value = f.sort;
  const cityInput = document.getElementById('filter-city');
  if (cityInput) cityInput.value = f.city;
  const rateSlider = document.getElementById('filter-max-rate');
  const rateLabel  = document.getElementById('filter-rate-label');
  if (rateSlider && rateLabel) {
    rateSlider.value = f.maxRate || rateSlider.max;
    rateLabel.textContent = f.maxRate ? `₹${Number(f.maxRate).toLocaleString('en-IN')}` : 'Any';
  }
  const softwareInput = document.getElementById('filter-software');
  if (softwareInput) softwareInput.value = f.software;
  const languageInput = document.getElementById('filter-language');
  if (languageInput) languageInput.value = f.language;
  
  // Experience radio buttons
  const expRadio = document.querySelector(`input[name="experience"][value="${f.minExperience}"]`);
  if (expRadio) expRadio.checked = true;
  
  syncCategoryPills();
  syncCategoryCheckboxes();
  document.querySelectorAll('.star-opt').forEach(o => o.classList.toggle('active', parseFloat(o.dataset.rating) === f.minRating));
  renderActiveChips();
}

/* ── Mobile sidebar ─────────────────────────────────────── */
function initMobileSidebar() {
  const sidebar  = document.getElementById('filter-sidebar');
  const overlay  = document.getElementById('sidebar-overlay');
  const toggle   = document.getElementById('filter-toggle-btn');
  const closeBtn = document.getElementById('sidebar-close-btn');

  toggle?.addEventListener('click', () => {
    sidebar.classList.add('open');
    overlay.classList.add('visible');
  });

  const close = () => { sidebar.classList.remove('open'); overlay.classList.remove('visible'); };
  overlay?.addEventListener('click', close);
  closeBtn?.addEventListener('click', close);
}

/* ── Hire flow ──────────────────────────────────────────── */
function handleHire(editorId, editorName) {
  if (typeof openHireModal === 'function') {
    openHireModal(editorId, editorName);
  } else {
    toast(`Hire modal loading... (${editorName})`, 'info');
  }
}

/* ── Favorites ──────────────────────────────────────────── */
async function loadFavorites() {
  if (!isLoggedIn() || getUser()?.role !== 'client') return;
  try {
    const res  = await fetch(`${API}/users/me/favorites`, { headers: { 'Authorization': `Bearer ${getToken()}` } });
    const data = await res.json();
    if (data.success) state.favoriteIds = (data.data.favorites || []).map(f => f.user_id);
  } catch {}
}

async function handleFavorite(btn, editorId) {
  if (!isLoggedIn()) { toast('Log in to save editors.', 'info'); return; }
  if (getUser()?.role !== 'client') { toast('Only clients can save favourites.', 'info'); return; }

  const isFav = state.favoriteIds.includes(editorId);
  const method = isFav ? 'DELETE' : 'POST';

  try {
    const res  = await fetch(`${API}/users/me/favorites/${editorId}`, {
      method, headers: { 'Authorization': `Bearer ${getToken()}` }
    });
    const data = await res.json();
    if (data.success) {
      if (isFav) { state.favoriteIds = state.favoriteIds.filter(id => id !== editorId); btn.textContent = '🤍'; }
      else       { state.favoriteIds.push(editorId); btn.textContent = '❤️'; }
      toast(data.message);
    } else { toast(data.message || 'Could not update.', 'error'); }
  } catch { toast('Network error.', 'error'); }
}

/* ── URL Params (shareable filters) ─────────────────────── */
function readURLParams() {
  const p = new URLSearchParams(window.location.search);
  if (p.get('category'))  state.filters.category  = p.get('category');
  if (p.get('search'))    state.filters.search    = p.get('search');
  if (p.get('available')) state.filters.available = true;
  if (p.get('sort'))      state.filters.sort      = p.get('sort');
}

function writeURLParams() {
  const f = state.filters;
  const p = new URLSearchParams();
  if (f.category)  p.set('category',  f.category);
  if (f.search)    p.set('search',    f.search);
  if (f.available) p.set('available', '1');
  if (f.sort !== 'rating') p.set('sort', f.sort);
  const url = `${window.location.pathname}?${p}`.replace(/\?$/, '');
  window.history.replaceState({}, '', url);
}

/* ── Nav user state ─────────────────────────────────────── */
function initNavUser() {
  const user = getUser();
  const navLinks = document.getElementById('nav-links');
  if (!navLinks) return;

  if (user) {
    const dashUrl = user.role === 'editor' ? 'editor-dashboard.html' : 'dashboard.html';
    navLinks.innerHTML = `
      <a href="${dashUrl}" class="btn btn-outline btn-sm">My Dashboard</a>
      <a href="${user.role === 'client' ? 'dashboard.html' : 'editor-dashboard.html'}" class="btn btn-primary btn-sm">
        ${user.role === 'client' ? '🏠 Dashboard' : '🎬 Dashboard'}
      </a>`;
  } else {
    navLinks.innerHTML = `
      <a href="login.html" class="btn btn-outline btn-sm">Log In</a>
      <a href="register.html" class="btn btn-primary btn-sm">Sign Up Free</a>`;
  }
}

/* ── Boot ───────────────────────────────────────────────── */
async function init() {
  readURLParams();
  initNavUser();
  initCategoryBar();
  initSidebarFilters();
  initSearch();
  initSort();
  initMobileSidebar();
  syncUIToState();

  // Delegated click handling for grid buttons
  document.getElementById('editors-grid')?.addEventListener('click', (e) => {
    const hireBtn = e.target.closest('.btn-hire');
    if (hireBtn) {
      e.preventDefault();
      e.stopPropagation();
      const editorId = hireBtn.dataset.id;
      const editorName = hireBtn.dataset.name;
      handleHire(editorId, editorName);
      return;
    }

    const favBtn = e.target.closest('.btn-fav');
    if (favBtn) {
      e.preventDefault();
      e.stopPropagation();
      const editorId = parseInt(favBtn.dataset.id, 10);
      handleFavorite(favBtn, editorId);
      return;
    }
  });

  // Load favorites if logged in as client
  await loadFavorites();
  await fetchEditors();
}

document.addEventListener('DOMContentLoaded', init);
