# Complete Setup Guide

Step-by-step guide to set up the complete Telegram trading automation system.

## 🏗️ Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Telegram      │    │      n8n        │    │   MetaTrader 5  │
│   Group         │────▶│   Workflows     │────▶│   Trading       │
│   Monitor       │    │   & Database    │    │   Platform      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Direct        │    │   Telegram      │    │   Expert        │
│   MT5 Trading   │    │   Logging       │    │   Advisors      │
│   (Alternative) │    │   System        │    │   (Alternative) │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🚀 Prerequisites

### 1. System Requirements
- **Operating System**: Windows (for MT5), Linux/macOS (for monitoring)
- **Python**: 3.8 or higher
- **MetaTrader 5**: Latest version from your broker
- **n8n**: Self-hosted or cloud instance
- **VPS**: Optional but recommended for 24/7 operation

### 2. Account Requirements
- **Telegram Account**: For API access and group monitoring
- **Broker Account**: MT5-compatible broker with API access
- **Domain/VPS**: For hosting n8n and webhooks (optional)

## 📱 Phase 1: Telegram Setup

### Step 1: Get Telegram API Credentials
1. Visit https://my.telegram.org
2. Login with your phone number
3. Go to "API development tools"
4. Create a new application:
   - **App title**: "Trading Monitor"
   - **Short name**: "trading-monitor"
   - **Platform**: Desktop
5. Save your `API_ID` and `API_HASH`

### Step 2: Find Your Target Group
1. Clone this repository:
   ```bash
   git clone <repository-url>
   cd telegram-trading
   ```

2. Set up basic monitor:
   ```bash
   cd telegram-monitor
   pip install -r requirements.txt
   cp .env.example .env
   ```

3. Edit `.env` with your Telegram credentials:
   ```env
   TELEGRAM_API_ID=your_api_id
   TELEGRAM_API_HASH=your_api_hash
   TELEGRAM_PHONE=+1234567890
   ```

4. Find your target group:
   ```bash
   python list_groups.py
   ```
   
5. Copy the group ID and add to `.env`:
   ```env
   TELEGRAM_GROUP_ID=-1001234567890
   ```

## 🔄 Phase 2: n8n Workflow Setup

### Step 1: Install n8n
Choose one option:

**Option A: Docker (Recommended)**
```bash
docker run -it --rm --name n8n -p 5678:5678 n8nio/n8n
```

**Option B: npm**
```bash
npm install -g n8n
n8n start
```

**Option C: VPS Deployment**
```bash
# On your VPS
curl -L https://github.com/n8n-io/n8n/raw/master/docker/compose/withPostgres/docker-compose.yml -o docker-compose.yml
docker-compose up -d
```

### Step 2: Import Workflows
1. Open n8n at `http://localhost:5678` (or your VPS IP)
2. Go to **Workflows** → **Import from File**
3. Import these files in order:
   - `n8n-workflows/telegram_signal_storage.json`
   - `n8n-workflows/mt5_api_endpoint.json`
   - `n8n-workflows/n8n_trading_logs_workflow.json`

### Step 3: Configure Database
If using SQLite (default):
```bash
# n8n will create this automatically
# Location: ~/.n8n/database.sqlite (or container volume)
```

If using PostgreSQL:
```sql
CREATE DATABASE trading;
CREATE USER n8n WITH ENCRYPTED PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE trading TO n8n;
```

### Step 4: Get Webhook URLs
After importing workflows, note the webhook URLs:
- Signal Storage: `https://your-n8n.com/webhook/telegram`
- Trading Logs: `https://your-n8n.com/webhook/trading-logs`

## 🤖 Phase 3: Telegram Bot Setup (For Notifications)

### Step 1: Create Telegram Bot
1. Message @BotFather on Telegram
2. Send `/newbot`
3. Follow prompts to create bot
4. Save the bot token

### Step 2: Get Your Chat ID
1. Message your bot with `/start`
2. Visit: `https://api.telegram.org/bot<BOT_TOKEN>/getUpdates`
3. Find your chat ID in the response
4. Or use this Python script:
   ```python
   import requests
   token = "YOUR_BOT_TOKEN"
   response = requests.get(f"https://api.telegram.org/bot{token}/getUpdates")
   print(response.json())
   ```

### Step 3: Configure Logging Workflow
1. Open the **Trading Logs** workflow in n8n
2. Update the **Telegram** node with:
   - **Bot Token**: Your bot token
   - **Chat ID**: Your chat ID
3. Save and activate the workflow

## 💹 Phase 4: MetaTrader 5 Setup

### Step 1: Install MT5
1. Download MT5 from your broker
2. Install and login to your account
3. Enable algorithmic trading:
   - **Tools** → **Options** → **Expert Advisors**
   - ✅ **Allow algorithmic trading**
   - ✅ **Allow DLL imports**
   - ✅ **Allow imports of external experts**

