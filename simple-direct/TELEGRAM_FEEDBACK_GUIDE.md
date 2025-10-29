# 📱 Telegram Feedback Integration Guide

Complete setup guide for Telegram notifications via N8N webhook for your Windows VPS trading bot.

## 🎯 **Overview**

Your trading bot now includes **dual webhook integration**:

1. **📊 Trading Logs** → `https://n8n.srv881084.hstgr.cloud/webhook/trading-logs`
2. **📱 Telegram Feedback** → `https://n8n.srv881084.hstgr.cloud/webhook/91126b9d-bd23-4e92-8891-5bfb217455c7`

## 🔧 **Configuration**

### **Environment Variables (.env)**

```env
# N8N Webhooks
N8N_LOG_WEBHOOK=https://n8n.srv881084.hstgr.cloud/webhook/trading-logs
N8N_TELEGRAM_FEEDBACK=https://n8n.srv881084.hstgr.cloud/webhook/91126b9d-bd23-4e92-8891-5bfb217455c7
```

### **What Each Webhook Does**

**📊 Trading Logs Webhook**

- Technical logging for analysis
- JSON formatted data
- Used for debugging and monitoring

**📱 Telegram Feedback Webhook**

- Human-readable messages to Telegram
- Rich formatted notifications
- Real-time trade updates

## 📱 **Telegram Notification Types**

### **1. Signal Received 📊**

```
📊 NEW SIGNAL DETECTED

Symbol: EURUSD
Direction: BUY
Range: 1.0850 - 1.0870
Stop Loss: 1.0800
Take Profit: 1.0950
Time: 2025-10-29 14:30:25
```

### **2. Trade Executed ✅**

```
✅ TRADE EXECUTED SUCCESSFULLY

Symbol: EURUSD
Direction: BUY
Entry Price: 1.0860
Volume: 0.01
Stop Loss: 1.0800
Take Profit: 1.0950
Order ID: 12345
Deal ID: 67890
Execution Time: 2025-10-29 14:30:30
```

### **3. Trade Failed ❌**

```
❌ TRADE EXECUTION FAILED

Symbol: EURUSD
Direction: BUY
Attempted Entry: 1.0860
Error: Insufficient margin
Time: 2025-10-29 14:30:30
```

### **4. System Started 🚀**

```
🚀 TRADING BOT STARTED

Status: Online and monitoring
Group ID: 4867740501
MT5 Connection: ✅ Connected
Time: 2025-10-29 14:25:00
```

### **5. System Stopped 🛑**

```
🛑 TRADING BOT STOPPED

Status: Offline
Time: 2025-10-29 18:45:30
```

### **6. Error Alerts 🚨**

```
🚨 ERROR ALERT

Error Type: mt5_connection
Message: Failed to connect to MT5 terminal
Context: Login attempt failed
Time: 2025-10-29 14:30:00
```

## 🧪 **Testing the Integration**

### **Method 1: Test Script**

```cmd
# On Windows VPS
cd C:\TradingBot
python test_telegram_feedback.py
```

Expected output:

```
✅ Webhook test successful!
✅ Signal Received notification sent successfully
✅ Trade Executed notification sent successfully
✅ System Started notification sent successfully
✅ Error Alert notification sent successfully
🎉 All tests passed!
```

### **Method 2: Manual Test**

```cmd
# Test via curl
curl -X POST "https://n8n.srv881084.hstgr.cloud/webhook/91126b9d-bd23-4e92-8891-5bfb217455c7" ^
     -H "Content-Type: application/json" ^
     -d "{\"message\":\"🧪 Test message from Windows VPS\",\"timestamp\":\"2025-10-29T14:30:00\",\"source\":\"manual_test\"}"
```

### **Method 3: Python Test**

