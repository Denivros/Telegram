# Ubuntu VPS Setup Guide for MT5 Trading Bot

**Complete guide for deploying your Telegram MT5 trading bot on Hostinger Ubuntu VPS**

## 🚀 Quick Overview

- **Platform**: Ubuntu 20.04/22.04 LTS (Hostinger VPS)
- **Method**: Wine + MetaTrader5 + Python
- **Cost**: Much cheaper than Windows VPS
- **Performance**: Better for 24/7 trading operations

---

## 📋 Prerequisites

1. **Hostinger VPS** with Ubuntu 20.04+
2. **SSH access** to your VPS
3. **Root/sudo privileges**
4. **Your project files** (we'll upload them)

---

## 🛠️ Method 1: Direct Ubuntu Setup (Recommended)

### Step 1: Connect to Your VPS

```bash
# SSH into your Hostinger VPS
ssh root@your-vps-ip
# or if you have a user account:
ssh username@your-vps-ip
```

### Step 2: System Update & Dependencies

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install essential packages
sudo apt install -y curl wget git unzip software-properties-common

# Install Python 3.10+ and pip
sudo apt install -y python3 python3-pip python3-venv

# Install Wine dependencies
sudo dpkg --add-architecture i386
sudo apt update
sudo apt install -y wine wine32 wine64 winetricks

# Install X11 and display dependencies (needed for MT5)
sudo apt install -y xvfb x11vnc fluxbox
```

### Step 3: Configure Wine Environment

```bash
# Set up Wine prefix for MT5
export WINEARCH=win64
export WINEPREFIX=$HOME/.wine-mt5

# Initialize Wine
winecfg  # Set Windows version to "Windows 10"

# Install Windows components needed by MT5
winetricks -q corefonts vcrun2019 vcrun2015 msvcrt
```

### Step 4: Install MetaTrader5

```bash
# Create working directory
mkdir -p ~/trading-bot
cd ~/trading-bot

# Download MT5 installer
wget https://download.mql5.com/cdn/web/metaquotes.software.corp/mt5/mt5setup.exe

# Install MT5 via Wine
DISPLAY=:0 wine mt5setup.exe

# Verify MT5 installation
ls ~/.wine-mt5/drive_c/Program\ Files/MetaTrader\ 5/
```

### Step 5: Install Python in Wine

```bash
# Download Python Windows installer
wget https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe

# Install Python in Wine environment
DISPLAY=:0 wine python-3.11.9-amd64.exe

# Add Wine Python to PATH
echo 'export PATH="$HOME/.wine-mt5/drive_c/users/$USER/AppData/Local/Programs/Python/Python311:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

### Step 6: Install Python Packages in Wine

```bash
# Install trading bot dependencies
wine python -m pip install --upgrade pip
wine python -m pip install MetaTrader5 telethon requests python-dotenv
```

### Step 7: Upload Your Project Files

```bash
# Create project directory
mkdir -p ~/trading-bot/simple-direct
cd ~/trading-bot/simple-direct

# Upload your files (choose one method):

# Method A: Using SCP from your Mac
# scp -r /Users/victorivros/Documents/Analyte/Python/Telegram/simple-direct/* root@your-vps-ip:~/trading-bot/simple-direct/

# Method B: Using Git (if you have a repo)
# git clone https://github.com/yourusername/your-repo.git

# Method C: Manual upload via nano/vim
nano .env
# Copy paste your .env content

nano direct_mt5_monitor.py
# Copy paste your Python script
```

### Step 8: Configure Environment

```bash
# Create .env file with your credentials
cat > .env << 'EOF'
# Telegram API credentials
TELEGRAM_API_ID=22159421
TELEGRAM_API_HASH=0a383c450ac02bbc327fd975f32387c4
TELEGRAM_PHONE=+32474071892
TELEGRAM_GROUP_ID=4867740501
SESSION_NAME=telegram_monitor

# MT5 VPS Connection
MT5_LOGIN=700010991
MT5_PASSWORD=!yo9q9E&
MT5_SERVER=PUPrime-Demo

# Trading Configuration
ENTRY_STRATEGY=adaptive
DEFAULT_VOLUME=0.01
MAGIC_NUMBER=123456

# n8n webhook URL
N8N_LOG_WEBHOOK=https://n8n.srv881084.hstgr.cloud/webhook-test/trading-logs
EOF
```

### Step 9: Create Virtual Display for MT5

```bash
# Create startup script for virtual display
cat > ~/start-display.sh << 'EOF'
#!/bin/bash
# Start virtual display for MT5 GUI
export DISPLAY=:0
Xvfb :0 -screen 0 1024x768x24 &
fluxbox &
sleep 2
EOF

chmod +x ~/start-display.sh
```

### Step 10: Test the Setup

```bash
# Start virtual display
~/start-display.sh

# Test MT5 connection
cd ~/trading-bot/simple-direct
DISPLAY=:0 wine python direct_mt5_monitor.py --test-connection
```

---

## 🐳 Method 2: Docker Setup (Alternative)

### Create Dockerfile

```bash
# Create Dockerfile
cat > Dockerfile << 'EOF'
FROM ubuntu:22.04

# Prevent interactive prompts
ENV DEBIAN_FRONTEND=noninteractive

# Install dependencies
RUN apt-get update && apt-get install -y \
    wine \
    wine32 \
    wine64 \
    winetricks \
    python3 \
    python3-pip \
    wget \
    xvfb \
    x11vnc \
    fluxbox \
    && rm -rf /var/lib/apt/lists/*

# Set Wine architecture
ENV WINEARCH=win64
ENV WINEPREFIX=/root/.wine
ENV DISPLAY=:99

# Create working directory
WORKDIR /app

# Copy project files
COPY . .

# Install Python packages
RUN pip3 install -r requirements.txt

# Setup script
COPY setup.sh /setup.sh
RUN chmod +x /setup.sh

# Start script
COPY start.sh /start.sh
RUN chmod +x /start.sh

EXPOSE 8000

CMD ["/start.sh"]
EOF
```

### Create Docker Compose

```bash
cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  trading-bot:
    build: .
    container_name: mt5-trading-bot
    restart: unless-stopped
    volumes:
      - ./logs:/app/logs
      - ./data:/app/data
    environment:
      - DISPLAY=:99
    ports:
      - "5900:5900"  # VNC access
    networks:
      - trading-network

networks:
  trading-network:
    driver: bridge
EOF
```

---

## 🔧 VPS Performance Optimization

### Resource Monitoring

```bash
# Install monitoring tools
sudo apt install -y htop iotop nethogs

# Create monitoring script
cat > ~/monitor.sh << 'EOF'
#!/bin/bash
echo "=== System Resources ==="
free -h
echo ""
echo "=== Disk Usage ==="
df -h
echo ""
echo "=== Trading Bot Process ==="
ps aux | grep -E "(python|wine|mt5)" | grep -v grep
EOF

chmod +x ~/monitor.sh
```

### Auto-Start Setup

```bash
# Create systemd service
sudo tee /etc/systemd/system/trading-bot.service << 'EOF'
[Unit]
Description=MT5 Trading Bot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/trading-bot/simple-direct
Environment=DISPLAY=:0
ExecStartPre=/root/start-display.sh
ExecStart=/usr/bin/wine /root/.wine-mt5/drive_c/users/root/AppData/Local/Programs/Python/Python311/python.exe direct_mt5_monitor.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable auto-start
sudo systemctl daemon-reload
sudo systemctl enable trading-bot
sudo systemctl start trading-bot
```

---

## 📊 Monitoring & Management

### Log Management

```bash
# View real-time logs
sudo journalctl -u trading-bot -f

# Check Wine processes
ps aux | grep wine

# Monitor resource usage
htop
```

### Remote Access Setup

```bash
# Install VNC for remote GUI access (optional)
sudo apt install -y tightvncserver

# Start VNC server
vncserver :1 -geometry 1024x768 -depth 24
```

---

## 🚨 Troubleshooting Guide

### Common Issues & Solutions

**1. Wine MT5 Installation Fails**

```bash
# Clean Wine prefix and retry
rm -rf ~/.wine-mt5
export WINEPREFIX=$HOME/.wine-mt5
winecfg
```

**2. Display Issues**

```bash
# Restart virtual display
pkill Xvfb
pkill fluxbox
~/start-display.sh
```

**3. Python Package Issues**

```bash
# Reinstall packages
wine python -m pip uninstall MetaTrader5
wine python -m pip install MetaTrader5 --no-cache-dir
```

**4. Connection Problems**

```bash
# Test network connectivity
ping google.com
nslookup puprime.com

# Check firewall
sudo ufw status
sudo ufw allow 443/tcp
```

---

## 💡 Pro Tips

1. **Use Screen/Tmux** for persistent sessions:

   ```bash
   sudo apt install screen
   screen -S trading-bot
   # Run your bot inside screen session
   ```

2. **Set up Log Rotation**:

   ```bash
   sudo nano /etc/logrotate.d/trading-bot
   ```

3. **Monitor VPS Resources**:

   - RAM: Keep under 80% usage
   - CPU: Should be minimal when idle
   - Disk: Monitor log file sizes

4. **Backup Configuration**:
   ```bash
   tar -czf trading-bot-backup.tar.gz ~/trading-bot/
   ```

---

## 🎯 Next Steps After Setup

1. **Test Connection**: Verify MT5 connects to PUPrime demo
2. **Test Telegram**: Ensure bot reads your Telegram group
3. **Test Trading**: Place a small demo trade
4. **Monitor Performance**: Watch for 24-48 hours
5. **Go Live**: Switch to live account when confident

Would you like me to help you with any specific part of this setup?
