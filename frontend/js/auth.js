/**
 * ============================================================
 * ClipConnect - Authentication JavaScript
 * ============================================================
 * Purpose:
 *   Handles all frontend logic for Login and Register pages:
 *     - Form submission and validation
 *     - Calling ApiService for register/login
 *     - Displaying error messages
 *     - Password show/hide toggle
 *     - Password strength meter (register page)
 *     - Role card selection (register page)
 *     - Redirect after successful auth
 *     - Button loading states
 *
 * Included in:
 *   - login.html
 *   - register.html
 *
 * Depends on:
 *   - js/api.js (ApiService, TokenManager)
 * ============================================================
 */

'use strict';

// ============================================================
// DOM READY
// ============================================================

document.addEventListener('DOMContentLoaded', function () {

    // Detect which page we're on by checking for specific elements
    const registerForm = document.getElementById('register-form');
    const loginForm = document.getElementById('login-form');

    if (registerForm) {
        initRegisterPage();
    }

    if (loginForm) {
        initLoginPage();
    }

    // Common: Initialize password toggles for any page
    initPasswordToggles();

    // Redirect logged-in users away from auth pages
    redirectIfLoggedIn();
});


// ============================================================
// REDIRECT LOGGED IN USERS
// ============================================================

/**
 * If the user is already logged in, redirect them to the home page.
 * Prevents logged-in users from seeing the login/register pages.
 */
function redirectIfLoggedIn() {
    if (TokenManager.isLoggedIn()) {
        window.location.href = 'index.html';
    }
}


// ============================================================
// REGISTER PAGE INITIALIZATION
// ============================================================

function initRegisterPage() {
    const form = document.getElementById('register-form');
    const passwordInput = document.getElementById('password');
    const roleCards = document.querySelectorAll('.role-card');

    // Initialize role card selection behavior
    if (roleCards.length) {
        initRoleCards(roleCards);
    }

    // Live password strength meter
    if (passwordInput) {
        passwordInput.addEventListener('input', function () {
            updatePasswordStrength(this.value);
        });
    }

    // Form submission
    form.addEventListener('submit', handleRegisterSubmit);
}


// ============================================================
// LOGIN PAGE INITIALIZATION
// ============================================================

function initLoginPage() {
    const form = document.getElementById('login-form');
    form.addEventListener('submit', handleLoginSubmit);
}


// ============================================================
// REGISTER FORM HANDLER
// ============================================================

/**
 * Handles the register form submission event.
 * @param {Event} e - Form submit event
 */
async function handleRegisterSubmit(e) {
    e.preventDefault();  // Prevent default HTML form submission

    const form = e.target;
    const submitBtn = form.querySelector('[type="submit"]');

    // Collect form values
    const full_name = document.getElementById('full_name').value.trim();
    const email = document.getElementById('email').value.trim();
    const password = document.getElementById('password').value;
    const role = getSelectedRole();

    // Client-side validation
    const errors = validateRegisterForm({ full_name, email, password, role });
    if (Object.keys(errors).length > 0) {
        displayFieldErrors(errors);
        return;
    }

    // Clear previous errors
    clearAllErrors();

    // Show loading state
    setButtonLoading(submitBtn, true, 'Creating Account...');

    try {
        // Call the register API
        const response = await ApiService.auth.register({ full_name, email, password, role });

        // Success!
        showMessage('success',
            `🎉 Welcome to ClipConnect, ${response.data.user.full_name}! Redirecting to login...`
        );

        // Redirect to login after 2 seconds
        setTimeout(() => {
            window.location.href = 'login.html';
        }, 2000);

    } catch (error) {
        // Handle API errors
        if (error.errors) {
            displayFieldErrors(error.errors);
        }
        showMessage('error', error.message || 'Registration failed. Please try again.');

    } finally {
        setButtonLoading(submitBtn, false, 'Create Account');
    }
}


// ============================================================
// LOGIN FORM HANDLER
// ============================================================