```python
import requests
from datetime import datetime

url = "https://n8n.srv881084.hstgr.cloud/webhook/91126b9d-bd23-4e92-8891-5bfb217455c7"
payload = {
    "message": "🧪 **TEST MESSAGE**\n\nThis is a test from Python script",
    "timestamp": datetime.now().isoformat(),
    "source": "python_test"
}

response = requests.post(url, json=payload)
print(f"Status: {response.status_code}")
```

## 🔄 **Integration Flow**

```
Trading Signal Detected
        ↓
Signal Parsing & Validation
        ↓
📱 Send "Signal Received" to Telegram
        ↓
MT5 Entry Calculation
        ↓
Trade Execution Attempt
        ↓
📱 Send "Trade Result" to Telegram
        ↓
Continue Monitoring...
```

## 🚀 **Deployment Steps**

### **1. Upload Updated Files**

Ensure these files are on your Windows VPS:

- ✅ `direct_mt5_monitor.py` (updated with Telegram feedback)
- ✅ `.env` (with both webhook URLs)
- ✅ `test_telegram_feedback.py` (testing script)

### **2. Install Dependencies**

```cmd
cd C:\TradingBot
pip install requests python-dotenv telethon MetaTrader5
```

### **3. Test Webhook**

```cmd
python test_telegram_feedback.py
```

### **4. Start Trading Bot**

```cmd
python direct_mt5_monitor.py
```

### **5. Verify Notifications**

You should receive a startup message in Telegram:

```
🚀 TRADING BOT STARTED

Status: Online and monitoring
Group ID: 4867740501
MT5 Connection: ✅ Connected
Time: 2025-10-29 14:30:00
```

## 🛠️ **Troubleshooting**

### **No Telegram Messages**

1. Check webhook URL is correct
2. Verify N8N workflow is active
3. Test with `test_telegram_feedback.py`
4. Check bot logs for webhook errors

### **Webhook Timeouts**

```python
# In direct_mt5_monitor.py, TelegramFeedback class
response = requests.post(
    self.webhook_url,
    json=payload,
    timeout=30,  # Increase timeout
    headers={'Content-Type': 'application/json'}
)
```

### **Messages Not Formatted**

- Check N8N workflow processes the `message` field
- Ensure Telegram bot supports Markdown formatting
- Verify webhook payload structure

### **Duplicate Messages**

- Check if bot is running multiple instances
- Verify session files aren't duplicated
- Monitor Windows Task Manager for multiple python processes

## 🔍 **Monitoring & Logs**

### **Bot Logs**

```cmd
# View real-time logs
powershell Get-Content direct_mt5_monitor.log -Wait -Tail 50

# Search for webhook errors
findstr "Telegram" direct_mt5_monitor.log
findstr "webhook" direct_mt5_monitor.log
```

### **Webhook Status Codes**

- `200` - Success ✅
- `400` - Bad request (check payload format)
- `404` - Webhook not found (check URL)
- `500` - N8N server error
- `Timeout` - Network/server issues

## 📊 **Expected Performance**

**✅ Response Times:**

- Webhook calls: <2 seconds
- Signal to notification: <5 seconds
- Trade execution feedback: <3 seconds

**✅ Reliability:**

- 99%+ webhook success rate
- Auto-retry on failures
- Graceful error handling

**✅ Message Types:**

- 📊 Signal notifications: Real-time
- ✅/❌ Trade results: Immediate
- 🚀/🛑 System status: On startup/shutdown
- 🚨 Error alerts: As they occur

## 🎯 **Production Ready**

Your Windows VPS trading bot now includes:

1. **Direct MT5 Integration** - No API limitations
2. **Real-time Signal Monitoring** - Telegram group watching
3. **Instant Trade Execution** - Direct MT5 Python library
4. **Comprehensive Logging** - Technical logs to N8N
5. **Rich Telegram Feedback** - Human-readable notifications
6. **Error Handling** - Graceful failure recovery
7. **Health Monitoring** - System status tracking

Deploy with confidence! Your trading bot will keep you informed of every trade via Telegram. 🎉
