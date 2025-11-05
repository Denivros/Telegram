# 🪟 Windows VPS Direct MT5 Deployment Guide

Complete guide for deploying your Direct MT5 Telegram Monitor on Windows VPS with full Python MetaTrader5 integration.

## 🎯 **Advantages of Windows VPS**

✅ **Native MT5 Support** - Full MetaTrader5 Python library compatibility  
✅ **Direct Integration** - No API limitations or external dependencies  
✅ **Real-time Execution** - Instant trade execution without network delays  
✅ **Advanced Strategies** - Full access to MT5 functions and data  
✅ **No Rate Limits** - Direct connection to your broker

## 📦 **Files to Deploy**

From your `simple-direct` folder:

- `direct_mt5_monitor.py` (main script)
- `requirements.txt` (dependencies)
- `.env.example` (configuration template)
- `telegram_monitor.session` (if you have it)

## 🔧 **Step 1: Windows VPS Setup**

### **Connect to Windows VPS**

```powershell
# Via RDP (Remote Desktop)
mstsc /v:your-windows-vps-ip
```

### **Install Python 3.11+**

1. Download Python from https://python.org/downloads/windows/
2. **Important**: Check "Add Python to PATH" during installation
3. Verify installation:

```cmd
python --version
pip --version
```

### **Install Git (Optional but recommended)**

Download from: https://git-scm.com/download/win

## 🏦 **Step 2: Install MetaTrader 5**

1. **Download MT5** from your broker or MetaQuotes
2. **Install MT5** on the VPS
3. **Login** with your trading account
4. **Test connection** - ensure you can see live quotes

## 📂 **Step 3: Create Project Directory**

```cmd
# Create project folder
mkdir C:\TradingBot
cd C:\TradingBot

# Create subdirectories
mkdir logs
mkdir sessions
```

## 📤 **Step 4: Upload Files to Windows VPS**

### **Method 1: RDP File Transfer**

