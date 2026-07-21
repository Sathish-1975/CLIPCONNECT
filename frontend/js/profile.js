/**
 * ============================================================
 * ClipConnect — profile.js
 * ============================================================
 * Powers the public editor-profile.html page:
 *   - Reads ?id= from URL
 *   - Fetches GET /api/users/editors/:id
 *   - Renders all profile sections (banner, avatar, bio,
 *     stats, skills, software, languages, pricing,
 *     portfolio images, portfolio videos, social links)
 *   - Lightbox for portfolio images
 *   - Star rating renderer
 * ============================================================
 */

'use strict';

const API     = 'http://localhost:5001/api';
const UPLOADS = 'http://localhost:5001/uploads';

/* ─────────────────────────────────────────────
   Utility helpers
───────────────────────────────────────────── */
function qs(sel, root = document) { return root.querySelector(sel); }
function el(tag, cls, html = '') {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  if (html) e.innerHTML = html;
  return e;
}

function stars(rating) {
  const full  = Math.floor(rating);
  const half  = rating % 1 >= 0.5;
  const empty = 5 - full - (half ? 1 : 0);
  return '★'.repeat(full) + (half ? '½' : '') + '☆'.repeat(empty);
}

function formatCurrency(val) {
  if (!val) return '—';
  return '₹' + Number(val).toLocaleString('en-IN');
}

function categoryLabel(cat) {
  const map = {
    youtube: 'YouTube', reels: 'Reels & Shorts', wedding: 'Wedding',
    corporate: 'Corporate', motion_graphics: 'Motion Graphics',
    podcast: 'Podcast', ecommerce: 'E-Commerce', documentary: 'Documentary', other: 'Other'
  };
  return map[cat] || cat;
}

function availabilityLabel(status) {
  const map = { available: 'Available', busy: 'Busy', on_vacation: 'On Vacation' };
  return map[status] || status;
}

/* ─────────────────────────────────────────────
   Render helpers
───────────────────────────────────────────── */

function renderBanner(p) {
  const banner = qs('.profile-banner');
  if (p.cover_banner && banner) {
    banner.style.backgroundImage = `url('${UPLOADS}/banners/${p.cover_banner}')`;
    banner.style.backgroundSize = 'cover';
    banner.style.backgroundPosition = 'center';
  }
}

function renderAvatar(p, user) {
  const wrap = qs('.profile-avatar');
  if (!wrap) return;
  if (p.profile_photo) {
    wrap.innerHTML = `<img src="${UPLOADS}/avatars/${p.profile_photo}" alt="${user.full_name}">`;
  } else {
    const initials = (user.full_name || '?').split(' ').map(w => w[0]).join('').toUpperCase().slice(0, 2);
    wrap.textContent = initials;
  }
}

function renderHeader(p, user) {
  const setText = (id, txt) => { const el = document.getElementById(id); if (el) el.textContent = txt; };
  const setHTML = (id, html) => { const el = document.getElementById(id); if (el) el.innerHTML = html; };

  setText('profile-name',     user.full_name || 'Editor');
  setText('profile-username', p.username ? `@${p.username}` : '');
  setText('profile-tagline',  p.tagline || '');

  // Availability badge
  const avBadge = document.getElementById('availability-badge');
  if (avBadge) {
    const status = p.availability_status || 'available';
    avBadge.className = `availability-badge ${status}`;
    avBadge.innerHTML = `<span class="availability-badge__dot"></span>${availabilityLabel(status)}`;
  }

  // Verified badge
  if (p.is_verified) {
    const vb = document.getElementById('verified-badge');
    if (vb) vb.style.display = 'flex';
  }

  // Edit profile button (only if viewing own profile)
  const storedUser = (() => { try { return JSON.parse(localStorage.getItem('cc_user')); } catch { return null; } })();
  if (storedUser && storedUser.id === user.id) {
    const editBtn = document.getElementById('edit-profile-btn');
    if (editBtn) editBtn.style.display = 'inline-flex';
  }
}

