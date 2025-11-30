# 🚀 Complete Deployment Guide for Tinko.in

## Overview

This guide covers deploying:
1. **Backend API** (FastAPI) → `api.tinko.in`
2. **Frontend** (Landing Page + Dashboard) → `tinko.in`
3. **Database** (PostgreSQL/SQLite)
4. **Environment Configuration**
5. **SSL Certificates**
6. **DNS Setup**

---

## 📋 Prerequisites

### What You Need:
- ✅ A server (VPS) - DigitalOcean, AWS, Azure, or any cloud provider
- ✅ Domain name: `tinko.in` (you already have this)
- ✅ SSH access to your server
- ✅ GitHub repository access
- ✅ Basic Linux/Ubuntu knowledge

### Recommended Server Specs:
- **OS:** Ubuntu 20.04 or 22.04 LTS
- **RAM:** 2GB minimum (4GB recommended)
- **CPU:** 2 cores
- **Storage:** 20GB SSD
- **Cost:** ~$10-20/month

---

## 🎯 Deployment Architecture

```
tinko.in (Frontend)
    ↓
    ├── Landing Page (index.html)
    ├── Dashboard (dashboard/*)
    └── Static Assets

api.tinko.in (Backend)
    ↓
    ├── FastAPI Application
    ├── Database (PostgreSQL)
    └── Redis (for caching)
```

---

## Part 1️⃣: Server Setup

### Step 1: Create a Server

**Option A: DigitalOcean (Recommended for beginners)**
1. Go to https://www.digitalocean.com
2. Create a new Droplet
3. Choose Ubuntu 22.04
4. Select $12/month plan (2GB RAM)
5. Add SSH key or use password
6. Create droplet

**Option B: AWS EC2**
1. Launch EC2 instance
2. Choose Ubuntu 22.04 AMI
3. Select t2.small or t3.small
4. Configure security groups (ports 80, 443, 22)

**Option C: Azure, Google Cloud, etc.**
Similar process - create Ubuntu VM with at least 2GB RAM

---

### Step 2: Connect to Your Server

```bash
# From your local machine, connect via SSH
ssh root@YOUR_SERVER_IP

# Example:
ssh root@165.232.123.45
```

---

### Step 3: Initial Server Setup

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install essential tools
sudo apt install -y git curl wget vim nginx python3-pip python3-venv postgresql postgresql-contrib redis-server certbot python3-certbot-nginx

# Create a non-root user (recommended)
adduser tinko
usermod -aG sudo tinko

# Switch to the new user
su - tinko
```

---

## Part 2️⃣: Backend Deployment

### Step 1: Clone Backend Repository

```bash
# Navigate to home directory
cd ~

# Clone your backend repo
git clone https://github.com/stealthorga-crypto/Tinko-clean-backend.git
cd Tinko-clean-backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

---

### Step 2: Setup Database

**Option A: PostgreSQL (Recommended for Production)**

```bash
# Create database and user
sudo -u postgres psql

# In PostgreSQL shell:
CREATE DATABASE tinko_db;
CREATE USER tinko_user WITH PASSWORD 'your_secure_password_here';
GRANT ALL PRIVILEGES ON DATABASE tinko_db TO tinko_user;
\q
```

**Option B: Keep SQLite (Easier for MVP)**
```bash
# Just use the existing SQLite database
# No additional setup needed
```

---

### Step 3: Configure Environment Variables

```bash
# Create .env file
cd ~/Tinko-clean-backend
nano .env
```

**Add these variables:**

```bash
# Database
DATABASE_URL=postgresql://tinko_user:your_secure_password_here@localhost/tinko_db
# Or for SQLite:
# DATABASE_URL=sqlite:///./tinko.db

# JWT Secret (generate a secure random string)
JWT_SECRET=your_super_secret_jwt_key_change_this_in_production_543210

# Supabase (for OTP authentication)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_supabase_anon_key

# Razorpay (for payments)
RAZORPAY_KEY_ID=your_razorpay_key_id
RAZORPAY_KEY_SECRET=your_razorpay_secret

# Stripe (optional)
STRIPE_SECRET_KEY=your_stripe_secret_key
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret

# Application
ENVIRONMENT=production
PUBLIC_BASE_URL=https://api.tinko.in
FRONTEND_URL=https://tinko.in

# CORS Origins (important!)
ALLOWED_ORIGINS=https://tinko.in,https://www.tinko.in
```

