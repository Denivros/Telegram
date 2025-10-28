#!/bin/bash
# 
# Hostinger Ubuntu VPS - MT5 Trading Bot Auto-Setup Script
# This script automates the entire installation process
#

set -e  # Exit on any error

echo "🚀 Starting MT5 Trading Bot Setup on Ubuntu VPS..."
echo "=================================================="

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   print_error "This script must be run as root (use sudo)"
   exit 1
fi

# Get system info
print_status "Detecting system information..."
OS_VERSION=$(lsb_release -rs 2>/dev/null || echo "unknown")
ARCH=$(uname -m)
print_success "Ubuntu $OS_VERSION detected ($ARCH)"

# Step 1: System Update
print_status "Step 1: Updating system packages..."
apt update && apt upgrade -y
print_success "System updated successfully"

# Step 2: Install Dependencies
print_status "Step 2: Installing dependencies..."
apt install -y \
    curl \
    wget \
    git \
    unzip \
    software-properties-common \
    python3 \
    python3-pip \
    python3-venv \
    htop \
    screen \
    nano

print_success "Basic dependencies installed"

# Step 3: Install Wine
print_status "Step 3: Installing Wine..."
dpkg --add-architecture i386
apt update

# Install Wine from official repository
apt install -y wine wine32 wine64 winetricks

# Verify Wine installation
if command -v wine &> /dev/null; then
    WINE_VERSION=$(wine --version)
    print_success "Wine installed: $WINE_VERSION"
else
    print_error "Wine installation failed"
    exit 1
fi

# Step 4: Install Display System
print_status "Step 4: Installing virtual display system..."
apt install -y xvfb x11vnc fluxbox

print_success "Virtual display system installed"

# Step 5: Create Trading Bot User (Optional but recommended)
print_status "Step 5: Setting up trading bot environment..."
BOT_USER="trader"
BOT_HOME="/home/$BOT_USER"

# Create user if doesn't exist
if ! id "$BOT_USER" &>/dev/null; then
    useradd -m -s /bin/bash "$BOT_USER"
    print_success "Created user: $BOT_USER"
else
    print_warning "User $BOT_USER already exists"
fi

# Step 6: Setup Wine Environment for Bot User
print_status "Step 6: Configuring Wine environment..."
sudo -u "$BOT_USER" bash << 'EOF'
export WINEARCH=win64
export WINEPREFIX=$HOME/.wine-mt5

# Initialize Wine (non-interactive)
echo "Setting up Wine prefix..."
wineboot --init

# Install Windows components
echo "Installing Windows components..."
winetricks -q corefonts vcrun2019 vcrun2015 msvcrt

echo "Wine environment configured"
EOF

print_success "Wine environment configured for $BOT_USER"

# Step 7: Create Project Directory
print_status "Step 7: Creating project directories..."
PROJECT_DIR="$BOT_HOME/trading-bot"
sudo -u "$BOT_USER" mkdir -p "$PROJECT_DIR/simple-direct"
sudo -u "$BOT_USER" mkdir -p "$PROJECT_DIR/logs"
sudo -u "$BOT_USER" mkdir -p "$PROJECT_DIR/backups"

print_success "Project directories created"

# Step 8: Download and Install MT5
print_status "Step 8: Downloading MetaTrader 5..."
cd "$PROJECT_DIR"

# Download MT5 installer
sudo -u "$BOT_USER" wget -O mt5setup.exe "https://download.mql5.com/cdn/web/metaquotes.software.corp/mt5/mt5setup.exe"

print_success "MT5 installer downloaded"

# Step 9: Download Python Windows Installer
print_status "Step 9: Downloading Python for Windows..."
sudo -u "$BOT_USER" wget -O python-installer.exe "https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe"

print_success "Python installer downloaded"

# Step 10: Create Virtual Display Startup Script
print_status "Step 10: Creating startup scripts..."

cat > "$BOT_HOME/start-display.sh" << 'EOF'
#!/bin/bash
# Start virtual display for MT5
export DISPLAY=:99
echo "Starting virtual display..."
Xvfb :99 -screen 0 1024x768x24 -ac &
sleep 2
export DISPLAY=:99
fluxbox &
sleep 1
echo "Virtual display started on :99"
EOF

chown "$BOT_USER:$BOT_USER" "$BOT_HOME/start-display.sh"
chmod +x "$BOT_HOME/start-display.sh"

# Step 11: Create Installation Script for User
cat > "$BOT_HOME/install-mt5-python.sh" << 'EOF'
#!/bin/bash
# Install MT5 and Python in Wine (run as trader user)

export WINEARCH=win64
export WINEPREFIX=$HOME/.wine-mt5
export DISPLAY=:99

echo "Starting virtual display..."
$HOME/start-display.sh

echo "Installing MetaTrader 5..."
cd ~/trading-bot
wine mt5setup.exe /S  # Silent installation

echo "Installing Python in Wine..."
wine python-installer.exe /quiet InstallAllUsers=0 PrependPath=1

echo "Waiting for installations to complete..."
sleep 30

echo "Installing Python packages..."
wine python -m pip install --upgrade pip
wine python -m pip install MetaTrader5 telethon requests python-dotenv

echo "Installation complete!"
EOF

chown "$BOT_USER:$BOT_USER" "$BOT_HOME/install-mt5-python.sh"
chmod +x "$BOT_HOME/install-mt5-python.sh"

# Step 12: Create System Service Template
print_status "Step 11: Creating systemd service template..."

cat > /etc/systemd/system/mt5-trading-bot.service << EOF
[Unit]
Description=MT5 Trading Bot
After=network.target