function renderStats(p) {
  const setS = (id, val) => { const el = document.getElementById(id); if (el) el.textContent = val; };
  setS('stat-rating',   p.avg_rating > 0 ? Number(p.avg_rating).toFixed(1) : '—');
  setS('stat-reviews',  p.total_reviews || '0');
  setS('stat-projects', p.completed_projects || '0');
}

function renderStarRating(p) {
  const el = document.getElementById('star-rating');
  if (!el) return;
  if (p.avg_rating > 0) {
    el.innerHTML = `<span class="rating-stars">${stars(Number(p.avg_rating))}</span>
                    <span style="color:#94A3B8;font-size:0.85rem;margin-left:6px">${Number(p.avg_rating).toFixed(1)} / 5.0 (${p.total_reviews} reviews)</span>`;
  } else {
    el.innerHTML = `<span style="color:#475569;font-size:0.85rem">No reviews yet</span>`;
  }
}

function renderBio(p) {
  const el = document.getElementById('profile-bio');
  if (!el) return;
  el.textContent = p.bio || 'This editor hasn\'t added a bio yet.';
}

function renderMeta(p) {
  const el = document.getElementById('profile-meta');
  if (!el) return;
  const items = [];
  if (p.city || p.country) items.push(`<span class="profile-meta-item">📍 ${[p.city, p.country].filter(Boolean).join(', ')}</span>`);
  if (p.experience_years)   items.push(`<span class="profile-meta-item">🎬 ${p.experience_years} yr${p.experience_years > 1 ? 's' : ''} experience</span>`);
  if (p.category)           items.push(`<span class="profile-meta-item">🏷️ ${categoryLabel(p.category)}</span>`);
  if (p.response_time)      items.push(`<span class="profile-meta-item">⏱️ ${p.response_time}</span>`);
  el.innerHTML = items.join('');
}

function renderSkills(p) {
  const el = document.getElementById('skills-list');
  if (!el) return;
  const tags = p.skills || [];
  if (tags.length === 0) { el.innerHTML = '<span style="color:#475569">No skills listed</span>'; return; }
  el.innerHTML = tags.map(t => `<span class="skill-tag">${t}</span>`).join('');
}

function renderSoftware(p) {
  const el = document.getElementById('software-list');
  if (!el) return;
  const sw = p.software_used || [];
  if (sw.length === 0) { el.innerHTML = '<li style="color:#475569">Not specified</li>'; return; }
  el.innerHTML = sw.map(s => `<li>${s}</li>`).join('');
}

function renderLanguages(p) {
  const el = document.getElementById('lang-list');
  if (!el) return;
  const langs = p.languages || [];
  if (langs.length === 0) { el.innerHTML = '<span style="color:#475569">Not specified</span>'; return; }
  el.innerHTML = langs.map(l => `<div class="language-item">🌐 ${l}</div>`).join('');
}

function renderPricing(p) {
  const el = document.getElementById('pricing-block');
  if (!el) return;
  const rows = [];
  if (p.hourly_rate)      rows.push(`<div class="pricing-row"><span class="pricing-row__label">Hourly Rate</span><span class="pricing-row__value">${formatCurrency(p.hourly_rate)} / hr</span></div>`);
  if (p.fixed_price_from) rows.push(`<div class="pricing-row"><span class="pricing-row__label">Fixed Price From</span><span class="pricing-row__value">${formatCurrency(p.fixed_price_from)}</span></div>`);
  if (p.fixed_price_to)   rows.push(`<div class="pricing-row"><span class="pricing-row__label">Fixed Price Up To</span><span class="pricing-row__value">${formatCurrency(p.fixed_price_to)}</span></div>`);
  el.innerHTML = rows.length ? rows.join('') : '<p style="color:#475569;font-size:0.85rem">Pricing not set</p>';
}