/**
 * Handles the login form submission event.
 * @param {Event} e - Form submit event
 */
async function handleLoginSubmit(e) {
    e.preventDefault();

    const form = e.target;
    const submitBtn = form.querySelector('[type="submit"]');

    const email = document.getElementById('email').value.trim();
    const password = document.getElementById('password').value;

    // Client-side validation
    const errors = validateLoginForm({ email, password });
    if (Object.keys(errors).length > 0) {
        displayFieldErrors(errors);
        return;
    }

    clearAllErrors();
    setButtonLoading(submitBtn, true, 'Signing In...');

    try {
        const response = await ApiService.auth.login({ email, password });

        // Save token and user data to localStorage
        TokenManager.save(response.data.token, response.data.user);

        showMessage('success', `Welcome back, ${response.data.user.full_name}! 🎬`);

        // Redirect to home page after 1 second
        setTimeout(() => {
            window.location.href = 'index.html';
        }, 1200);

    } catch (error) {
        if (error.errors) {
            displayFieldErrors(error.errors);
        }
        showMessage('error', error.message || 'Login failed. Please check your credentials.');

    } finally {
        setButtonLoading(submitBtn, false, 'Sign In');
    }
}


// ============================================================
// CLIENT-SIDE VALIDATION
// ============================================================

function validateRegisterForm({ full_name, email, password, role }) {
    const errors = {};

    if (!full_name || full_name.length < 2) {
        errors.full_name = 'Full name must be at least 2 characters.';
    }

    if (!email || !isValidEmail(email)) {
        errors.email = 'Please enter a valid email address.';
    }

    if (!password || password.length < 8) {
        errors.password = 'Password must be at least 8 characters.';
    }

    if (!role) {
        errors.role = 'Please select your account type.';
    }

    return errors;
}

function validateLoginForm({ email, password }) {
    const errors = {};

    if (!email || !isValidEmail(email)) {
        errors.email = 'Please enter a valid email address.';
    }

    if (!password) {
        errors.password = 'Password is required.';
    }

    return errors;
}

function isValidEmail(email) {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}


// ============================================================
// ERROR DISPLAY UTILITIES
// ============================================================

/**
 * Displays field-level errors beneath each input.
 * @param {Object} errors - { field_name: "error message" }
 */
function displayFieldErrors(errors) {
    // Clear existing errors first
    clearAllErrors();

    for (const [field, message] of Object.entries(errors)) {
        const input = document.getElementById(field);
        if (input) {
            input.classList.add('error');

            // Find or create the error element below the input
            let errorEl = input.closest('.form-group')?.querySelector('.form-error');
            if (!errorEl) {
                errorEl = document.createElement('p');
                errorEl.className = 'form-error';
                input.closest('.form-group')?.appendChild(errorEl);
            }

            errorEl.innerHTML = `<span>⚠</span> ${message}`;
            errorEl.style.display = 'flex';
        }
    }
}

/**
 * Clears all error states from all inputs on the page.
 */
function clearAllErrors() {
    document.querySelectorAll('.form-input.error, .form-select.error').forEach(el => {
        el.classList.remove('error');
    });

    document.querySelectorAll('.form-error').forEach(el => {
        el.textContent = '';
        el.style.display = 'none';
    });
}

/**
 * Shows a page-level success or error message banner.
 * @param {'success'|'error'} type
 * @param {string} message
 */
function showMessage(type, message) {
    const msgEl = document.getElementById('auth-message');
    if (!msgEl) return;

    msgEl.className = `auth-message ${type} show`;
    msgEl.innerHTML = `
        <span>${type === 'success' ? '✓' : '✕'}</span>
        <span>${message}</span>
    `;

    // Auto-hide after 6 seconds
    if (type !== 'success') {
        setTimeout(() => {
            msgEl.classList.remove('show');
        }, 6000);
    }
}


// ============================================================
// BUTTON LOADING STATE
// ============================================================

