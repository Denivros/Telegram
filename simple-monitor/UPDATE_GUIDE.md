# 📋 Telegram Monitor Update Guide

Complete guide for updating your Telegram monitor running on Hostinger VPS when you make changes to the script or environment configuration.

## 🔄 Quick Update Process Overview

When you modify either the `telegram_monitor.py` script or the `.env` file, you need to:

1. **Package** the updated files
2. **Upload** to your VPS
3. **Rebuild** the Docker container
4. **Restart** the monitor

---

## 📝 **Method 1: Automatic Update Script (Recommended)**

### Step 1: Use the Auto-Update Script

I've created an automated script that handles everything for you:

```bash
cd /Users/victorivros/Documents/Analyte/Python/Telegram/simple-monitor
./update-monitor.sh
```

If the script doesn't exist, create it:

```bash
#!/bin/bash
# Auto-update script for Telegram Monitor

echo "🔄 Updating Telegram Monitor on VPS..."

# Create package with all files
tar -czf telegram-monitor-update.tar.gz \
    telegram_monitor.py \
    setup_session.py \
    requirements.txt \
    .env \
    Dockerfile \
    telegram_monitor.session

# Upload to VPS
echo "📤 Uploading to VPS..."
scp telegram-monitor-update.tar.gz root@31.97.183.241:~/

# Create update script for VPS
cat > vps-update.sh << 'EOF'
#!/bin/bash
echo "🔧 Applying updates on VPS..."

# Extract files
tar -xzf telegram-monitor-update.tar.gz
rm -rf telegram-monitor-old
mv telegram-monitor telegram-monitor-old 2>/dev/null || true
mkdir -p telegram-monitor
mv telegram_monitor.py setup_session.py requirements.txt .env Dockerfile telegram_monitor.session telegram-monitor/
cd telegram-monitor

# Stop and remove old container
echo "🛑 Stopping old container..."
docker stop telegram-monitor 2>/dev/null || true
docker rm telegram-monitor 2>/dev/null || true

# Rebuild image
echo "🔨 Rebuilding Docker image..."
docker build -t telegram-monitor .

# Start new container
echo "🚀 Starting updated monitor..."
docker run -d \
    --name telegram-monitor \
    --restart unless-stopped \
    -v $(pwd)/logs:/app/logs \
    telegram-monitor

echo "✅ Update complete!"
docker ps --filter "name=telegram-monitor"
docker logs telegram-monitor --tail 10

# Cleanup
cd ..
rm -f telegram-monitor-update.tar.gz vps-update.sh
EOF

# Upload and run update script
scp vps-update.sh root@31.97.183.241:~/
ssh root@31.97.183.241 'chmod +x vps-update.sh && ./vps-update.sh'

# Local cleanup
rm telegram-monitor-update.tar.gz vps-update.sh

echo "🎉 Monitor updated successfully!"
```

Make it executable:

```bash
chmod +x update-monitor.sh
```

---

## 🛠️ **Method 2: Manual Step-by-Step Process**

### Step 1: Package Your Files

```bash
cd /Users/victorivros/Documents/Analyte/Python/Telegram/simple-monitor

# Create archive with all necessary files
tar -czf telegram-monitor-update.tar.gz \
    telegram_monitor.py \
    setup_session.py \
    requirements.txt \
    .env \
    Dockerfile \
    telegram_monitor.session
```

### Step 2: Upload to VPS

```bash
# Upload the package
scp telegram-monitor-update.tar.gz root@31.97.183.241:~/
```

### Step 3: SSH into VPS and Update

```bash
# Connect to your VPS
ssh root@31.97.183.241

# Extract files
tar -xzf telegram-monitor-update.tar.gz

# Backup old version
rm -rf telegram-monitor-old
mv telegram-monitor telegram-monitor-old

# Setup new version
mkdir -p telegram-monitor
mv telegram_monitor.py setup_session.py requirements.txt .env Dockerfile telegram_monitor.session telegram-monitor/
cd telegram-monitor
```

### Step 4: Rebuild and Restart Docker Container

```bash
# Stop current container
docker stop telegram-monitor
docker rm telegram-monitor

# Rebuild image with updates
docker build -t telegram-monitor .

# Start new container
docker run -d \
    --name telegram-monitor \
    --restart unless-stopped \
    -v $(pwd)/logs:/app/logs \
    telegram-monitor
```

### Step 5: Verify Update

```bash
# Check if container is running
docker ps --filter "name=telegram-monitor"

# Check logs
docker logs telegram-monitor --tail 20

# Exit VPS
exit
```

---

