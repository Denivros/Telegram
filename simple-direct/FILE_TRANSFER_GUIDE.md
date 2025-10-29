# 📁 File Transfer to Windows VPS Guide

Multiple methods to get your trading bot files from Mac to Windows VPS.

## 📋 **Files You Need to Transfer**

From your local `simple-direct` folder:

- ✅ `direct_mt5_monitor.py` (main bot script)
- ✅ `requirements.txt` (Python dependencies)
- ✅ `setup_windows_vps.bat` (automated setup script)
- ✅ `WINDOWS_VPS_DEPLOYMENT.md` (this guide)
- ✅ `telegram_monitor.session` (if you have it from Ubuntu VPS)
- ✅ `.env.example` → rename to `.env` and configure

## 🖥️ **Method 1: RDP Copy-Paste (Easiest)**

### **Step 1: Connect via RDP**

```bash
# On Mac, use Microsoft Remote Desktop from App Store
# Or use built-in Screen Sharing if configured
```

### **Step 2: Enable Clipboard Sharing**

1. Open **Microsoft Remote Desktop**
2. Edit your VPS connection
3. Check **"Redirect local clipboard"**
4. Connect to VPS

### **Step 3: Transfer Files**

1. On Mac: Select all files in `simple-direct` folder
2. Copy files (`Cmd+C`)
3. On Windows VPS: Navigate to `C:\TradingBot`
4. Paste files (`Ctrl+V`)

## ☁️ **Method 2: Cloud Storage (Most Reliable)**

### **Upload from Mac:**

```bash
# Option A: Google Drive
# 1. Upload simple-direct folder to Google Drive
# 2. Share folder publicly or with your Google account

# Option B: Dropbox
# 1. Upload to Dropbox
# 2. Get sharing link

# Option C: GitHub (if you use Git)
cd /Users/victorivros/Documents/Analyte/Python/Telegram/simple-direct
git init
git add .
git commit -m "Windows VPS deployment files"
git remote add origin https://github.com/yourusername/trading-bot.git
git push -u origin main
```

### **Download on Windows VPS:**

```cmd
REM Method A: Direct browser download
REM 1. Open browser on VPS
REM 2. Download from Google Drive/Dropbox
REM 3. Extract to C:\TradingBot\

REM Method B: Git clone (if using GitHub)
cd C:\
git clone https://github.com/yourusername/trading-bot.git TradingBot
```

## 📡 **Method 3: SCP/SFTP (If SSH Enabled)**

### **Enable SSH on Windows VPS:**

```powershell
# Run as Administrator
Add-WindowsCapability -Online -Name OpenSSH.Server~~~~0.0.1.0
Start-Service sshd
Set-Service -Name sshd -StartupType 'Automatic'
```

### **Transfer from Mac:**

```bash
# SCP transfer
scp -r /Users/victorivros/Documents/Analyte/Python/Telegram/simple-direct/* administrator@your-vps-ip:C:/TradingBot/

# SFTP transfer
sftp administrator@your-vps-ip
cd C:/TradingBot
put -r /Users/victorivros/Documents/Analyte/Python/Telegram/simple-direct/*
```

## 💾 **Method 4: FTP Transfer**

### **Setup FTP Server on Windows VPS:**

1. Enable IIS + FTP in Windows Features
2. Configure FTP site in IIS Manager
3. Create FTP user account

### **Upload from Mac:**

```bash
# Using command line FTP
ftp your-vps-ip
# Enter credentials
# Navigate and upload files

# Or use FileZilla
# Download FileZilla for Mac
# Connect with FTP credentials
# Drag and drop files
```

## 📧 **Method 5: Email Transfer (Small Files)**

For configuration files only:

```bash
# Zip the essential files
cd /Users/victorivros/Documents/Analyte/Python/Telegram/simple-direct
zip -r trading-bot-config.zip .env direct_mt5_monitor.py setup_windows_vps.bat

# Email to yourself
# Download on Windows VPS
```

## 🚀 **Quick Start After Transfer**

Once files are on Windows VPS:

```cmd
# Navigate to project directory
cd C:\TradingBot

# Run automated setup
setup_windows_vps.bat

# Edit configuration (use Notepad)
notepad .env

# Test MT5 connection
python test_mt5.py

# Start the bot
python direct_mt5_monitor.py
```

## 🔧 **Essential Post-Transfer Steps**

### **1. Configure .env File**

```cmd
# Edit with your actual credentials
notepad C:\TradingBot\.env
```

Update these values:

```env
MT5_LOGIN=your_actual_mt5_account
MT5_PASSWORD=your_actual_password
MT5_SERVER=your_broker_server_name
```

### **2. Test Telegram Session**

```cmd
# If you have existing session
copy telegram_monitor.session C:\TradingBot\

# If creating new session, run the bot once
python direct_mt5_monitor.py
# Follow phone verification prompts
```

### **3. Verify MT5 Installation**

- Install MetaTrader 5 from your broker
- Login with your trading account
- Ensure live quotes are showing
- Test manual trades work

## 🎯 **Recommended Transfer Method**

**For beginners:** Use **Method 1 (RDP Copy-Paste)**

- Simplest and most reliable
- No additional configuration needed
- Works with any file size

**For developers:** Use **Method 2 (Cloud Storage)**

- Can version control your code
- Easy to update later
- Backup your files automatically

**For advanced users:** Use **Method 3 (SCP)**

- Fastest for large files
- Command-line automation
- Secure encrypted transfer

## ⚡ **One-Click Transfer Script**

Save this on your Mac as `transfer_to_vps.sh`:

```bash
#!/bin/bash

echo "🚀 Transferring Trading Bot to Windows VPS..."

VPS_IP="your-windows-vps-ip"
VPS_USER="administrator"
SOURCE_DIR="/Users/victorivros/Documents/Analyte/Python/Telegram/simple-direct"

echo "📁 Creating remote directory..."
ssh ${VPS_USER}@${VPS_IP} "mkdir -p C:/TradingBot"

echo "📤 Transferring files..."
scp -r ${SOURCE_DIR}/* ${VPS_USER}@${VPS_IP}:C:/TradingBot/

echo "🔧 Running setup script..."
ssh ${VPS_USER}@${VPS_IP} "cd C:/TradingBot && setup_windows_vps.bat"

echo "✅ Transfer complete! Connect to VPS to continue setup."
```

Make it executable:

```bash
chmod +x transfer_to_vps.sh
./transfer_to_vps.sh
```

Your files are now ready for Windows VPS deployment! 🎯
