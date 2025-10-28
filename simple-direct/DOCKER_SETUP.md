# Docker Setup Guide for MT5 Trading Bot

**Complete Docker deployment guide for your Telegram MT5 trading bot on Hostinger VPS**

## 🐳 Why Docker for MT5 Trading Bot?

### **Advantages:**

✅ **Consistent Environment** - Works exactly the same everywhere  
✅ **Easy Deployment** - Single command to start everything  
✅ **Isolation** - Bot runs in its own container  
✅ **Easy Updates** - Just rebuild and restart  
✅ **Backup & Recovery** - Simple container management  
✅ **Scaling** - Can run multiple bots easily

### **Perfect for:**

- Production deployment on Hostinger VPS
- Testing different configurations
- Easy rollbacks if something breaks
- Running multiple trading strategies

---

## � Quick Start with Docker

### **Step 1: Install Docker on Your VPS**

```bash
# SSH into your Hostinger VPS
ssh root@your-vps-ip

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.21.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Start Docker service
sudo systemctl start docker
sudo systemctl enable docker

# Verify installation
docker --version
docker-compose --version
```

### **Step 2: Upload Your Project**

```bash
# From your Mac (in simple-direct directory):
# First, edit upload script with your VPS IP
nano upload-to-vps.sh  # Set VPS_IP="your-actual-ip"

# Upload all files including Docker setup
./upload-to-vps.sh
```

### **Step 3: Build and Start (Super Simple!)**

```bash
# SSH into VPS and navigate to project
ssh root@your-vps-ip
cd /home/trader/trading-bot/simple-direct

# Configure your credentials
nano .env  # Add your MT5 and Telegram credentials

# Build and start with one command!
./docker-manage.sh build
./docker-manage.sh start
```

---

## 📊 Docker Management Commands

Your `docker-manage.sh` script provides easy management:

```bash
# Build the container
./docker-manage.sh build

# Start the bot
./docker-manage.sh start

# View real-time logs
./docker-manage.sh logs -f

# Check status and health
./docker-manage.sh status

# Stop the bot
./docker-manage.sh stop

# Restart after changes
./docker-manage.sh restart

# Open shell inside container
./docker-manage.sh shell

# Update bot (rebuild + restart)
./docker-manage.sh update

# Clean up everything
./docker-manage.sh cleanup

# Create backup
./docker-manage.sh backup

# Restore from backup
./docker-manage.sh restore
```

---

## 💡 Docker vs Direct Installation

### **Docker Advantages:**

✅ **One command setup** - `./docker-manage.sh build && ./docker-manage.sh start`  
✅ **No dependency conflicts** - everything isolated in container  
✅ **Easy updates** - rebuild container with new code  
✅ **Consistent environment** - works same everywhere  
✅ **Resource control** - limit CPU/RAM usage  
✅ **Multiple bots** - run different strategies in parallel

### **When to Use Docker:**

- **Production deployment** on VPS
- **Multiple trading bots** or strategies
- **Team deployment** - same setup for everyone
- **Easy maintenance** - update/restart with one command

### **When Direct Installation Might Be Better:**

- **Development/testing** on local machine
- **Simple single bot** setup
- **Learning Wine+MT5** setup process
