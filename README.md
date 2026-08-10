# 🎬 ClipConnect — Freelance Video Editor Marketplace

> **India's #1 platform connecting clients with professional freelance video editors.**  
> Built like Swiggy/Zomato — but for creative talent.

---

## 📋 Table of Contents

- [Overview](#overview)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Week 1 — What's Built](#week-1--whats-built)
- [Setup Guide](#setup-guide)
- [API Reference](#api-reference)
- [Frontend Pages](#frontend-pages)
- [Environment Variables](#environment-variables)
- [Database Schema](#database-schema)

---

## Overview

ClipConnect is a full-stack freelance marketplace where:
- **Clients** post projects and hire video editors
- **Editors** create profiles, showcase work, and get hired
- **Admins** manage the platform

---

## Tech Stack

| Layer        | Technology                          |
|--------------|-------------------------------------|
| Frontend     | HTML5, CSS3, Vanilla JavaScript     |
| Backend      | Python Flask 3.0                    |
| Database     | PostgreSQL 15+                      |
| ORM          | SQLAlchemy 2.0                      |
| Auth         | JWT (PyJWT) + bcrypt                |
| CORS         | Flask-CORS                          |
| DB Migration | Flask-Migrate (Alembic)             |

---

## Project Structure

```
clipconnect/
│
├── backend/
│   ├── app.py                  # Flask app entry point (Application Factory)
│   ├── config.py               # Environment-based config (Dev/Test/Prod)
│   ├── requirements.txt        # Python dependencies
│   ├── .env                    # Environment variables (NOT in Git!)
│   ├── .gitignore
│   │
│   ├── database/
│   │   └── __init__.py         # SQLAlchemy db instance
│   │
│   ├── models/
│   │   ├── __init__.py         # Registers all models
│   │   └── user_model.py       # User table (id, name, email, password, role)
│   │
│   ├── routes/
│   │   ├── __init__.py         # Blueprint registration
│   │   └── auth_routes.py      # /api/auth/* endpoints
│   │
│   ├── controllers/
│   │   ├── __init__.py
│   │   └── auth_controller.py  # Register, Login, GetMe business logic
│   │
│   ├── middleware/
│   │   ├── __init__.py
│   │   └── auth_middleware.py  # @token_required, @admin_required decorators
│   │
│   └── utils/
│       ├── __init__.py
│       ├── response_helper.py  # Standardized JSON responses
│       ├── validators.py       # Input validation functions
│       └── jwt_helper.py       # JWT generate / decode helpers
│
└── frontend/
    ├── index.html              # Landing page (Hero, Categories, Editors, Footer)
    ├── login.html              # Login page
    ├── register.html           # Registration page
    │
    ├── css/
    │   ├── variables.css       # Design system tokens (colors, fonts, spacing)
    │   ├── main.css            # Global styles, components, animations
    │   ├── navbar.css          # Navigation bar styles
    │   └── auth.css            # Login & Register page styles
    │
    ├── js/
    │   ├── api.js              # Fetch API wrapper + TokenManager
    │   ├── auth.js             # Form logic for login & register
    │   └── navbar.js           # Navbar scroll, hamburger, auth-aware
    │
    ├── images/                 # Static image assets
    └── assets/                 # Other assets (fonts, icons, etc.)
```

---

## 🚀 Features Built

### 1. Authentication & Onboarding
- **Role-based Auth:** Secure JWT registration and login for Clients, Editors, and Admins.
- **Password Strength:** Real-time UI strength meter.
- **Seeded Data:** Pre-populated Admin, Client, and Editor accounts for testing.

### 2. Client Portal (Dashboard)
- **Project Posting:** Clients can create projects with budget, deadlines, and requirements.
- **Hiring Workflow:** Send proposals and hire requests directly to freelance editors.
- **Escrow Payments:** Simulated Razorpay escrow system. Funds are held in escrow when an editor accepts a project.
- **Project Review:** Clients receive project submissions, can review watermarked files, request revisions, or accept the work.
- **Fund Release:** Upon acceptance, escrow funds are automatically released to the editor.

### 3. Editor Portal (Dashboard)
- **Profile Management:** Editors can setup professional profiles with portfolios, rates, categories, and availability status.
- **Proposal Management:** Accept or decline incoming hire requests.
- **Project Execution:** Upload draft submissions for client review.
- **Earnings & Stats:** Track completed projects, overall earnings, and client ratings.

### 4. Admin Control Panel
- **Live Analytics:** Comprehensive dashboard showing Total Users, Revenue, Active Projects, and Real-time Activity Feed.
- **User Moderation:** Admins can view all users, suspend or activate accounts, and track activity metrics.
- **Platform Oversight:** Monitor all platform projects, financial ledger (escrow, release, refund), and system notifications.

### 5. Tech Foundations
- **Frontend:** Responsive, glassmorphism UI built with pure HTML/CSS/JS.
- **Backend:** Flask REST API with SQLAlchemy ORM and PostgreSQL.
- **Robust Workflows:** Comprehensive error handling and unified API service integration (`api.js`).

---

## Setup Guide

### Prerequisites
- Python 3.10+ installed
- PostgreSQL 13+ installed and running
- Git installed
- A code editor (VS Code recommended)

---

### Step 1 — Clone / Open the Project

```bash
# If using Git
git clone <your-repo-url>
cd clipconnect

# Or just navigate to your project folder
cd "d:/Major project2.o"
```

---

### Step 2 — Create PostgreSQL Database

Open **pgAdmin** or the **PostgreSQL shell (psql)** and run:

```sql
-- Create the database
CREATE DATABASE clipconnect;

-- Verify it was created
\l
```

Or use psql from the command line:
```bash
psql -U postgres -c "CREATE DATABASE clipconnect;"
```

---

### Step 3 — Configure Environment Variables

Edit `backend/.env` and update your PostgreSQL credentials:

```env
DB_USERNAME=postgres
DB_PASSWORD=YOUR_ACTUAL_PASSWORD_HERE
DB_HOST=localhost
DB_PORT=5432
DB_NAME=clipconnect

DATABASE_URL=postgresql://postgres:YOUR_ACTUAL_PASSWORD_HERE@localhost:5432/clipconnect
```

---

### Step 4 — Set Up Python Virtual Environment

```bash
# Navigate to backend folder
cd backend

# Create virtual environment
python -m venv venv

# Activate it (Windows PowerShell)
.\venv\Scripts\Activate.ps1

# Activate it (Windows CMD)
venv\Scripts\activate.bat

# Activate it (Mac/Linux)
source venv/bin/activate

# You should see (venv) in your terminal prompt
```

---

### Step 5 — Install Python Dependencies

```bash
# Make sure you're in the backend/ folder with venv active
pip install -r requirements.txt
```

---

### Step 6 — Run the Flask Backend

```bash
# Still in backend/ folder with venv active
python app.py
```

You should see:
```
============================================================
  🎬 ClipConnect API Server
  🌐 Running at: http://localhost:5000
  📡 Health check: http://localhost:5000/api/health
  🔐 Auth API: http://localhost:5000/api/auth
  🐛 Debug mode: True
============================================================
```

---

### Step 7 — Open the Frontend

Open `frontend/index.html` in your browser using one of:

**Option A — VS Code Live Server (Recommended)**
1. Install the "Live Server" extension in VS Code
2. Right-click `frontend/index.html` → "Open with Live Server"
3. It opens at `http://127.0.0.1:5500`

**Option B — Direct file open**
1. Navigate to `frontend/` in File Explorer
2. Double-click `index.html`
3. Note: Some features may require Live Server for CORS to work correctly

---

### Step 8 — Test the API

**Using a browser — Health Check:**
```
http://localhost:5000/api/health
http://localhost:5000/api/auth/health
```

**Using PowerShell/curl — Register:**
```powershell
$body = '{"full_name":"Alex Johnson","email":"alex@example.com","password":"Secret@123","role":"client"}'
Invoke-RestMethod -Uri "http://localhost:5000/api/auth/register" -Method POST -Body $body -ContentType "application/json"
```

**Login:**
```powershell
$body = '{"email":"alex@example.com","password":"Secret@123"}'
Invoke-RestMethod -Uri "http://localhost:5000/api/auth/login" -Method POST -Body $body -ContentType "application/json"
```

---

## API Reference

### Base URL
```
http://localhost:5000/api
```

### Auth Endpoints

| Method | Endpoint | Auth Required | Description |
|--------|----------|---------------|-------------|
| GET | `/health` | No | Server health check |
| GET | `/auth/health` | No | Auth service health |
| POST | `/auth/register` | No | Register new user |
| POST | `/auth/login` | No | Login, get JWT |
| GET | `/auth/me` | Yes (Bearer Token) | Get current user |

---

### POST `/api/auth/register`

**Request Body:**
```json
{
  "full_name": "Alex Johnson",
  "email": "alex@example.com",
  "password": "Secret@123",
  "role": "client"
}
```

**Success Response (201):**
```json
{
  "success": true,
  "message": "Welcome to ClipConnect, Alex Johnson! Your account has been created.",
  "status_code": 201,
  "data": {
    "user": {
      "id": 1,
      "full_name": "Alex Johnson",
      "email": "alex@example.com",
      "role": "client",
      "profile_image": null,
      "is_active": true,
      "is_verified": false,
      "created_at": "2025-01-01T12:00:00+00:00"
    }
  }
}
```

**Error Response (409 — Email Exists):**
```json
{
  "success": false,
  "message": "This email address is already registered.",
  "status_code": 409,
  "errors": { "email": "Email already exists" }
}
```

---

### POST `/api/auth/login`

**Request Body:**
```json
{
  "email": "alex@example.com",
  "password": "Secret@123"
}
```

**Success Response (200):**
```json
{
  "success": true,
  "message": "Welcome back, Alex Johnson!",
  "status_code": 200,
  "data": {
    "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "token_type": "Bearer",
    "expires_in": 3600,
    "user": { "id": 1, "full_name": "Alex Johnson", "role": "client", ... }
  }
}
```

---

### GET `/api/auth/me`

**Headers:**
```
Authorization: Bearer <your_jwt_token>
```

**Success Response (200):**
```json
{
  "success": true,
  "message": "Profile fetched successfully.",
  "data": {
    "user": { "id": 1, "full_name": "Alex Johnson", "role": "client", ... }
  }
}
```

---

## Frontend Pages

| Page | File | Description |
|------|------|-------------|
| Home | `frontend/index.html` | Landing page with hero, categories, editor cards, how-it-works, footer |
| Register | `frontend/register.html` | Registration form with role selector + password strength |
| Login | `frontend/login.html` | Login form with JWT-based auth |

---

## Environment Variables

| Variable | Example Value | Description |
|----------|---------------|-------------|
| `FLASK_ENV` | `development` | Environment mode |
| `SECRET_KEY` | `your-secret-key` | Flask session secret |
| `DATABASE_URL` | `postgresql://postgres:pass@localhost:5432/clipconnect` | Full DB URL |
| `JWT_SECRET_KEY` | `your-jwt-secret` | JWT signing key |
| `JWT_ACCESS_TOKEN_EXPIRES` | `3600` | Token expiry in seconds |
| `CORS_ORIGINS` | `http://localhost:5500` | Allowed frontend origins |

---

## Database Schema

### `users` Table

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY, AUTO INCREMENT | Unique user ID |
| `full_name` | VARCHAR(150) | NOT NULL | User's full name |
| `email` | VARCHAR(255) | UNIQUE, NOT NULL, INDEX | Login email |
| `password` | VARCHAR(255) | NOT NULL | bcrypt hash |
| `role` | ENUM | NOT NULL, DEFAULT 'client' | client / editor / admin |
| `profile_image` | VARCHAR(500) | NULLABLE | Profile picture URL |
| `is_active` | BOOLEAN | NOT NULL, DEFAULT true | Account active status |
| `is_verified` | BOOLEAN | NOT NULL, DEFAULT false | Email verification flag |
| `created_at` | TIMESTAMP+TZ | NOT NULL | Account creation time |
| `updated_at` | TIMESTAMP+TZ | NOT NULL | Last update time |

---

## 🏆 Project Completion Status

ClipConnect is now **fully functional**!
All major workflows (Authentication, Hiring, Escrow Payments, Project Review, Submissions, Admin Dashboard) are 100% complete and integrated.

---

*Built with ❤️ for ClipConnect*
*By Sathish*