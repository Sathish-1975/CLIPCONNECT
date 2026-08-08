/**
 * ============================================================
 * ClipConnect — edit-profile.js
 * ============================================================
 * Handles the full editor profile editing experience:
 *   - Tab navigation (Basic, Professional, Location/Pricing,
 *     Portfolio, Social Links)
 *   - Fetch & populate existing profile data
 *   - Tag input (skills, software, languages)
 *   - Avatar + Banner + Resume upload (with live preview)
 *   - Portfolio image upload + video link add/remove
 *   - Save each section via PUT /api/users/me/profile
 *   - Profile completion progress bar
 * ============================================================
 */

'use strict';

/* ─────────────────────────────────────────────
   Config & Globals
───────────────────────────────────────────── */
const API = 'http://localhost:5000/api';
const UPLOADS = 'http://localhost:5000/uploads';

let currentProfile = null;   // Cached profile from server
let pendingChanges = {};     // Accumulated field changes (flushed on Save)

/* ─────────────────────────────────────────────
   Token helpers
───────────────────────────────────────────── */
const getToken  = () => localStorage.getItem('cc_token');
const getUser   = () => { try { return JSON.parse(localStorage.getItem('cc_user')); } catch { return null; } };

function authHeaders() {
  return { 'Authorization': `Bearer ${getToken()}`, 'Content-Type': 'application/json' };
}

/* ─────────────────────────────────────────────
   Toast notifications
───────────────────────────────────────────── */
function toast(msg, type = 'success') {
  const el = document.getElementById('toast');
  if (!el) return;
  el.textContent = msg;
  el.className = `toast ${type} show`;
  setTimeout(() => el.classList.remove('show'), 3500);
}

/* ─────────────────────────────────────────────
   Profile Completion Score
───────────────────────────────────────────── */
function calcCompletion(p) {
  const fields = [
    p.username, p.tagline, p.bio, p.profile_photo, p.cover_banner,
    p.category, p.experience_years,
    p.skills?.length, p.software_used?.length, p.languages?.length,
    p.city, p.country,
    p.hourly_rate || p.fixed_price_from,
    p.availability_status,
    p.resume_file,
    (p.portfolio_videos?.length || p.portfolio_images?.length),
    (p.website_url || p.instagram_url || p.linkedin_url || p.youtube_url),
  ];
  const filled = fields.filter(Boolean).length;
  return Math.round((filled / fields.length) * 100);
}

function updateProgressBar(p) {
  const pct  = calcCompletion(p);
  const bar  = document.getElementById('progress-fill');
  const lbl  = document.getElementById('progress-label');
  if (bar) bar.style.width = pct + '%';
  if (lbl) lbl.textContent = `Profile ${pct}% complete`;
}

/* ─────────────────────────────────────────────
   Tab navigation
───────────────────────────────────────────── */
function initTabs() {
  const tabs  = document.querySelectorAll('.profile-tab-btn');
  const panes = document.querySelectorAll('.profile-tab-pane');

  tabs.forEach(btn => {
    btn.addEventListener('click', () => {
      const target = btn.dataset.tab;
      tabs.forEach(t => t.classList.remove('active'));
      panes.forEach(p => p.classList.remove('active'));
      btn.classList.add('active');
      document.getElementById(`tab-${target}`)?.classList.add('active');
    });
  });
}