function renderSocial(p) {
  const el = document.getElementById('social-links');
  if (!el) return;
  const links = [
    { key: 'website_url',   label: '🌐 Website',   icon: '🌐' },
    { key: 'youtube_url',   label: '▶️ YouTube',   icon: '▶️' },
    { key: 'instagram_url', label: '📸 Instagram', icon: '📸' },
    { key: 'linkedin_url',  label: '💼 LinkedIn',  icon: '💼' },
    { key: 'twitter_url',   label: '🐦 Twitter',   icon: '🐦' },
    { key: 'behance_url',   label: '🎨 Behance',   icon: '🎨' },
  ];
  const active = links.filter(l => p[l.key]);
  if (active.length === 0) { el.innerHTML = '<p style="color:#475569;font-size:0.85rem">No social links added</p>'; return; }
  el.innerHTML = active.map(l => `<a href="${p[l.key]}" target="_blank" rel="noopener noreferrer" class="social-link">${l.icon} ${l.label}</a>`).join('');
}

function renderPortfolioImages(p) {
  const grid = document.getElementById('portfolio-img-grid');
  if (!grid) return;
  const images = p.portfolio_images || [];
  if (images.length === 0) {
    grid.innerHTML = '<p style="color:#475569;font-size:0.88rem;grid-column:1/-1">No portfolio images yet.</p>';
    return;
  }
  grid.innerHTML = images.map((img, i) => `
    <div class="portfolio-item" data-index="${i}" data-src="${img.url || `${UPLOADS}/portfolio/images/${img.filename}`}">
      <img src="${img.url || `${UPLOADS}/portfolio/images/${img.filename}`}" alt="${img.title || `Image ${i+1}`}" loading="lazy">
      <div class="portfolio-item__overlay">
        ${img.title ? `<span style="color:white;font-size:0.85rem;font-weight:600;text-align:center;padding:4px">${img.title}</span>` : ''}
      </div>
    </div>`).join('');

  // Lightbox
  grid.querySelectorAll('.portfolio-item').forEach(item => {
    item.addEventListener('click', () => openLightbox(item.dataset.src));
  });
}

function renderPortfolioVideos(p) {
  const list = document.getElementById('portfolio-video-list');
  if (!list) return;
  const videos = p.portfolio_videos || [];
  if (videos.length === 0) {
    list.innerHTML = '<p style="color:#475569;font-size:0.88rem">No portfolio videos yet.</p>';
    return;
  }
  list.innerHTML = videos.map(vid => {
    const thumb = vid.thumbnail || getVideoThumbnail(vid.url);
    return `
    <a href="${vid.url}" target="_blank" rel="noopener noreferrer" class="video-item" style="display:flex;text-decoration:none">
      <div class="video-item__thumb">
        ${thumb ? `<img src="${thumb}" alt="${vid.title || 'Video'}">` : '▶'}
      </div>
      <div class="video-item__info">
        <div class="video-item__title">${vid.title || 'Portfolio Video'}</div>
        ${vid.description ? `<div class="video-item__desc">${vid.description}</div>` : ''}
        <div style="font-size:0.75rem;color:#475569;margin-top:4px;word-break:break-all">${vid.url}</div>
      </div>
    </a>`;
  }).join('');
}

function getVideoThumbnail(url) {
  if (!url) return null;
  const ytMatch = url.match(/(?:youtube\.com\/watch\?v=|youtu\.be\/)([^&\s]+)/);
  if (ytMatch) return `https://img.youtube.com/vi/${ytMatch[1]}/mqdefault.jpg`;
  return null;
}

function renderResume(p) {
  const el = document.getElementById('resume-section');
  if (!el) return;
  if (p.resume_file) {
    el.innerHTML = `<a href="${UPLOADS}/resumes/${p.resume_file}" class="resume-btn" target="_blank">
      📄 Download Resume / CV
    </a>`;
  } else {
    el.innerHTML = '<p style="color:#475569;font-size:0.85rem">No resume uploaded</p>';
  }
}

