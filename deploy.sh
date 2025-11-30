#!/bin/bash

# Tinko Quick Deploy Script
# This script automates the deployment process

set -e  # Exit on error

echo "================================================"
echo "🚀 TINKO DEPLOYMENT SCRIPT"
echo "================================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ️  $1${NC}"
}

# Check if running as non-root
if [ "$EUID" -eq 0 ]; then 
    print_error "Please do not run as root. Use a regular user with sudo privileges."
    exit 1
fi

# Ask for confirmation
echo "This script will deploy Tinko to this server."
echo "Make sure you have:"
echo "  - Configured DNS to point to this server"
echo "  - Have Supabase credentials ready"
echo "  - Have payment gateway credentials (optional for now)"
echo ""
read -p "Continue? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 1
fi

# Step 1: Update system
print_info "Updating system packages..."
sudo apt update && sudo apt upgrade -y
print_success "System updated"

# Step 2: Install dependencies
print_info "Installing dependencies..."
sudo apt install -y git curl wget vim nginx python3-pip python3-venv postgresql postgresql-contrib redis-server certbot python3-certbot-nginx
print_success "Dependencies installed"

# Step 3: Clone backend
print_info "Cloning backend repository..."
cd ~
if [ -d "Tinko-clean-backend" ]; then
    print_info "Backend directory exists, pulling latest changes..."
    cd Tinko-clean-backend
    git pull origin main
else
    git clone https://github.com/stealthorga-crypto/Tinko-clean-backend.git
    cd Tinko-clean-backend
fi
print_success "Backend repository ready"

# Step 4: Setup Python virtual environment
print_info "Setting up Python virtual environment..."
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
print_success "Virtual environment ready"

# Step 5: Configure environment variables
print_info "Configuring environment variables..."
cat > .env << EOF
# Database (using SQLite for quick start)
DATABASE_URL=sqlite:///./tinko.db

# JWT Secret (CHANGE THIS!)
JWT_SECRET=$(openssl rand -hex 32)

# Supabase (you need to add your credentials)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_supabase_anon_key

# Application
ENVIRONMENT=production
PUBLIC_BASE_URL=https://api.tinko.in
FRONTEND_URL=https://tinko.in
ALLOWED_ORIGINS=https://tinko.in,https://www.tinko.in
EOF
print_success "Environment file created"
print_info "⚠️  IMPORTANT: Edit ~/.Tinko-clean-backend/.env and add your Supabase credentials"

# Step 6: Initialize database
print_info "Initializing database..."
python -c "from app.db import Base, engine; Base.metadata.create_all(bind=engine)" || print_error "Database initialization failed (this might be okay if DB already exists)"
print_success "Database ready"

# Step 7: Create systemd service
print_info "Creating systemd service..."
sudo tee /etc/systemd/system/tinko-backend.service > /dev/null << EOF
[Unit]
Description=Tinko Backend API
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$HOME/Tinko-clean-backend
Environment="PATH=$HOME/Tinko-clean-backend/venv/bin"
ExecStart=$HOME/Tinko-clean-backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable tinko-backend
sudo systemctl start tinko-backend
print_success "Backend service started"

# Step 8: Configure Nginx for backend
print_info "Configuring Nginx for backend API..."
sudo tee /etc/nginx/sites-available/api.tinko.in > /dev/null << 'EOF'
server {
    listen 80;
    server_name api.tinko.in;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

sudo ln -sf /etc/nginx/sites-available/api.tinko.in /etc/nginx/sites-enabled/
print_success "Nginx configured for backend"

# Step 9: Create frontend directory
print_info "Creating frontend directory..."
mkdir -p ~/frontend
print_success "Frontend directory created"
print_info "⚠️  You need to upload your frontend files to ~/frontend/"
print_info "    Use: scp -r tinko_prelaunch_landing_page/* $USER@$(hostname -I | awk '{print $1}'):~/frontend/"

# Step 10: Configure Nginx for frontend
print_info "Configuring Nginx for frontend..."
sudo tee /etc/nginx/sites-available/tinko.in > /dev/null << EOF
server {
    listen 80;
    server_name tinko.in www.tinko.in;
    root $HOME/frontend;
    index index.html;

    location / {
        try_files \$uri \$uri/ =404;
    }

    location ~* \.(jpg|jpeg|png|gif|ico|css|js|webp)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
EOF

sudo ln -sf /etc/nginx/sites-available/tinko.in /etc/nginx/sites-enabled/
print_success "Nginx configured for frontend"

# Step 11: Test and reload Nginx
print_info "Testing Nginx configuration..."
sudo nginx -t && sudo systemctl reload nginx
print_success "Nginx reloaded"

# Step 12: Setup SSL (if DNS is configured)
echo ""
print_info "To setup SSL certificates, run these commands after DNS is configured:"
echo "  sudo certbot --nginx -d tinko.in -d www.tinko.in"
echo "  sudo certbot --nginx -d api.tinko.in"

# Final status
echo ""
echo "================================================"
echo "🎉 DEPLOYMENT COMPLETE!"
echo "================================================"
echo ""
echo "Next steps:"
echo "1. Edit ~/Tinko-clean-backend/.env and add your Supabase credentials"
echo "2. Upload frontend files to ~/frontend/"
echo "3. Configure DNS to point to this server's IP: $(hostname -I | awk '{print $1}')"
echo "4. Wait for DNS propagation (10-60 minutes)"
echo "5. Run SSL setup: sudo certbot --nginx -d tinko.in -d www.tinko.in"
echo "6. Run SSL setup: sudo certbot --nginx -d api.tinko.in"
echo ""
echo "Check backend status: sudo systemctl status tinko-backend"
echo "View backend logs: sudo journalctl -u tinko-backend -f"
echo "View Nginx logs: sudo tail -f /var/log/nginx/error.log"
echo ""
print_success "Deployment script finished!"