## 📋 **Common Update Scenarios**

### Scenario 1: Changed .env File Only

If you only changed environment variables:

```bash
# Quick .env update
cd /Users/victorivros/Documents/Analyte/Python/Telegram/simple-monitor
scp .env root@31.97.183.241:~/telegram-monitor/
ssh root@31.97.183.241 'cd telegram-monitor && docker stop telegram-monitor && docker rm telegram-monitor && docker build -t telegram-monitor . && docker run -d --name telegram-monitor --restart unless-stopped -v $(pwd)/logs:/app/logs telegram-monitor'
```

### Scenario 2: Changed Python Script Only

If you only modified `telegram_monitor.py`:

```bash
# Quick script update
cd /Users/victorivros/Documents/Analyte/Python/Telegram/simple-monitor
scp telegram_monitor.py root@31.97.183.241:~/telegram-monitor/
ssh root@31.97.183.241 'cd telegram-monitor && docker stop telegram-monitor && docker rm telegram-monitor && docker build -t telegram-monitor . && docker run -d --name telegram-monitor --restart unless-stopped -v $(pwd)/logs:/app/logs telegram-monitor'
```

### Scenario 3: Added New Dependencies

If you modified `requirements.txt`:

```bash
# Full rebuild required
./update-monitor.sh  # Use the auto-update script
```

---

## 🔍 **Verification Commands**

After any update, use these commands to verify everything is working:

```bash
# Check container status
ssh root@31.97.183.241 'docker ps --filter "name=telegram-monitor"'

# View live logs
ssh root@31.97.183.241 'docker logs telegram-monitor -f'

# Check recent logs only
ssh root@31.97.183.241 'docker logs telegram-monitor --tail 20'

# Test container restart
ssh root@31.97.183.241 'docker restart telegram-monitor'
```

---

## 🚨 **Troubleshooting**

### Container Won't Start

```bash
# Check logs for errors
ssh root@31.97.183.241 'docker logs telegram-monitor'

# Check if session file exists
ssh root@31.97.183.241 'ls -la telegram-monitor/telegram_monitor.session'

# Rebuild image from scratch
ssh root@31.97.183.241 'cd telegram-monitor && docker build --no-cache -t telegram-monitor .'
```

### Session File Issues

If the Telegram session becomes invalid:

```bash
# Recreate session locally
cd /Users/victorivros/Documents/Analyte/Python/Telegram/simple-monitor
python3 setup_session.py

# Upload new session
scp telegram_monitor.session root@31.97.183.241:~/telegram-monitor/

# Restart container
ssh root@31.97.183.241 'cd telegram-monitor && docker restart telegram-monitor'
```

### Permission Issues

```bash
# Fix file permissions on VPS
ssh root@31.97.183.241 'chmod 644 telegram-monitor/*'
```

---

## 📁 **File Structure on VPS**

Your VPS should have this structure:

```
/root/
├── telegram-monitor/           # Current version
│   ├── telegram_monitor.py
│   ├── setup_session.py
│   ├── requirements.txt
│   ├── .env
│   ├── Dockerfile
│   ├── telegram_monitor.session
│   └── logs/                   # Docker volume for logs
├── telegram-monitor-old/       # Backup of previous version
└── telegram-monitor-update.tar.gz  # Upload package (temporary)
```

---

## ⚡ **Quick Reference**

| Task             | Command                                                    |
| ---------------- | ---------------------------------------------------------- |
| **Full Update**  | `./update-monitor.sh`                                      |
| **Check Status** | `ssh root@31.97.183.241 'docker ps \| grep telegram'`      |
| **View Logs**    | `ssh root@31.97.183.241 'docker logs telegram-monitor -f'` |
| **Restart**      | `ssh root@31.97.183.241 'docker restart telegram-monitor'` |
| **Stop**         | `ssh root@31.97.183.241 'docker stop telegram-monitor'`    |
| **Check Files**  | `ssh root@31.97.183.241 'ls -la telegram-monitor/'`        |

---

## 🔐 **Security Notes**

- Always backup your session file: `telegram_monitor.session`
- Keep your `.env` file secure (contains API credentials)
- Test changes locally when possible before deploying
- Monitor logs after updates to ensure everything works correctly

---

## 🎯 **Best Practices**

1. **Always test locally first** if you have the Python environment set up
2. **Keep backups** of working configurations
3. **Check logs** immediately after updates
4. **Use the auto-update script** for consistency
5. **Document your changes** if you modify the core functionality

That's it! With this guide, you can easily update your Telegram monitor whenever you make changes. The auto-update script makes it a one-command operation! 🚀
