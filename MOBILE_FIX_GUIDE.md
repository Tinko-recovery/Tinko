# 🔧 Fix Mobile Backend Connection Issue

## Problem
- ✅ Works on laptop
- ❌ Doesn't work on mobile
- Error: "Backend unreachable"

## Root Cause
Your code is using `http://127.0.0.1:8000` which only works on your laptop. Mobile devices can't reach "localhost" of your laptop.

---

## ✅ Solution: Update to Your Render Backend URL

### Step 1: Get Your Render Backend URL

1. Go to https://dashboard.render.com
2. Find your backend service
3. Copy the URL (something like: `https://tinko-backend-xyz.onrender.com`)

### Step 2: Update These Files

You need to update the API URL in **2 files**:

#### **File 1: `auth.js`** (Line 12)

**Change from:**
```javascript
const API_BASE = "http://127.0.0.1:8000";
```

**Change to:**
```javascript
const API_BASE = "https://your-actual-render-url.onrender.com";
```

**Example:**
```javascript
const API_BASE = "https://tinko-backend-xyz.onrender.com";
```

---

#### **File 2: `dashboard/onboarding.html`** (Around line 172)

Find this line:
```javascript
const API_BASE = "http://127.0.0.1:8000";
```

Replace with:
```javascript
const API_BASE = "https://your-actual-render-url.onrender.com";
```

---

### Step 3: Push Changes to GitHub

```bash
cd "C:\Users\sadis\OneDrive\Desktop\Tinko full\tinko_prelaunch_landing_page"

# Add changes
git add auth.js dashboard/onboarding.html

# Commit
git commit -m "fix: Update API URL to Render backend for mobile access"

# Push
git push origin main
```

---

### Step 4: Update CORS on Backend

Make sure your backend allows requests from tinko.in.

**Check your backend `.env` or `main.py`:**

```python
# In main.py, add your domain to CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://tinko.in",
        "https://www.tinko.in",
        "http://localhost:3000",  # for local testing
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

Push this change to your backend repo and Render will auto-deploy.

---

### Step 5: Render Will Auto-Deploy

1. Render detects your GitHub push
2. Automatically rebuilds and deploys
3. Wait 2-3 minutes for deployment
4. Test on mobile again

---

## 🧪 Testing

### Test on Laptop:
1. Go to https://tinko.in
2. Enter email
3. Get OTP
4. Should work ✅

### Test on Mobile:
1. Go to https://tinko.in
2. Enter email
3. Get OTP
4. Should now work ✅

---

## 🔍 How to Find Your Render Backend URL

### Option 1: From Render Dashboard
1. Log in to https://dashboard.render.com
2. Click on your backend service
3. Look for the URL at the top (usually ends with `.onrender.com`)

### Option 2: Check Your Deployed API
1. Visit: https://your-backend.onrender.com/docs
2. You should see the Swagger API documentation

### Option 3: Test Health Endpoint
```bash
curl https://your-backend.onrender.com/health
```
Should return: `{"status": "ok"}`

---

## 📝 Quick Fix Checklist

- [ ] Get Render backend URL from dashboard
- [ ] Update `auth.js` line ~12
- [ ] Update `dashboard/onboarding.html` line ~172
- [ ] Push to GitHub
- [ ] Wait for Render to deploy (2-3 min)
- [ ] Test on laptop - should still work
- [ ] Test on mobile - should now work
- [ ] Check browser console for errors if still failing

---

## 🚨 Common Issues

### Issue 1: CORS Error
**Symptom:** "Access to fetch...blocked by CORS policy"

**Fix:** Update CORS in backend to include tinko.in

### Issue 2: Mixed Content Error
**Symptom:** "Mixed Content: The page at 'https://...' was loaded over HTTPS, but requested an insecure resource 'http://...'"

**Fix:** Make sure API_BASE uses `https://` not `http://`

### Issue 3: Certificate Error
**Symptom:** "NET::ERR_CERT_AUTHORITY_INVALID"

**Fix:** Render provides free SSL. Make sure you're using the Render URL (ends with .onrender.com)

---

## 📍 Exact Changes Needed

### In `auth.js` (Line 12):
```javascript
// BEFORE
const API_BASE = "http://127.0.0.1:8000";

// AFTER (replace with your actual Render URL)
const API_BASE = "https://tinko-backend-abc123.onrender.com";
```

### In `dashboard/onboarding.html` (Around line 172):
```javascript
// BEFORE
const API_BASE = "http://127.0.0.1:8000";

// AFTER (same URL as above)
const API_BASE = "https://tinko-backend-abc123.onrender.com";
```

---

## ✅ After Fix

Once you update and push:

1. **Render auto-deploys** (2-3 minutes)
2. **Mobile will work** - can reach Render's public URL
3. **Laptop will work** - can also reach Render's public URL
4. **Both use same backend** - consistent behavior

---

## 💡 Pro Tip: Environment-Based URLs

For future, you can make the URL smart:

```javascript
const API_BASE = window.location.hostname === 'localhost'
  ? "http://127.0.0.1:8000"  // Local development
  : "https://your-backend.onrender.com";  // Production
```

This way you don't need to change it when testing locally!

---

**Need Help Finding Your Render URL?**

It's in your Render dashboard, looks like:
- `https://tinko-backend.onrender.com`
- `https://tinko-api-xyz.onrender.com`
- Or similar

Just copy whatever URL Render gave you for your backend service!