/* ─────────────────────────────────────────────
   Lightbox for portfolio images
───────────────────────────────────────────── */
let lightbox = null;

function openLightbox(src) {
  if (!lightbox) {
    lightbox = document.createElement('div');
    lightbox.style.cssText = `
      position:fixed;inset:0;background:rgba(0,0,0,0.92);
      display:flex;align-items:center;justify-content:center;
      z-index:9999;cursor:zoom-out;animation:fadeIn 0.2s ease`;
    lightbox.innerHTML = `<img id="lb-img" style="max-width:90vw;max-height:90vh;border-radius:8px;box-shadow:0 24px 80px rgba(0,0,0,0.8)" alt="Portfolio">`;
    lightbox.addEventListener('click', () => { document.body.removeChild(lightbox); lightbox = null; });
    document.body.appendChild(lightbox);
  }
  document.getElementById('lb-img').src = src;
}

/* ─────────────────────────────────────────────
   Hire / Contact button
───────────────────────────────────────────── */
function initHireButton(userId) {
  const btn = document.getElementById('hire-btn');
  if (!btn) return;
  btn.addEventListener('click', () => {
    const token = localStorage.getItem('cc_token');
    if (!token) {
      window.location.href = `login.html?redirect=editor-profile.html?id=${userId}`;
    } else {
      // Week 3: navigate to order/gig page
      toast('Hiring flow coming in Week 3!', 'info');
    }
  });
}

/* ─────────────────────────────────────────────
   Toast
───────────────────────────────────────────── */
function toast(msg, type = 'success') {
  let t = document.getElementById('toast');
  if (!t) {
    t = document.createElement('div');
    t.id = 'toast';
    document.body.appendChild(t);
  }
  t.textContent = msg;
  t.className = `toast ${type} show`;
  setTimeout(() => t.classList.remove('show'), 3500);
}

/* ─────────────────────────────────────────────
   Loading state
───────────────────────────────────────────── */
function showSkeleton() {
  qs('.profile-banner').classList.add('skeleton');
}
function hideSkeleton() {
  qs('.profile-banner')?.classList.remove('skeleton');
}

/* ─────────────────────────────────────────────
   Main
───────────────────────────────────────────── */
async function init() {
  // Get editor user_id from URL ?id=
  const params = new URLSearchParams(window.location.search);
  const userId = params.get('id');
  if (!userId) {
    document.getElementById('profile-error')?.style.setProperty('display', 'block');
    toast('No editor ID specified in URL.', 'error');
    return;
  }

  showSkeleton();

  try {
    const res  = await fetch(`${API}/users/editors/${userId}`);
    const data = await res.json();

    hideSkeleton();

    if (!data.success || !data.data?.profile) {
      document.getElementById('profile-error')?.style.setProperty('display', 'block');
      toast('Editor not found.', 'error');
      return;
    }

    const p    = data.data.profile;
    const user = p.user;

    // Update page title / meta
    document.title = `${user.full_name} — ClipConnect`;

    // Render all sections
    renderBanner(p);
    renderAvatar(p, user);
    renderHeader(p, user);
    renderStats(p);
    renderStarRating(p);
    renderBio(p);
    renderMeta(p);
    renderSkills(p);
    renderSoftware(p);
    renderLanguages(p);
    renderPricing(p);
    renderSocial(p);
    renderPortfolioImages(p);
    renderPortfolioVideos(p);
    renderResume(p);
    initHireButton(userId);

    // Show content
    qs('.profile-content')?.style.setProperty('display', 'block');

  } catch (err) {
    hideSkeleton();
    console.error(err);
    toast('Failed to load profile.', 'error');
  }
}

document.addEventListener('DOMContentLoaded', init);