### Step 2: Install Python MT5 Package
```bash
pip install MetaTrader5
```

### Step 3: Test MT5 Connection
```python
import MetaTrader5 as mt5

# Test connection
if mt5.initialize():
    print("✅ MT5 connected successfully")
    account_info = mt5.account_info()
    print(f"Account: {account_info.login}")
    print(f"Balance: {account_info.balance}")
    mt5.shutdown()
else:
    print("❌ MT5 connection failed")
```

## 🔧 Phase 5: Choose Integration Method

### Method 1: Direct MT5 Integration (Recommended)

**Best for**: Simple setup, lowest latency, direct control

1. **Setup direct trading system:**
   ```bash
   cd direct-trading
   pip install -r requirements.txt
   cp .env.example .env
   ```

2. **Configure environment:**
   ```env
   # Copy from telegram-monitor/.env and add:
   ENTRY_STRATEGY=adaptive
   DEFAULT_VOLUME=0.01
   N8N_LOG_WEBHOOK=https://your-n8n.com/webhook/trading-logs
   ```

3. **Run the system:**
   ```bash
   python telegram_direct_mt5.py
   ```

### Method 2: HTTP API + n8n (Flexible)

**Best for**: Complex workflows, multiple integrations, web interfaces

1. **Setup MT5 API server:**
   ```bash
   cd mt5-integration
   pip install -r mt5_requirements.txt
   cp mt5_config.env.example mt5_config.env
   ```

2. **Configure MT5 API:**
   ```env
   MT5_LOGIN=your_account_number
   MT5_PASSWORD=your_password
   MT5_SERVER=your_broker_server
   API_HOST=0.0.0.0
   API_PORT=8080
   ```

3. **Run API server:**
   ```bash
   python mt5_api_server.py
   ```

4. **Configure telegram monitor:**
   ```bash
   cd ../telegram-monitor
   # Add to .env:
   N8N_WEBHOOK_URL=https://your-n8n.com/webhook/telegram
   ```

5. **Run monitor:**
   ```bash
   python telegram_monitor.py
   ```

### Method 3: Expert Advisor (Native MT5)

**Best for**: Broker restrictions, native MT5 integration, minimal dependencies

1. **Compile Expert Advisor:**
   - Open MT5 MetaEditor
   - Open `mt5-integration/mt5_expert_advisor.mq5`
   - Compile (F7)

2. **Configure EA settings:**
   - Magic Number: `12345`
   - API URL: `https://your-n8n.com/api/signals`
   - Poll Interval: `5` seconds

3. **Run EA:**
   - Drag compiled EA to a chart
   - Enable auto trading
   - Check that EA is active (green smiley face)

## 🧪 Phase 6: Testing

### Step 1: Test Telegram Monitoring
1. Send a test message to your monitored group:
   ```
   EURUSD BUY RANGE: 1.0850 - 1.0880
   SL: 1.0820
   TP: 1.0920
   ```

2. Check logs to verify message was received and parsed

### Step 2: Test Signal Processing
1. **For Direct MT5**: Check MT5 terminal for new positions
2. **For HTTP API**: Check API server logs for trade execution
3. **For Expert Advisor**: Check MT5 Experts tab for EA activity

### Step 3: Test Telegram Notifications
1. Verify you receive Telegram notifications about:
   - 📊 Signal received
   - 🎯 Entry calculated
   - ✅ Trade executed (or ❌ failed)

### Step 4: Demo Account Testing
⚠️ **CRITICAL**: Always test on demo accounts first!

1. Switch MT5 to demo account
2. Set small volumes (0.01 lots)
3. Monitor for several signals
4. Verify all trades execute correctly
5. Check profit/loss calculations

## 🚀 Phase 7: Production Deployment

### VPS Deployment (Recommended)

1. **Choose VPS provider:**
   - Hostinger VPS (if you already have n8n there)
   - AWS/DigitalOcean for dedicated setup
   - ForexVPS for trading-optimized hosting

2. **Setup VPS:**
   ```bash
   # Update system
   sudo apt update && sudo apt upgrade -y
   
   # Install Python
   sudo apt install python3 python3-pip git -y
   
   # Clone repository
   git clone <your-repository>
   cd telegram-trading
   ```

3. **Configure environment:**
   ```bash
   # Copy your local .env files to VPS
   scp telegram-monitor/.env user@vps:/path/to/project/telegram-monitor/
   scp direct-trading/.env user@vps:/path/to/project/direct-trading/
   ```

4. **Run in screen sessions:**
   ```bash
   # For n8n (if not using Docker)
   screen -S n8n
   n8n start
   # Ctrl+A+D to detach
   
   # For Telegram monitor
   screen -S telegram
   cd telegram-monitor && python3 telegram_monitor.py
   # Ctrl+A+D to detach
   
   # For direct trading (alternative)
   screen -S direct-trading
   cd direct-trading && python3 telegram_direct_mt5.py
   # Ctrl+A+D to detach
   ```

