/**
 * ============================================================
 * ClipConnect - Navbar JavaScript
 * ============================================================
 * Purpose:
 *   Handles all interactive behavior for the navigation bar:
 *     - Scroll-based glass effect (adds .scrolled class)
 *     - Mobile hamburger toggle (open/close mobile menu)
 *     - Active link highlighting based on current page
 *     - Auth-aware display (Login/Register vs. Logout)
 *     - User initials avatar (if logged in)
 *     - Smooth close on mobile link click
 *
 * Included in:
 *   - index.html
 *   - login.html
 *   - register.html
 *
 * Depends on:
 *   - js/api.js (TokenManager)
 * ============================================================
 */

'use strict';

document.addEventListener('DOMContentLoaded', function () {
    initNavbar();
});


function initNavbar() {
    initScrollEffect();
    initMobileMenu();
    setActiveNavLink();
    updateNavForAuthState();
}


// ============================================================
// SCROLL EFFECT
// ============================================================

/**
 * Adds .scrolled class to navbar when user scrolls down.
 * This triggers a stronger glassmorphism effect (defined in navbar.css).
 */
function initScrollEffect() {
    const navbar = document.querySelector('.navbar');
    if (!navbar) return;

    // Use IntersectionObserver for performance (no scroll event listener)
    const sentinel = document.createElement('div');
    sentinel.style.cssText = 'position:absolute;top:80px;height:1px;width:100%;pointer-events:none;';
    document.body.prepend(sentinel);

    const observer = new IntersectionObserver(
        ([entry]) => {
            navbar.classList.toggle('scrolled', !entry.isIntersecting);
        },
        { threshold: 0 }
    );

    observer.observe(sentinel);
}


// ============================================================
// MOBILE HAMBURGER MENU
// ============================================================

function initMobileMenu() {
    const hamburger = document.getElementById('navbar-hamburger');
    const mobileMenu = document.getElementById('navbar-mobile-menu');

    if (!hamburger || !mobileMenu) return;

    // Toggle open/close on hamburger click
    hamburger.addEventListener('click', function () {
        const isOpen = this.classList.toggle('open');
        mobileMenu.classList.toggle('open', isOpen);

        // Prevent body scroll when menu is open
        document.body.style.overflow = isOpen ? 'hidden' : '';

        // Accessibility
        this.setAttribute('aria-expanded', String(isOpen));
        mobileMenu.setAttribute('aria-hidden', String(!isOpen));
    });

    // Close menu when any mobile nav link is clicked
    mobileMenu.querySelectorAll('a').forEach(link => {
        link.addEventListener('click', closeMobileMenu);
    });

    // Close menu when clicking outside (on overlay)
    document.addEventListener('click', function (e) {
        if (!hamburger.contains(e.target) && !mobileMenu.contains(e.target)) {
            closeMobileMenu();
        }
    });

    // Close on Escape key
    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape') closeMobileMenu();
    });

    function closeMobileMenu() {
        hamburger.classList.remove('open');
        mobileMenu.classList.remove('open');
        document.body.style.overflow = '';
        hamburger.setAttribute('aria-expanded', 'false');
        mobileMenu.setAttribute('aria-hidden', 'true');
    }
}


// ============================================================
// ACTIVE LINK HIGHLIGHTING
// ============================================================

/**
 * Compares the current page URL to nav links and adds .active class.
 * Works by matching the filename (e.g., 'index.html').
 */
function setActiveNavLink() {
    const currentPage = window.location.pathname.split('/').pop() || 'index.html';

    document.querySelectorAll('.nav-link, .mobile-nav-link').forEach(link => {
        const href = link.getAttribute('href') || '';
        const linkPage = href.split('/').pop();

        if (linkPage === currentPage || (currentPage === '' && linkPage === 'index.html')) {
            link.classList.add('active');
        }
    });
}


// ============================================================
// AUTH-AWARE NAVBAR
// ============================================================

/**
 * Updates the navbar buttons/avatar based on login state.
 * - Not logged in: shows Login + Register buttons
 * - Logged in: shows user avatar/initials + Logout
 */