Save and exit (Ctrl+X, Y, Enter)

---

### Step 4: Run Database Migrations

```bash
# Activate virtual environment
source venv/bin/activate

# Run migrations (if you have Alembic)
alembic upgrade head

# Or initialize the database manually
python -c "from app.db import Base, engine; Base.metadata.create_all(bind=engine)"
```

---

### Step 5: Test Backend Locally

```bash
# Test if the backend runs
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Test from another terminal or browser
curl http://YOUR_SERVER_IP:8000/health

# If it works, stop with Ctrl+C
```

---

### Step 6: Setup Systemd Service (Keep Backend Running)

```bash
# Create service file
sudo nano /etc/systemd/system/tinko-backend.service
```

**Add this content:**

```ini
[Unit]
Description=Tinko Backend API
After=network.target

[Service]
Type=simple
User=tinko
WorkingDirectory=/home/tinko/Tinko-clean-backend
Environment="PATH=/home/tinko/Tinko-clean-backend/venv/bin"
ExecStart=/home/tinko/Tinko-clean-backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Enable and start the service:**

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable service to start on boot
sudo systemctl enable tinko-backend

# Start the service
sudo systemctl start tinko-backend

# Check status
sudo systemctl status tinko-backend

# View logs
sudo journalctl -u tinko-backend -f
```

---

### Step 7: Configure Nginx for Backend

```bash
# Create Nginx config for backend
sudo nano /etc/nginx/sites-available/api.tinko.in
```

**Add this content:**

```nginx
server {
    listen 80;
    server_name api.tinko.in;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support (if needed)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

**Enable the site:**

```bash
# Create symbolic link
sudo ln -s /etc/nginx/sites-available/api.tinko.in /etc/nginx/sites-enabled/

# Test Nginx configuration
sudo nginx -t

# Reload Nginx
sudo systemctl reload nginx
```

---

## Part 3️⃣: Frontend Deployment

### Step 1: Upload Frontend Files

**Option A: Use Git (Recommended)**

```bash
# On your server
cd ~
git clone https://github.com/YOUR_USERNAME/tinko-frontend.git
# Or if you don't have a frontend repo yet, use SCP/SFTP to upload files
```

**Option B: Upload via SCP from your local machine**

```bash
# From your local machine (Windows PowerShell)
cd "C:\Users\sadis\OneDrive\Desktop\Tinko full"