/* ─────────────────────────────────────────────
   Tag Input Component
   Usage: initTagInput('skills-input', 'skills-tags', 'skills')
───────────────────────────────────────────── */
function initTagInput(inputId, containerId, fieldName) {
  const wrap  = document.getElementById(containerId);
  const field = document.getElementById(inputId);
  if (!wrap || !field) return;

  function renderTags(tags) {
    // Remove existing badges
    wrap.querySelectorAll('.tag-badge').forEach(b => b.remove());
    tags.forEach((tag, i) => {
      const badge = document.createElement('span');
      badge.className = 'tag-badge';
      badge.innerHTML = `${tag}<span class="tag-badge__remove" data-i="${i}">×</span>`;
      wrap.insertBefore(badge, field);
    });
  }

  function getTags() {
    return Array.from(wrap.querySelectorAll('.tag-badge'))
      .map(b => b.childNodes[0].textContent.trim())
      .filter(Boolean);
  }

  function pushTag(val) {
    val = val.trim();
    if (!val) return;
    const current = getTags();
    if (current.includes(val)) return;  // No duplicates
    if (current.length >= 30) { toast('Max 30 tags allowed', 'error'); return; }
    renderTags([...current, val]);
    pendingChanges[fieldName] = getTags();
    field.value = '';
  }

  // Enter or comma → add tag
  field.addEventListener('keydown', e => {
    if (e.key === 'Enter' || e.key === ',') {
      e.preventDefault();
      pushTag(field.value.replace(/,/g, ''));
    }
    if (e.key === 'Backspace' && !field.value) {
      const tags = getTags();
      if (tags.length) {
        tags.pop();
        renderTags(tags);
        pendingChanges[fieldName] = tags;
      }
    }
  });

  // Remove tag via ×
  wrap.addEventListener('click', e => {
    if (e.target.classList.contains('tag-badge__remove')) {
      const i = parseInt(e.target.dataset.i);
      const tags = getTags();
      tags.splice(i, 1);
      renderTags(tags);
      pendingChanges[fieldName] = tags;
    }
  });

  // Click wrap → focus input
  wrap.addEventListener('click', () => field.focus());

  // Expose a setter for initial data
  wrap._setTags = (arr) => renderTags(Array.isArray(arr) ? arr : []);

  return { renderTags, getTags };
}

/* ─────────────────────────────────────────────
   Populate form with profile data
───────────────────────────────────────────── */
function populateForm(p) {
  const set = (id, val) => { const el = document.getElementById(id); if (el && val != null) el.value = val; };

  // Basic tab
  set('field-username', p.username || '');
  set('field-tagline',  p.tagline  || '');
  set('field-bio',      p.bio      || '');

  // Avatar preview
  if (p.profile_photo) {
    const av = document.getElementById('avatar-preview');
    if (av) { av.src = `${UPLOADS}/avatars/${p.profile_photo}`; av.style.display = 'block'; }
    const initials = document.getElementById('avatar-initials');
    if (initials) initials.style.display = 'none';
  }

  // Banner preview
  if (p.cover_banner) {
    const bv = document.getElementById('banner-preview');
    if (bv) { bv.src = `${UPLOADS}/banners/${p.cover_banner}`; bv.style.display = 'block'; }
  }

  // Professional tab
  set('field-category',    p.category || '');
  set('field-experience',  p.experience_years || 0);

  // Tag inputs
  document.getElementById('skills-tags')?._setTags?.(p.skills || []);
  document.getElementById('software-tags')?._setTags?.(p.software_used || []);
  document.getElementById('lang-tags')?._setTags?.(p.languages || []);

  // Location & pricing tab
  set('field-city',           p.city || '');
  set('field-country',        p.country || '');
  set('field-hourly-rate',    p.hourly_rate || '');
  set('field-price-from',     p.fixed_price_from || '');
  set('field-price-to',       p.fixed_price_to || '');
  set('field-availability',   p.availability_status || 'available');
  set('field-response-time',  p.response_time || '');

  // Social links tab
  set('field-website',   p.website_url   || '');
  set('field-youtube',   p.youtube_url   || '');
  set('field-instagram', p.instagram_url || '');
  set('field-linkedin',  p.linkedin_url  || '');
  set('field-twitter',   p.twitter_url   || '');
  set('field-behance',   p.behance_url   || '');

  // Portfolio tab
  renderPortfolioImages(p.portfolio_images || []);
  renderPortfolioVideos(p.portfolio_videos || []);

  // Resume
  if (p.resume_file) {
    const resumeInfo = document.getElementById('resume-info');
    if (resumeInfo) {
      resumeInfo.textContent = `Current: ${p.resume_file}`;
      resumeInfo.style.display = 'block';
    }
  }
}

