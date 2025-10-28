# Hostinger VPS Deployment Guide

**Step-by-step deployment for your MT5 Trading Bot on Hostinger Ubuntu 24.04**

## 🖥️ **Your VPS Details:**

- **OS**: Ubuntu 24.04 LTS (Latest stable)
- **Type**: KVM 2 (Good performance for trading)
- **Access**: Root SSH access
- **IP**: 31.97.183.241
- **SSH**: `ssh root@31.97.183.241`

---

## 🚀 **Quick Deployment (Recommended - Docker)**

### **Step 1: Test VPS Connection**

```bash
# From your Mac - test connection
ssh root@31.97.183.241

# You should see Ubuntu 24.04 welcome message
# Type 'exit' to disconnect for now
```

### **Step 2: Upload Your Project**

```bash
# From your Mac (in simple-direct directory)
./upload-to-vps.sh

# This will automatically upload to root@31.97.183.241
```

### **Step 3: Install Docker on VPS**

```bash
# SSH into your VPS
ssh root@31.97.183.241

# Install Docker (Ubuntu 24.04 optimized)
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Install Docker Compose V2
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Start and enable Docker
systemctl start docker
systemctl enable docker

# Verify installation
docker --version
docker-compose --version
```

### **Step 4: Configure and Start Bot**

```bash
# Navigate to project directory
cd /root/trading-bot/simple-direct

# Configure your credentials
nano .env
# Add your actual MT5 and Telegram credentials

# Build and start the bot
./docker-manage.sh build
./docker-manage.sh start
```

### **Step 5: Monitor Your Bot**

```bash
# Watch real-time logs
./docker-manage.sh logs -f

# Check status
./docker-manage.sh status

# If everything looks good, enable auto-start
docker update --restart unless-stopped mt5-trading-bot
```

---

## 🛠️ **Alternative: Direct Installation**

If you prefer direct installation without Docker:

### **Step 1: Upload Setup Script**

```bash
# From your Mac
scp setup-vps.sh root@31.97.183.241:~/

# SSH and run
ssh root@31.97.183.241
chmod +x setup-vps.sh
./setup-vps.sh
```

### **Step 2: Complete Installation**

```bash
# Upload your project files
./upload-to-vps.sh

# Complete the setup
sudo -u trader /home/trader/install-mt5-python.sh
```

---

## ⚡ **Ubuntu 24.04 Optimizations**

### **Performance Tweaks:**

```bash
# SSH into VPS
ssh root@31.97.183.241

# Update system
apt update && apt upgrade -y

# Install performance monitoring
apt install -y htop iotop nethogs

# Optimize for trading (low latency)
echo 'net.core.rmem_max = 268435456' >> /etc/sysctl.conf
echo 'net.core.wmem_max = 268435456' >> /etc/sysctl.conf
sysctl -p

# Set timezone (adjust for your broker's timezone)
timedatectl set-timezone UTC
```

### **Security Setup:**

```bash
# Basic firewall (Docker will handle MT5 ports)
ufw enable
ufw allow ssh
ufw allow 5900/tcp  # VNC for debugging (optional)

# Disable unnecessary services
systemctl disable snapd
systemctl stop snapd
```

---

## 📊 **Monitoring Commands**

### **System Monitoring:**

```bash
# Check system resources
htop

# Monitor Docker containers
docker stats

# Check disk space
df -h

# Monitor network
nethogs
```

### **Bot Monitoring:**

```bash
# Real-time logs
./docker-manage.sh logs -f

# Container health
./docker-manage.sh status

# Enter container for debugging
./docker-manage.sh shell
```

---

## 🔧 **KVM 2 Specific Notes**

### **Advantages of Your VPS:**

✅ **Full virtualization** - Better performance than OpenVZ
✅ **Dedicated resources** - No resource sharing
✅ **Ubuntu 24.04** - Latest LTS with best compatibility
✅ **Root access** - Full control over system

### **Resource Management:**

```bash
# Check your VPS specs
lscpu
free -h
df -h

# Optimize for trading
echo 'vm.swappiness=10' >> /etc/sysctl.conf
echo 'vm.vfs_cache_pressure=50' >> /etc/sysctl.conf
```

---

## 🎯 **Quick Start Commands**

### **Complete Deployment (Copy & Paste):**

```bash
# 1. From your Mac - upload files
./upload-to-vps.sh

# 2. SSH into VPS and install Docker
ssh root@31.97.183.241
curl -fsSL https://get.docker.com | sh
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# 3. Navigate and configure
cd /root/trading-bot/simple-direct
cp .env.example .env
nano .env  # Add your credentials

# 4. Build and start
./docker-manage.sh build
./docker-manage.sh start

# 5. Monitor
./docker-manage.sh logs -f
```

### **Daily Management:**

```bash
# Check bot status
ssh root@31.97.183.241
cd /root/trading-bot/simple-direct
./docker-manage.sh status

# View recent logs
./docker-manage.sh logs --tail 50

# Restart if needed
./docker-manage.sh restart
```

---

## 🔍 **Troubleshooting for Ubuntu 24.04**

### **Common Issues:**

**Docker installation fails:**

```bash
# Remove old Docker versions first
apt remove docker docker-engine docker.io containerd runc
apt autoremove
# Then reinstall
curl -fsSL https://get.docker.com | sh
```

**Container build fails:**

```bash
# Check Docker daemon
systemctl status docker
systemctl start docker

# Clear Docker cache
docker system prune -a
./docker-manage.sh build
```

**Network connectivity issues:**

```bash
# Test connectivity
ping google.com
nslookup puprime.com

# Check firewall
ufw status
ufw allow out 443/tcp  # HTTPS
ufw allow out 80/tcp   # HTTP
```

---

## 📋 **Next Steps Checklist**

- [ ] **Test SSH connection**: `ssh root@31.97.183.241`
- [ ] **Upload files**: `./upload-to-vps.sh`
- [ ] **Install Docker**: Follow commands above
- [ ] **Configure .env**: Add your MT5 and Telegram credentials
- [ ] **Build container**: `./docker-manage.sh build`
- [ ] **Start bot**: `./docker-manage.sh start`
- [ ] **Monitor logs**: `./docker-manage.sh logs -f`
- [ ] **Test demo trading**: Verify with small demo trades
- [ ] **Enable auto-start**: For production use

---

## 💡 **Pro Tips for Your Setup**

1. **Use screen/tmux** for persistent sessions:

   ```bash
   apt install screen
   screen -S trading
   # Your commands here
   # Ctrl+A, D to detach
   ```

2. **Set up log monitoring**:

   ```bash
   # Create alias for quick log viewing
   echo 'alias bot-logs="cd /root/trading-bot/simple-direct && ./docker-manage.sh logs -f"' >> ~/.bashrc
   ```

3. **Regular backups**:
   ```bash
   # Daily backup
   cd /root/trading-bot/simple-direct
   ./docker-manage.sh backup
   ```

**Your Hostinger VPS is perfect for this setup!** Ubuntu 24.04 + KVM 2 will give you excellent performance for MT5 trading. 🚀