5. **Setup systemd services (optional):**
   ```bash
   # Create service files
   sudo nano /etc/systemd/system/telegram-monitor.service
   ```
   
   ```ini
   [Unit]
   Description=Telegram Trading Monitor
   After=network.target
   
   [Service]
   Type=simple
   User=your_user
   WorkingDirectory=/path/to/project/telegram-monitor
   ExecStart=/usr/bin/python3 telegram_monitor.py
   Restart=always
   
   [Install]
   WantedBy=multi-user.target
   ```
   
   ```bash
   sudo systemctl enable telegram-monitor
   sudo systemctl start telegram-monitor
   ```

### Windows MT5 VPS Setup

1. **Connect to Windows VPS:**
   - Use Remote Desktop Connection
   - Install MT5 and login

2. **Install Python on Windows:**
   ```cmd
   # Download Python from python.org
   # Install with "Add to PATH" checked
   pip install MetaTrader5 requests python-dotenv
   ```

3. **Transfer files:**
   - Copy mt5-integration folder to Windows VPS
   - Configure mt5_config.env with your credentials

4. **Run MT5 API server:**
   ```cmd
   cd mt5-integration
   python mt5_api_server.py
   ```

5. **Setup Windows service (optional):**
   - Use NSSM (Non-Sucking Service Manager)
   - Create service for mt5_api_server.py

## 📊 Phase 8: Monitoring and Maintenance

### Daily Checks
- ✅ All services running (screen -ls or systemctl status)
- ✅ MT5 connected and logged in
- ✅ Recent trades executing correctly
- ✅ Telegram notifications working
- ✅ No error messages in logs

### Weekly Maintenance
- 📊 Review trading performance
- 🔄 Update system packages
- 💾 Backup configuration files
- 🧹 Clean up log files
- 🔍 Monitor resource usage (CPU, RAM, disk)

### Log Monitoring
```bash
# Monitor real-time logs
tail -f telegram-monitor/telegram_monitor.log
tail -f direct-trading/telegram_monitor.log
tail -f mt5-integration/mt5_api.log

# Check for errors
grep -i error *.log
grep -i failed *.log
```

## 🛡️ Security Best Practices

### Environment Variables
- Never commit `.env` files to git
- Use strong, unique passwords
- Rotate API keys regularly
- Use separate credentials for demo/live

### Network Security
- Use HTTPS for all webhook URLs
- Implement API key authentication
- Restrict VPS access by IP
- Use VPN for remote access

### Trading Security
- Set maximum position sizes
- Implement daily/weekly loss limits
- Monitor unusual trading activity
- Have emergency stop procedures

## 🆘 Troubleshooting

### Common Issues

**"Could not find group"**
```bash
# Solution: Use exact group ID from list_groups.py
python list_groups.py
# Copy the exact ID including minus sign
```

**"MT5 connection failed"**
```bash
# Check MT5 is running and logged in
# Verify algorithmic trading is enabled
# Test with simple MT5 script
```

**"n8n webhook not responding"**
```bash
# Check n8n is running
curl -X GET http://your-n8n.com/health
# Check firewall/port settings
# Verify webhook URLs are correct
```

**"Telegram notifications not working"**
```bash
# Test bot token manually
curl -X GET "https://api.telegram.org/bot<TOKEN>/getMe"
# Check chat ID is correct
# Verify n8n workflow is active
```

### Recovery Procedures

**If system stops working:**
1. Check all services are running
2. Review recent log entries for errors
3. Test individual components (Telegram, n8n, MT5)
4. Restart services if needed
5. Verify configuration hasn't changed

**If trades are not executing:**
1. Check MT5 connection and login
2. Verify account has trading permissions
3. Check market is open and symbol exists
4. Test with manual trade in MT5
5. Review signal parsing logs

### Getting Help
- Check logs for specific error messages
- Test each component individually
- Search documentation for similar issues
- Create minimal test cases to isolate problems

## 📈 Advanced Configuration

### Risk Management
```env
# Add to .env files
MAX_DAILY_TRADES=5
MAX_DAILY_LOSS=100.00
MAX_POSITION_SIZE=0.1
ALLOWED_SYMBOLS=EURUSD,GBPUSD,USDJPY
```

### Multiple Groups
```env
# Monitor multiple Telegram groups
TELEGRAM_GROUP_IDS=-1001234567890,-1001234567891,-1001234567892
```

### Custom Strategies
```python
# Add to direct-trading/telegram_direct_mt5.py
def custom_entry_strategy(signal):
    # Your custom logic here
    return entry_price, order_type
```

### Performance Optimization
- Use Redis for caching
- Implement connection pooling
- Optimize database queries
- Use async processing where possible

This completes the comprehensive setup guide. Start with Phase 1 and work through each phase systematically. Always test on demo accounts before going live!