[Service]
Type=simple
User=$BOT_USER
Group=$BOT_USER
WorkingDirectory=$PROJECT_DIR/simple-direct
Environment=DISPLAY=:99
Environment=WINEARCH=win64
Environment=WINEPREFIX=$BOT_HOME/.wine-mt5
ExecStartPre=$BOT_HOME/start-display.sh
ExecStart=/usr/bin/wine $BOT_HOME/.wine-mt5/drive_c/users/$BOT_USER/AppData/Local/Programs/Python/Python311/python.exe direct_mt5_monitor.py
Restart=always
RestartSec=30
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

print_success "Systemd service created (disabled by default)"

# Step 13: Create Management Scripts
print_status "Step 12: Creating management scripts..."

# Bot management script
cat > "$BOT_HOME/manage-bot.sh" << 'EOF'
#!/bin/bash
# Trading Bot Management Script

case "$1" in
    start)
        echo "Starting trading bot..."
        sudo systemctl start mt5-trading-bot
        ;;
    stop)
        echo "Stopping trading bot..."
        sudo systemctl stop mt5-trading-bot
        ;;
    restart)
        echo "Restarting trading bot..."
        sudo systemctl restart mt5-trading-bot
        ;;
    status)
        sudo systemctl status mt5-trading-bot
        ;;
    logs)
        sudo journalctl -u mt5-trading-bot -f
        ;;
    enable)
        echo "Enabling auto-start..."
        sudo systemctl enable mt5-trading-bot
        ;;
    disable)
        echo "Disabling auto-start..."
        sudo systemctl disable mt5-trading-bot
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|logs|enable|disable}"
        exit 1
        ;;
esac
EOF

chown "$BOT_USER:$BOT_USER" "$BOT_HOME/manage-bot.sh"
chmod +x "$BOT_HOME/manage-bot.sh"

# Monitoring script
cat > "$BOT_HOME/monitor.sh" << 'EOF'
#!/bin/bash
# System monitoring for trading bot

echo "=== Trading Bot Status ==="
sudo systemctl is-active mt5-trading-bot

echo ""
echo "=== System Resources ==="
free -h
echo ""
df -h /

echo ""
echo "=== Wine Processes ==="
ps aux | grep -E "(wine|python)" | grep -v grep

echo ""
echo "=== Network Connectivity ==="
ping -c 1 8.8.8.8 >/dev/null 2>&1 && echo "Internet: OK" || echo "Internet: FAILED"
EOF

chown "$BOT_USER:$BOT_USER" "$BOT_HOME/monitor.sh"
chmod +x "$BOT_HOME/monitor.sh"

# Step 14: Create Environment Template
print_status "Step 13: Creating environment template..."

cat > "$PROJECT_DIR/simple-direct/.env.template" << 'EOF'
# MT5 Trading Bot Configuration
# Copy this to .env and fill in your actual values

# Telegram API Configuration
TELEGRAM_API_ID=your_telegram_api_id
TELEGRAM_API_HASH=your_telegram_api_hash
TELEGRAM_PHONE=your_phone_number
TELEGRAM_GROUP_ID=your_group_id
SESSION_NAME=telegram_monitor

# MT5 Connection (Demo Account)
MT5_LOGIN=your_mt5_login
MT5_PASSWORD=your_mt5_password
MT5_SERVER=your_broker_server

# Trading Settings
ENTRY_STRATEGY=adaptive
DEFAULT_VOLUME=0.01
MAGIC_NUMBER=123456

# n8n Webhook URL
N8N_LOG_WEBHOOK=your_n8n_webhook_url
EOF

chown "$BOT_USER:$BOT_USER" "$PROJECT_DIR/simple-direct/.env.template"

# Step 15: Final Instructions
print_success "✅ Setup completed successfully!"
echo ""
echo "=================================================="
echo "🎯 NEXT STEPS:"
echo "=================================================="
echo ""
echo "1. 📁 Upload your trading bot files:"
echo "   scp -r /path/to/your/simple-direct/* root@your-vps-ip:$PROJECT_DIR/simple-direct/"
echo ""
echo "2. 🔧 Complete the installation (run as trader user):"
echo "   sudo -u $BOT_USER $BOT_HOME/install-mt5-python.sh"
echo ""
echo "3. ⚙️ Configure your environment:"
echo "   sudo -u $BOT_USER cp $PROJECT_DIR/simple-direct/.env.template $PROJECT_DIR/simple-direct/.env"
echo "   sudo -u $BOT_USER nano $PROJECT_DIR/simple-direct/.env"
echo ""
echo "4. 🧪 Test the bot:"
echo "   sudo -u $BOT_USER $BOT_HOME/manage-bot.sh start"
echo "   sudo -u $BOT_USER $BOT_HOME/manage-bot.sh logs"
echo ""
echo "5. 🚀 Enable auto-start (after testing):"
echo "   sudo -u $BOT_USER $BOT_HOME/manage-bot.sh enable"
echo ""
echo "=================================================="
echo "📁 Important Paths:"
echo "  • Project: $PROJECT_DIR"
echo "  • User Home: $BOT_HOME" 
echo "  • Management: $BOT_HOME/manage-bot.sh"
echo "  • Monitoring: $BOT_HOME/monitor.sh"
echo ""
echo "🔍 Useful Commands:"
echo "  • Check status: sudo -u $BOT_USER $BOT_HOME/manage-bot.sh status"
echo "  • View logs: sudo -u $BOT_USER $BOT_HOME/manage-bot.sh logs"
echo "  • Monitor system: sudo -u $BOT_USER $BOT_HOME/monitor.sh"
echo "=================================================="

print_success "🎉 Your VPS is ready for MT5 trading bot deployment!"