/**
 * ============================================================
 * ClipConnect - API Service Module
 * ============================================================
 * Purpose:
 *   Centralized module for all HTTP calls to the Flask backend.
 *   Wraps the native fetch() API with:
 *     - Automatic base URL prepending
 *     - JWT token auto-attachment in headers
 *     - Consistent error handling
 *     - JSON parsing
 *     - Loading state helpers
 *
 * Why this pattern?
 *   Instead of writing fetch() calls scattered across every JS file,
 *   we use one service. If the backend URL changes, we update ONE place.
 *   If auth headers change format, ONE place to fix.
 *
 * Usage:
 *   const result = await ApiService.auth.register({ full_name, email, password, role });
 *   const result = await ApiService.auth.login({ email, password });
 *   const result = await ApiService.auth.getMe();
 * ============================================================
 */


// ============================================================
// CONFIGURATION
// ============================================================

/**
 * Base URL of the Flask backend API.
 * Change this when deploying to production.
 * In production: 'https://api.clipconnect.com'
 */
const API_BASE_URL = 'http://localhost:5000/api';

/**
 * Default request timeout in milliseconds.
 * Prevents requests from hanging forever.
 */
const REQUEST_TIMEOUT_MS = 15000;  // 15 seconds


// ============================================================
// TOKEN MANAGEMENT
// ============================================================

const TokenManager = {
    /**
     * Key used to store the JWT token in localStorage.
     * Consistent key prevents typos elsewhere in the codebase.
     */
    TOKEN_KEY: 'clipconnect_token',
    USER_KEY: 'clipconnect_user',

    /**
     * Save token and user data to localStorage after login.
     * @param {string} token - JWT token string
     * @param {Object} user - User object from API
     */
    save(token, user) {
        localStorage.setItem(this.TOKEN_KEY, token);
        localStorage.setItem(this.USER_KEY, JSON.stringify(user));
    },

    /**
     * Retrieve the stored JWT token.
     * @returns {string|null} JWT token or null if not logged in
     */
    getToken() {
        return localStorage.getItem(this.TOKEN_KEY);
    },

    /**
     * Retrieve the stored user object.
     * @returns {Object|null} Parsed user object or null
     */
    getUser() {
        const raw = localStorage.getItem(this.USER_KEY);
        try {
            return raw ? JSON.parse(raw) : null;
        } catch {
            return null;
        }
    },

    /**
     * Check if a user is currently logged in (has a valid token stored).
     * Note: This does NOT verify the token's expiry — use /api/auth/me for that.
     * @returns {boolean}
     */
    isLoggedIn() {
        return !!this.getToken();
    },

    /**
     * Clear all auth data from localStorage (logout).
     */
    clear() {
        localStorage.removeItem(this.TOKEN_KEY);
        localStorage.removeItem(this.USER_KEY);
    }
};


// ============================================================
// CORE HTTP CLIENT
// ============================================================

/**
 * Core HTTP request function used by all API methods.
 * Handles: headers, auth tokens, JSON body, error parsing.
 *
 * @param {string} endpoint - API path (e.g., '/auth/register')
 * @param {Object} options - fetch() options overrides
 * @returns {Promise<Object>} - Parsed JSON response body
 * @throws {Object} - Error object with { message, errors, status_code }
 */
async function httpRequest(endpoint, options = {}) {
    const url = `${API_BASE_URL}${endpoint}`;

    // Build headers
    const headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        ...options.headers
    };

    // Auto-attach JWT token if available
    const token = TokenManager.getToken();
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }

    // Combine options
    const fetchOptions = {
        method: options.method || 'GET',
        headers,
        ...options
    };

    // Serialize body to JSON string if provided
    if (options.body && typeof options.body === 'object') {
        fetchOptions.body = JSON.stringify(options.body);
    }

    // Add timeout using AbortController
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);
    fetchOptions.signal = controller.signal;

    try {
        const response = await fetch(url, fetchOptions);
        clearTimeout(timeoutId);

        // Parse response body as JSON
        let data;
        try {
            data = await response.json();
        } catch {
            // If response isn't JSON (e.g., 502 Bad Gateway HTML)
            throw {
                message: 'Server returned an invalid response. Please try again.',
                status_code: response.status
            };
        }

        // If response is not ok (4xx / 5xx), throw an error with the API's error body
        if (!response.ok) {
            throw {
                message: data.message || 'An error occurred',
                errors: data.errors || null,
                status_code: data.status_code || response.status
            };
        }

        return data;

    } catch (err) {
        clearTimeout(timeoutId);

        // Network/timeout errors
        if (err.name === 'AbortError') {
            throw {
                message: 'Request timed out. Please check your connection and try again.',
                status_code: 408
            };
        }

        // If fetch() itself fails (no internet, CORS, etc.)
        if (err instanceof TypeError && err.message.includes('fetch')) {
            throw {
                message: 'Unable to connect to the server. Make sure the backend is running.',
                status_code: 0
            };
        }

        // Re-throw structured errors from above
        throw err;
    }
}


// ============================================================
// API SERVICE — Organized by Feature
// ============================================================

const ApiService = {

    // ----------------------------------------------------------
    // AUTH Endpoints
    // ----------------------------------------------------------
    auth: {

        /**
         * POST /api/auth/register
         * Register a new user account.
         *
         * @param {Object} payload
         * @param {string} payload.full_name
         * @param {string} payload.email
         * @param {string} payload.password
         * @param {string} payload.role - 'client' or 'editor'
         * @returns {Promise<Object>} - { success, message, data: { user } }
         */
        async register(payload) {
            return await httpRequest('/auth/register', {
                method: 'POST',
                body: payload
            });
        },

        /**
         * POST /api/auth/login
         * Login and retrieve JWT token.
         *
         * @param {Object} payload
         * @param {string} payload.email
         * @param {string} payload.password
         * @returns {Promise<Object>} - { success, message, data: { token, user } }
         */
        async login(payload) {
            return await httpRequest('/auth/login', {
                method: 'POST',
                body: payload
            });
        },

        /**
         * GET /api/auth/me
         * Get current authenticated user's profile.
         * Requires: valid JWT token in localStorage.
         *
         * @returns {Promise<Object>} - { success, data: { user } }
         */
        async getMe() {
            return await httpRequest('/auth/me', {
                method: 'GET'
            });
        },

        /**
         * GET /api/auth/health
         * Check if the auth service is running.
         */
        async healthCheck() {
            return await httpRequest('/auth/health', {
                method: 'GET'
            });
        },

        /**
         * Logout: Clears all local auth data.
         * (JWT is stateless, no server-side logout needed in Week 1)
         * In Week 3+, we'll add a token blacklist.
         */
        logout() {
            TokenManager.clear();
        }
    },

    // ----------------------------------------------------------
    // Add more service groups in future weeks:
    // gigs: { list, get, create, update, delete }
    // orders: { create, list, update }
    // reviews: { create, list }
    // ----------------------------------------------------------
};


// ============================================================
// EXPORT
// ============================================================

// Export as globals for use in HTML files without a module bundler
window.ApiService = ApiService;
window.TokenManager = TokenManager;