/* ─────────────────────────────────────────────
   Portfolio Images (edit mode)
───────────────────────────────────────────── */
function renderPortfolioImages(images) {
  const grid = document.getElementById('portfolio-img-grid');
  if (!grid) return;
  grid.innerHTML = '';

  images.forEach((img, i) => {
    const item = document.createElement('div');
    item.className = 'portfolio-edit-item';
    item.innerHTML = `
      <img src="${img.url || `${UPLOADS}/portfolio/images/${img.filename}`}" alt="${img.title || ''}">
      <div class="portfolio-edit-item__del" data-index="${i}" title="Remove">×</div>`;
    grid.appendChild(item);
  });

  // Delete handler
  grid.querySelectorAll('.portfolio-edit-item__del').forEach(btn => {
    btn.addEventListener('click', () => deletePortfolioImage(parseInt(btn.dataset.index)));
  });
}

async function deletePortfolioImage(index) {
  if (!confirm('Remove this portfolio image?')) return;
  try {
    const res = await fetch(`${API}/users/me/portfolio/image/${index}`, {
      method: 'DELETE',
      headers: { 'Authorization': `Bearer ${getToken()}` }
    });
    const data = await res.json();
    if (data.success) {
      toast('Image removed');
      await refreshProfile();
    } else {
      toast(data.message || 'Failed to remove image', 'error');
    }
  } catch { toast('Network error', 'error'); }
}

/* ─────────────────────────────────────────────
   Portfolio Videos (edit mode)
───────────────────────────────────────────── */
function renderPortfolioVideos(videos) {
  const list = document.getElementById('portfolio-video-list');
  if (!list) return;
  list.innerHTML = '';

  videos.forEach((vid, i) => {
    const item = document.createElement('div');
    item.className = 'video-edit-item';
    item.innerHTML = `
      <div class="video-edit-item__info">
        <div class="video-edit-item__title">${vid.title || '(No title)'}</div>
        <div class="video-edit-item__url">${vid.url}</div>
      </div>
      <button class="btn btn-secondary btn-sm del-video-btn" data-index="${i}">Remove</button>`;
    list.appendChild(item);
  });

  list.querySelectorAll('.del-video-btn').forEach(btn => {
    btn.addEventListener('click', () => deletePortfolioVideo(parseInt(btn.dataset.index)));
  });
}

async function deletePortfolioVideo(index) {
  if (!confirm('Remove this video?')) return;
  try {
    const res = await fetch(`${API}/users/me/portfolio/video/${index}`, {
      method: 'DELETE',
      headers: { 'Authorization': `Bearer ${getToken()}` }
    });
    const data = await res.json();
    if (data.success) {
      toast('Video removed');
      await refreshProfile();
    } else {
      toast(data.message || 'Failed', 'error');
    }
  } catch { toast('Network error', 'error'); }
}