function updateNavForAuthState() {
    const navActions = document.getElementById('nav-actions');
    const mobileNavActions = document.getElementById('mobile-nav-actions');

    if (!navActions) return;

    const isLoggedIn = TokenManager.isLoggedIn();
    const user = TokenManager.getUser();

    if (isLoggedIn && user) {
        // Show user info + logout
        const initials = getInitials(user.full_name);
        const roleLabel = user.role.charAt(0).toUpperCase() + user.role.slice(1);
        const isAdmin = user.role === 'admin';

        let dashboardLink = 'dashboard.html';
        if (user.role === 'editor') dashboardLink = 'editor-dashboard.html';
        else if (user.role === 'admin') dashboardLink = 'admin-dashboard.html';

        navActions.innerHTML = `
            <div class="navbar-user-info" style="display:flex;align-items:center;gap:12px;">
                ${!isAdmin ? `<a href="${dashboardLink}" class="btn btn-primary btn-sm">Dashboard</a>` : ''}
                <a href="chat.html" class="btn btn-ghost btn-sm" title="Messages">💬 Messages</a>
                <a href="earnings.html" class="btn btn-ghost btn-sm" title="Earnings">💸 Earnings</a>
                <a href="settings.html" class="btn btn-ghost btn-sm" title="Settings">⚙️ Settings</a>
                ${isAdmin ? '<a href="admin-dashboard.html" class="btn btn-primary btn-sm" style="background:#ef4444;" title="Admin">🛡️ Admin</a>' : ''}
                <div class="navbar-avatar-placeholder" title="${user.full_name} (${roleLabel})">
                    ${initials}
                </div>
                <button class="btn btn-ghost btn-sm" id="logout-btn" onclick="handleLogout()">
                    Logout
                </button>
            </div>
        `;

        if (mobileNavActions) {
            mobileNavActions.innerHTML = `
                <div style="padding:16px;background:var(--glass-bg);border-radius:12px;border:1px solid var(--border-subtle);margin-bottom:16px;">
                    <p style="font-size:13px;color:var(--text-muted);margin-bottom:4px;">Logged in as</p>
                    <p style="font-weight:600;color:var(--text-primary)">${user.full_name}</p>
                    <p style="font-size:12px;color:var(--color-primary-light)">${roleLabel}</p>
                </div>
                <a href="${dashboardLink}" class="btn btn-primary w-full" style="margin-bottom:8px;">Dashboard</a>
                <a href="chat.html" class="btn btn-secondary w-full" style="margin-bottom:8px;">Messages</a>
                <a href="earnings.html" class="btn btn-secondary w-full" style="margin-bottom:8px;">Earnings</a>
                <a href="settings.html" class="btn btn-secondary w-full" style="margin-bottom:16px;">Settings</a>
                <button class="btn btn-secondary w-full" onclick="handleLogout()">Sign Out</button>
            `;
        }

        // Update CTA buttons if on index page
        const ctaBtns = [document.getElementById('hero-cta-hire'), document.getElementById('cta-hire-btn')];
        ctaBtns.forEach(btn => { if (btn) btn.href = 'browse-editors.html'; });

        const editorBtns = [document.getElementById('hero-cta-editor'), document.getElementById('cta-editor-btn')];
        editorBtns.forEach(btn => { if (btn) btn.style.display = 'none'; });

    } else {
        // Show login/register buttons
        navActions.innerHTML = `
            <a href="login.html"    class="btn btn-ghost btn-sm"    id="nav-login-btn">Login</a>
            <a href="register.html" class="btn btn-primary btn-sm"  id="nav-register-btn">Get Started</a>
        `;

        if (mobileNavActions) {
            mobileNavActions.innerHTML = `
                <a href="login.html"    class="btn btn-secondary w-full">Login</a>
                <a href="register.html" class="btn btn-primary w-full">Create Account</a>
            `;
        }
    }
}


// ============================================================
// LOGOUT
// ============================================================

/**
 * Clears auth state and redirects to login page.
 * Exposed globally so HTML onclick="handleLogout()" works.
 */
function handleLogout() {
    ApiService.auth.logout();

    // Brief flash before redirect
    const btn = document.getElementById('logout-btn');
    if (btn) btn.textContent = 'Signing out...';

    setTimeout(() => {
        window.location.href = 'login.html';
    }, 500);
}

// Make handleLogout available globally
window.handleLogout = handleLogout;


// ============================================================
// UTILITIES
// ============================================================

/**
 * Generate initials from a full name.
 * "John Doe" → "JD"
 * @param {string} name
 * @returns {string} Up to 2 initials
 */
function getInitials(name) {
    if (!name) return '?';
    return name
        .split(' ')
        .filter(Boolean)
        .slice(0, 2)
        .map(word => word[0].toUpperCase())
        .join('');
}