1. Connect via RDP
2. Copy files from your local machine
3. Paste into `C:\TradingBot\`

### **Method 2: SCP/SFTP (if SSH enabled)**

```bash
# From your Mac
scp -r /Users/victorivros/Documents/Analyte/Python/Telegram/simple-direct/* administrator@your-vps-ip:C:/TradingBot/
```

### **Method 3: Cloud Storage**

1. Upload to Google Drive/Dropbox
2. Download on VPS
3. Extract to `C:\TradingBot\`

## ⚙️ **Step 5: Install Python Dependencies**

```cmd
cd C:\TradingBot

# Upgrade pip first
python -m pip install --upgrade pip

# Install MetaTrader5 library
pip install MetaTrader5

# Install other requirements
pip install telethon requests python-dotenv

# Or install from requirements.txt
pip install -r requirements.txt
```

## 🔐 **Step 6: Configure Environment Variables**

Create `C:\TradingBot\.env`:

```env
# Telegram API Configuration
TELEGRAM_API_ID=22159421
TELEGRAM_API_HASH=0a383c450ac02bbc327fd975f32387c4
TELEGRAM_PHONE=+32474071892
TELEGRAM_GROUP_ID=4867740501
SESSION_NAME=telegram_monitor

# MT5 Connection (if using remote VPS MT5)
MT5_LOGIN=your_mt5_account_number
MT5_PASSWORD=your_mt5_password
MT5_SERVER=your_broker_server

# Trading Configuration
DEFAULT_VOLUME=0.01
ENTRY_STRATEGY=adaptive
MAGIC_NUMBER=123456

# N8N Webhooks
N8N_LOG_WEBHOOK=https://n8n.srv881084.hstgr.cloud/webhook/trading-logs
N8N_TELEGRAM_FEEDBACK=https://n8n.srv881084.hstgr.cloud/webhook/91126b9d-bd23-4e92-8891-5bfb217455c7
```

## 🔑 **Step 7: Setup Telegram Session**

### **Option 1: Transfer Existing Session**

If you have `telegram_monitor.session`:

```cmd
copy telegram_monitor.session C:\TradingBot\
```

### **Option 2: Create New Session**

```cmd
cd C:\TradingBot
python
```

```python
# In Python interpreter
import asyncio
from telethon import TelegramClient

async def setup():
    client = TelegramClient('telegram_monitor', 22159421, '0a383c450ac02bbc327fd975f32387c4')
    await client.start(phone='+32474071892')
    print("Session created!")
    await client.disconnect()

asyncio.run(setup())
exit()
```

## 🧪 **Step 8: Test MT5 Connection**

Create `test_mt5.py`:

```python
import MetaTrader5 as mt5

# Test MT5 connection
if not mt5.initialize():
    print("MT5 initialize() failed")
    print(mt5.last_error())
else:
    print("MT5 initialized successfully!")

    # Get account info
    account_info = mt5.account_info()
    if account_info:
        print(f"Account: {account_info.login}")
        print(f"Balance: ${account_info.balance}")
        print(f"Server: {account_info.server}")

    # Test symbol
    symbol_info = mt5.symbol_info("EURUSD")
    if symbol_info:
        print(f"EURUSD available: {symbol_info.name}")

    mt5.shutdown()
```

Run test:

```cmd
python test_mt5.py
```

## 🚀 **Step 9: Run the Monitor**

```cmd
cd C:\TradingBot
python direct_mt5_monitor.py
```

## 🔧 **Step 10: Create Windows Service (Optional)**

Create `install_service.bat`:

```batch
@echo off
echo Installing Trading Bot as Windows Service...

# Using NSSM (Non-Sucking Service Manager)
# Download from: https://nssm.cc/download

nssm install "TradingBot" "C:\Python311\python.exe"
nssm set "TradingBot" AppDirectory "C:\TradingBot"
nssm set "TradingBot" AppParameters "direct_mt5_monitor.py"
nssm set "TradingBot" DisplayName "Telegram Trading Bot"
nssm set "TradingBot" Description "Direct MT5 Telegram Signal Monitor"
nssm set "TradingBot" Start SERVICE_AUTO_START

echo Service installed! Start with: net start TradingBot
pause
```

## 📊 **Step 11: Monitoring & Maintenance**

### **Check Logs**

```cmd
# View log file
type logs\direct_mt5_monitor.log

# Real-time log monitoring
powershell Get-Content logs\direct_mt5_monitor.log -Wait -Tail 50
```

### **Service Management**

```cmd
# Start service
net start TradingBot

# Stop service
net stop TradingBot

# Service status
sc query TradingBot
```

### **Restart Script**

Create `restart_bot.bat`:

```batch
@echo off
echo Restarting Trading Bot...
taskkill /f /im python.exe
timeout /t 5
cd C:\TradingBot
python direct_mt5_monitor.py
```

## 🛡️ **Security & Best Practices**

### **Firewall Configuration**

- Only allow necessary ports (3389 for RDP)
- Use VPN for secure access
- Disable unused Windows services

### **Auto-Start Setup**

Add to Windows startup:

```cmd
# Add to startup folder
copy restart_bot.bat "C:\ProgramData\Microsoft\Windows\Start Menu\Programs\Startup\"
```

### **Backup Configuration**

```cmd
# Create backup script
xcopy C:\TradingBot C:\TradingBot_Backup\ /E /Y
```

## 🎯 **Expected Results**

Once deployed, your system will:

✅ **Monitor Telegram** for trading signals  
✅ **Parse signals** with your custom patterns  
✅ **Execute trades** directly via MT5 Python library  
✅ **Send logs** to N8N for notifications  
✅ **Run 24/7** as Windows service  
✅ **Auto-restart** on failures

## 📋 **Troubleshooting**

### **MT5 Connection Issues**

```python
# Check MT5 status
import MetaTrader5 as mt5
print(mt5.version())
print(mt5.terminal_info())
print(mt5.account_info())
```

### **Telegram Connection Issues**

- Verify session file exists
- Check API credentials
- Test with simple Telethon script

### **Trading Issues**

- Verify account permissions
- Check minimum volume requirements
- Ensure sufficient margin
- Validate symbol names

## 🚀 **Deployment Commands Summary**

```cmd
# Quick deployment script
mkdir C:\TradingBot
cd C:\TradingBot

# Upload your files here

pip install MetaTrader5 telethon requests python-dotenv

# Configure .env file

# Test MT5 connection
python test_mt5.py

# Run the bot
python direct_mt5_monitor.py
```

Your Windows VPS is now ready for direct MT5 trading! 🎯
