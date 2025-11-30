# 🎯 Tinko Authentication & Onboarding Flow

## Overview
This document explains how the authentication and user routing works in the Tinko platform.

---

## 📋 Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    Landing Page (index.html)                │
│                                                               │
│  User clicks "Login with OTP"                                │
└───────────────────┬─────────────────────────────────────────┘
                    │
                    ├── Step 1: User enters email
                    │   POST /v1/auth/email/send-otp
                    │
                    ├── Step 2: User enters OTP code
                    │   POST /v1/auth/email/verify-otp
                    │   → Returns access_token
                    ▼
┌─────────────────────────────────────────────────────────────┐
│             auth.js: handlePostLoginRedirect()               │
│                                                               │
│  1. Save token to localStorage                               │
│  2. Call GET /v1/customer/profile                            │
│                                                               │
└───────────────────┬─────────────────────────────────────────┘
                    │
         ┌──────────┴──────────┐
         │                     │
         ▼                     ▼
    ┌────────┐           ┌────────┐
    │ 200 OK │           │  404   │
    └────┬───┘           └───┬────┘
         │                   │
         │                   │
    ┌────▼──────────┐   ┌────▼──────────────┐
    │  User exists  │   │  New User (First  │
    │  with org_id  │   │  time login OR    │
    │               │   │  no org_id)       │
    └────┬──────────┘   └────┬──────────────┘
         │                   │
         │                   │
         ▼                   ▼
  ┌──────────────┐    ┌──────────────────┐
  │  Dashboard   │    │   Onboarding     │
  │  index.html  │    │   Form           │
  │              │    │   onboarding.html│
  └──────────────┘    └──────┬───────────┘
                             │
                             │ User fills form
                             │ POST /v1/customer/profile
                             │ → Creates org & profile
                             │
                             ▼
                      ┌──────────────┐
                      │  Dashboard   │
                      │  index.html  │
                      └──────────────┘
```

---

## 🔐 Backend Endpoints

### 1. **GET /v1/customer/profile**
**Purpose:** Check if user profile exists and is complete

**Response Scenarios:**
- **404 Not Found** → User needs onboarding
  - New user (no database record)
  - Existing user without `org_id`
  
- **200 OK** → User profile complete, show dashboard
  ```json
  {
    "email": "user@example.com",
    "full_name": "Acme Store",
    "mobile": "+91 98765 43210",
    "org_id": 123,
    "onboarding_complete": true
  }
  ```

### 2. **POST /v1/customer/profile**
**Purpose:** Save onboarding data and create organization

**Request Body:**
```json
{
  "business_name": "Acme Store",
  "phone": "+91 98765 43210",
  "payment_gateway": "razorpay",
  "website": "https://acme.com",
  "monthly_volume": "500-1000"
}
```

**What it does:**
1. Creates a new `Organization` with a unique slug
2. Links the user to that organization (`org_id`)
3. Updates user's `full_name` and `mobile_number`
4. Returns the complete profile

---

## 📁 File Structure

```
tinko_prelaunch_landing_page/
│
├── index.html              # Landing page with OTP login
├── auth.js                 # Authentication logic
│
└── dashboard/
    ├── auth-guard.js       # Protects dashboard pages (checks token)
    ├── logout.js           # Logout functionality
    ├── onboarding.html     # NEW USER: Signup form
    └── index.html          # RETURNING USER: Dashboard
```

---

## 🎨 Features Implemented

### ✅ Landing Page (`index.html`)
- Modern, premium design with Tinko branding
- OTP-based authentication (no passwords)
- Two-step login process

### ✅ Onboarding Form (`dashboard/onboarding.html`)
- Beautiful, branded signup form
- Collects:
  - Business name *
  - Phone number *
  - Payment gateway *
  - Website (optional)
  - Monthly transaction volume (optional)
- Real-time validation
- Backend integration with POST /v1/customer/profile

### ✅ Dashboard (`dashboard/index.html`)
- Premium glassmorphism design
- Stats cards (revenue recovered, failed payments, recovery rate)
- Quick action buttons
- Profile loading from backend
- Logout functionality

### ✅ Authentication (`auth.js`)
- Handles OTP send/verify
- Token storage in localStorage
- Automatic routing:
  - New user → `onboarding.html`
  - Returning user → `dashboard/index.html`

---

## 🚀 How to Test

### 1. Start the backend server
```powershell
cd "Tinko full\tinko-backend-clean"
uvicorn app.main:app --reload --port 8000
```

### 2. Open the landing page
```powershell
cd "Tinko full\tinko_prelaunch_landing_page"
# Open index.html in browser
```

### 3. Test the flow
1. Enter your email → Click "Send OTP"
2. Check your email for the OTP code
3. Enter OTP → Click "Verify OTP"
4. **First time:** You'll see onboarding form
   - Fill in business details → Click "Complete Setup"
   - Redirected to dashboard
5. **Logout and login again:** You'll go straight to dashboard

---

## 🎯 Next Steps

You can enhance this further by:
- Adding transaction analytics to the dashboard
- Creating settings page for profile updates
- Adding email preferences
- Implementing API key generation for merchants
- Building the payment recovery tracking interface

---

**Need help?** Contact the Tinko team at contact@tinko.in