/* ─────────────────────────────────────────────
   File Upload helpers (avatar, banner, resume)
───────────────────────────────────────────── */
function initFileUpload(inputId, previewId, endpoint, fieldName, previewType = 'image') {
  const input   = document.getElementById(inputId);
  const preview = document.getElementById(previewId);
  if (!input) return;

  input.addEventListener('change', async () => {
    const file = input.files[0];
    if (!file) return;

    // Local preview
    if (previewType === 'image' && preview) {
      preview.src    = URL.createObjectURL(file);
      preview.style.display = 'block';
      const initials = document.getElementById('avatar-initials');
      if (initials) initials.style.display = 'none';
    }

    // Upload to server
    const formData = new FormData();
    formData.append(fieldName, file);

    try {
      const res = await fetch(`${API}/users/me/${endpoint}`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${getToken()}` },
        body: formData
      });
      const data = await res.json();
      if (data.success) {
        toast(`${endpoint.charAt(0).toUpperCase() + endpoint.slice(1)} uploaded!`);
        await refreshProfile();
      } else {
        toast(data.message || 'Upload failed', 'error');
      }
    } catch {
      toast('Upload failed. Check your connection.', 'error');
    }
  });
}

/* ─────────────────────────────────────────────
   Portfolio image upload
───────────────────────────────────────────── */
function initPortfolioImageUpload() {
  const input = document.getElementById('portfolio-img-input');
  if (!input) return;

  input.addEventListener('change', async () => {
    const files = Array.from(input.files).slice(0, 5);  // max 5 at a time
    if (!files.length) return;

    let success = 0;
    for (const file of files) {
      const formData = new FormData();
      formData.append('image', file);
      const titleEl = document.getElementById('portfolio-img-title');
      if (titleEl?.value) formData.append('title', titleEl.value);

      try {
        const res = await fetch(`${API}/users/me/portfolio/image`, {
          method: 'POST',
          headers: { 'Authorization': `Bearer ${getToken()}` },
          body: formData
        });
        const data = await res.json();
        if (data.success) success++;
        else toast(data.message || 'Upload failed', 'error');
      } catch { toast('Upload error', 'error'); }
    }

    if (success > 0) {
      toast(`${success} image${success > 1 ? 's' : ''} uploaded!`);
      input.value = '';
      await refreshProfile();
    }
  });
}

/* ─────────────────────────────────────────────
   Portfolio video add form
───────────────────────────────────────────── */
function initPortfolioVideoForm() {
  const btn = document.getElementById('add-video-btn');
  if (!btn) return;

  btn.addEventListener('click', async () => {
    const url   = document.getElementById('video-url')?.value?.trim();
    const title = document.getElementById('video-title')?.value?.trim();
    const desc  = document.getElementById('video-desc')?.value?.trim();

    if (!url) { toast('Please enter a video URL', 'error'); return; }

    try {
      const res = await fetch(`${API}/users/me/portfolio/video`, {
        method: 'POST',
        headers: authHeaders(),
        body: JSON.stringify({ url, title, description: desc })
      });
      const data = await res.json();
      if (data.success) {
        toast('Video added to portfolio!');
        document.getElementById('video-url').value   = '';
        document.getElementById('video-title').value = '';
        document.getElementById('video-desc').value  = '';
        await refreshProfile();
      } else {
        toast(data.message || 'Failed to add video', 'error');
      }
    } catch { toast('Network error', 'error'); }
  });
}

/* ─────────────────────────────────────────────
   Collect form field changes (called on input)
───────────────────────────────────────────── */
function trackFieldChange(inputId, fieldName, transform) {
  const el = document.getElementById(inputId);
  if (!el) return;
  el.addEventListener('input', () => {
    let val = el.value.trim();
    if (transform) val = transform(val);
    pendingChanges[fieldName] = val || null;
  });
}

function initFieldTracking() {
  trackFieldChange('field-username',     'username');
  trackFieldChange('field-tagline',      'tagline');
  trackFieldChange('field-bio',          'bio');
  trackFieldChange('field-city',         'city');
  trackFieldChange('field-country',      'country');
  trackFieldChange('field-response-time','response_time');
  trackFieldChange('field-website',      'website_url');
  trackFieldChange('field-youtube',      'youtube_url');
  trackFieldChange('field-instagram',    'instagram_url');
  trackFieldChange('field-linkedin',     'linkedin_url');
  trackFieldChange('field-twitter',      'twitter_url');
  trackFieldChange('field-behance',      'behance_url');
  trackFieldChange('field-hourly-rate',  'hourly_rate',   v => parseFloat(v) || null);
  trackFieldChange('field-price-from',   'fixed_price_from', v => parseFloat(v) || null);
  trackFieldChange('field-price-to',     'fixed_price_to',   v => parseFloat(v) || null);
  trackFieldChange('field-experience',   'experience_years', v => parseInt(v)   || null);

  // Select fields
  const catEl = document.getElementById('field-category');
  if (catEl) catEl.addEventListener('change', () => { pendingChanges.category = catEl.value || null; });

  const avEl = document.getElementById('field-availability');
  if (avEl) avEl.addEventListener('change', () => { pendingChanges.availability_status = avEl.value || null; });
}

/* ─────────────────────────────────────────────
   Save profile (PUT)
───────────────────────────────────────────── */
async function saveProfile() {
  if (Object.keys(pendingChanges).length === 0) {
    toast('No changes to save.', 'info');
    return;
  }

  // Collect tag arrays fresh from DOM
  const getTagsFrom = (containerId) => {
    const wrap = document.getElementById(containerId);
    if (!wrap) return undefined;
    return Array.from(wrap.querySelectorAll('.tag-badge'))
      .map(b => b.childNodes[0].textContent.trim())
      .filter(Boolean);
  };

  const skills   = getTagsFrom('skills-tags');
  const software = getTagsFrom('software-tags');
  const langs    = getTagsFrom('lang-tags');
  if (skills   !== undefined) pendingChanges.skills        = skills;
  if (software !== undefined) pendingChanges.software_used = software;
  if (langs    !== undefined) pendingChanges.languages     = langs;

  const saveBtn = document.getElementById('save-btn');
  if (saveBtn) { saveBtn.disabled = true; saveBtn.textContent = 'Saving...'; }

  try {
    const res = await fetch(`${API}/users/me/profile`, {
      method: 'PUT',
      headers: authHeaders(),
      body: JSON.stringify(pendingChanges)
    });
    const data = await res.json();

    if (data.success) {
      currentProfile = data.data.profile;
      pendingChanges = {};
      updateProgressBar(currentProfile);
      toast('Profile saved successfully!');

      const msg = document.getElementById('save-msg');
      if (msg) { msg.classList.add('visible'); setTimeout(() => msg.classList.remove('visible'), 3000); }
    } else {
      toast(data.message || 'Save failed', 'error');
    }
  } catch {
    toast('Network error. Could not save.', 'error');
  } finally {
    if (saveBtn) { saveBtn.disabled = false; saveBtn.textContent = 'Save Changes'; }
  }
}

/* ─────────────────────────────────────────────
   Load & refresh profile from server
───────────────────────────────────────────── */
async function refreshProfile() {
  try {
    const res = await fetch(`${API}/users/me/profile`, {
      headers: { 'Authorization': `Bearer ${getToken()}` }
    });
    const data = await res.json();
    if (data.success) {
      currentProfile = data.data.profile;
      populateForm(currentProfile);
      updateProgressBar(currentProfile);
    }
  } catch { /* silently ignore */ }
}

/* ─────────────────────────────────────────────
   Guard: redirect if not logged in / not editor
───────────────────────────────────────────── */
function authGuard() {
  const token = getToken();
  const user  = getUser();
  if (!token || !user) {
    window.location.href = 'login.html?redirect=edit-profile.html';
    return false;
  }
  if (user.role !== 'editor') {
    toast('Only editors can edit a profile.', 'error');
    setTimeout(() => window.location.href = 'index.html', 2000);
    return false;
  }
  return true;
}

/* ─────────────────────────────────────────────
   Bootstrap
───────────────────────────────────────────── */
async function init() {
  if (!authGuard()) return;

  const user = getUser();

  // Set avatar initials from user name
  const initials = document.getElementById('avatar-initials');
  if (initials && user?.full_name) {
    initials.textContent = user.full_name.split(' ').map(w => w[0]).join('').toUpperCase().slice(0,2);
  }

  // Ensure editor profile exists (auto-create if new editor)
  await fetch(`${API}/users/me/profile`, {
    method: 'POST',
    headers: authHeaders()
  });

  // Load existing data
  await refreshProfile();

  // Wire up components
  initTabs();
  initFieldTracking();
  initTagInput('skills-input',   'skills-tags',   'skills');
  initTagInput('software-input', 'software-tags', 'software_used');
  initTagInput('lang-input',     'lang-tags',     'languages');

  initFileUpload('avatar-input',  'avatar-preview',  'avatar',  'avatar',  'image');
  initFileUpload('banner-input',  'banner-preview',  'banner',  'banner',  'image');
  initFileUpload('resume-input',  null,              'resume',  'resume',  'file');

  initPortfolioImageUpload();
  initPortfolioVideoForm();

  // Save button
  document.getElementById('save-btn')?.addEventListener('click', saveProfile);

  // Nav user name
  const navName = document.getElementById('nav-user-name');
  if (navName && user?.full_name) navName.textContent = user.full_name;

  // View profile link
  const viewBtn = document.getElementById('view-profile-btn');
  if (viewBtn && user?.id) viewBtn.href = `editor-profile.html?id=${user.id}`;

  // Logout
  document.getElementById('logout-btn')?.addEventListener('click', () => {
    localStorage.removeItem('cc_token');
    localStorage.removeItem('cc_user');
    window.location.href = 'login.html';
  });
}

document.addEventListener('DOMContentLoaded', init);