/**
 * Toggles the loading state of a submit button.
 * @param {HTMLElement} btn - The button element
 * @param {boolean} isLoading - Whether to show loading state
 * @param {string} text - Button label text
 */
function setButtonLoading(btn, isLoading, text) {
    if (!btn) return;
    btn.disabled = isLoading;
    btn.classList.toggle('loading', isLoading);
    const textSpan = btn.querySelector('.btn-text');
    if (textSpan) textSpan.textContent = text;
}


// ============================================================
// PASSWORD TOGGLE
// ============================================================

/**
 * Initializes all password show/hide toggle buttons on the page.
 * Works by finding buttons with data-toggle-password attribute.
 */
function initPasswordToggles() {
    document.querySelectorAll('[data-toggle-password]').forEach(btn => {
        btn.addEventListener('click', function () {
            const targetId = this.dataset.togglePassword;
            const input = document.getElementById(targetId);
            if (!input) return;

            const isPassword = input.type === 'password';
            input.type = isPassword ? 'text' : 'password';

            // Toggle eye icon
            this.innerHTML = isPassword
                ? `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"></path><line x1="1" y1="1" x2="23" y2="23"></line></svg>`
                : `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg>`;
        });
    });
}


// ============================================================
// PASSWORD STRENGTH METER
// ============================================================

/**
 * Updates the password strength indicator bar and label.
 * @param {string} password - Current password value
 */
function updatePasswordStrength(password) {
    const strengthBar = document.getElementById('strength-bar');
    const strengthLabel = document.getElementById('strength-label');
    if (!strengthBar || !strengthLabel) return;

    const { score, label, className } = getPasswordStrength(password);

    const segments = strengthBar.querySelectorAll('.strength-segment');
    segments.forEach((seg, i) => {
        seg.className = 'strength-segment';
        if (i < score) {
            seg.classList.add(className);
        }
    });

    strengthLabel.textContent = password.length ? `Strength: ${label}` : '';
    strengthLabel.className = `strength-label ${password.length ? className : ''}`;
}

/**
 * Calculates a password strength score.
 * @param {string} password
 * @returns {{ score: number, label: string, className: string }}
 */
function getPasswordStrength(password) {
    if (!password) return { score: 0, label: '', className: '' };

    let score = 0;
    if (password.length >= 8)   score++;
    if (password.length >= 12)  score++;
    if (/[A-Z]/.test(password)) score++;
    if (/[a-z]/.test(password)) score++;
    if (/\d/.test(password))    score++;
    if (/[^A-Za-z0-9]/.test(password)) score++;

    if (score <= 2) return { score: 1, label: 'Weak',   className: 'weak' };
    if (score <= 3) return { score: 2, label: 'Fair',   className: 'fair' };
    if (score <= 4) return { score: 3, label: 'Good',   className: 'good' };
    return              { score: 4, label: 'Strong', className: 'strong' };
}


// ============================================================
// ROLE CARD SELECTION
// ============================================================

/**
 * Initializes click handlers for role selector cards.
 * Manages selected state and hidden radio input.
 * @param {NodeList} roleCards
 */
function initRoleCards(roleCards) {
    roleCards.forEach(card => {
        card.addEventListener('click', function () {
            // Remove selected from all
            roleCards.forEach(c => c.classList.remove('selected'));

            // Select this one
            this.classList.add('selected');

            // Check the hidden radio input
            const radio = this.querySelector('input[type="radio"]');
            if (radio) radio.checked = true;

            // Clear role error if any
            const roleError = document.getElementById('role-error');
            if (roleError) {
                roleError.style.display = 'none';
                roleError.textContent = '';
            }
        });
    });
}

/**
 * Gets the currently selected role from the role cards.
 * @returns {string|null} - 'client', 'editor', or null
 */
function getSelectedRole() {
    const checkedRadio = document.querySelector('.role-card input[type="radio"]:checked');
    return checkedRadio ? checkedRadio.value : null;
}