# Upload to server
scp -r tinko_prelaunch_landing_page/* tinko@YOUR_SERVER_IP:/home/tinko/frontend/
```

---

### Step 2: Update API URLs in Frontend

```bash
# On the server
cd ~/frontend  # or wherever you uploaded files

# Update auth.js to use production API URL
nano auth.js
```

**Change:**
```javascript
const API_BASE = "http://127.0.0.1:8000";  // OLD
```

**To:**
```javascript
const API_BASE = "https://api.tinko.in";  // NEW
```

**Also update in:**
- `dashboard/onboarding.html`
- Any other files that reference the API

---

### Step 3: Configure Nginx for Frontend

```bash
# Create Nginx config for frontend
sudo nano /etc/nginx/sites-available/tinko.in
```

**Add this content:**

```nginx
server {
    listen 80;
    server_name tinko.in www.tinko.in;
    root /home/tinko/frontend;
    index index.html;

    # Gzip compression
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;

    location / {
        try_files $uri $uri/ =404;
    }

    # Cache static assets
    location ~* \.(jpg|jpeg|png|gif|ico|css|js|webp)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

**Enable the site:**

```bash
# Create symbolic link
sudo ln -s /etc/nginx/sites-available/tinko.in /etc/nginx/sites-enabled/

# Test Nginx
sudo nginx -t

# Reload Nginx
sudo systemctl reload nginx
```

---

## Part 4️⃣: DNS Configuration

### Step 1: Point Domain to Server

Log in to your domain registrar (GoDaddy, Namecheap, etc.) and add these DNS records:

```
Type    Name        Value                   TTL
A       @           YOUR_SERVER_IP          3600
A       www         YOUR_SERVER_IP          3600
A       api         YOUR_SERVER_IP          3600
CNAME   www         tinko.in                3600
```

**Example with IP 165.232.123.45:**
```
A       @           165.232.123.45          3600
A       www         165.232.123.45          3600
A       api         165.232.123.45          3600
```

**Wait 10-60 minutes for DNS propagation**

---

## Part 5️⃣: SSL Certificates (HTTPS)

### Setup Free SSL with Let's Encrypt

```bash
# Install Certbot (should already be installed)
sudo apt install certbot python3-certbot-nginx -y

# Get SSL for main domain
sudo certbot --nginx -d tinko.in -d www.tinko.in

# Get SSL for API subdomain
sudo certbot --nginx -d api.tinko.in

# Follow the prompts:
# - Enter email
# - Agree to terms
# - Choose to redirect HTTP to HTTPS (recommended)

# Test auto-renewal
sudo certbot renew --dry-run
```

**Certbot will automatically:**
- Generate SSL certificates
- Update Nginx configs
- Setup auto-renewal

---

## Part 6️⃣: Verify Deployment

### Check if Everything Works:

**1. Backend API:**
```bash
curl https://api.tinko.in/health
# Should return: {"status": "ok"}

curl https://api.tinko.in/docs
# Should show Swagger UI
```

**2. Frontend:**
```bash
curl https://tinko.in
# Should return HTML content

curl https://www.tinko.in
# Should also work
```

**3. Test in Browser:**
- Visit https://tinko.in
- Try the login flow
- Complete onboarding
- Access dashboard

---

## Part 7️⃣: Update & Redeploy (Future Updates)

### When You Make Changes:

**Backend Updates:**
```bash
# SSH into server
ssh tinko@YOUR_SERVER_IP

# Pull latest changes
cd ~/Tinko-clean-backend
git pull origin main

# Activate venv and install any new dependencies
source venv/bin/activate
pip install -r requirements.txt

# Restart service
sudo systemctl restart tinko-backend

# Check logs
sudo journalctl -u tinko-backend -f
```

**Frontend Updates:**
```bash
# Upload new files or pull from git
cd ~/frontend
git pull origin main

# No restart needed - files are served directly by Nginx
```

---

## Part 8️⃣: Monitoring & Maintenance

### Check Service Status:
```bash
# Backend status
sudo systemctl status tinko-backend

# Backend logs
sudo journalctl -u tinko-backend -n 100 --no-pager

# Nginx status
sudo systemctl status nginx

# Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### Database Backup:
```bash
# For PostgreSQL
pg_dump -U tinko_user tinko_db > backup_$(date +%Y%m%d).sql

# For SQLite
cp ~/Tinko-clean-backend/tinko.db ~/backups/tinko_$(date +%Y%m%d).db
```

---

## 🎯 Quick Deployment Checklist

- [ ] Server created and accessible via SSH
- [ ] Backend cloned from GitHub
- [ ] Database setup (PostgreSQL or SQLite)
- [ ] Environment variables configured (.env file)
- [ ] Backend service running (systemd)
- [ ] Frontend files uploaded
- [ ] API URLs updated in frontend
- [ ] Nginx configured for both frontend and backend
- [ ] DNS records pointing to server
- [ ] SSL certificates installed
- [ ] Test login flow works
- [ ] Test onboarding works
- [ ] Test payment failure flow
- [ ] Setup monitoring and backups

---

## 💰 Estimated Costs

- **Server (DigitalOcean):** $12/month
- **Domain (tinko.in):** Already owned
- **SSL Certificates:** Free (Let's Encrypt)
- **Supabase (Free tier):** $0/month
- **Total:** ~$12/month

---

## 🆘 Troubleshooting

### Issue: Can't access api.tinko.in
```bash
# Check if backend is running
sudo systemctl status tinko-backend

# Check Nginx config
sudo nginx -t

# Check DNS
nslookup api.tinko.in
```

### Issue: CORS errors
Update `.env` in backend:
```bash
ALLOWED_ORIGINS=https://tinko.in,https://www.tinko.in
```

Then restart:
```bash
sudo systemctl restart tinko-backend
```

### Issue: Database connection error
Check DATABASE_URL in `.env` and verify PostgreSQL is running:
```bash
sudo systemctl status postgresql
```

---

## 📚 Additional Resources

- **Nginx Docs:** https://nginx.org/en/docs/
- **Let's Encrypt:** https://letsencrypt.org/
- **FastAPI Deployment:** https://fastapi.tiangolo.com/deployment/
- **DigitalOcean Tutorials:** https://www.digitalocean.com/community/tutorials

---

## ✅ You're Done!

Your application is now live at:
- **Frontend:** https://tinko.in
- **API:** https://api.tinko.in
- **API Docs:** https://api.tinko.in/docs

**Need help?** Review the logs or reach out for support!
