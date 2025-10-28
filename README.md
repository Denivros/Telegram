# Telegram Trading Automation System

A comprehensive system for monitoring Telegram trading signals and automatically executing trades via MetaTrader 5.

## 🚀 Project Structure

```
├── telegram-monitor/          # Basic Telegram group monitoring
│   ├── telegram_monitor.py    # Main monitoring script 
│   ├── list_groups.py         # Helper to find group IDs
│   └── requirements.txt       # Dependencies
│
├── direct-trading/            # Enhanced monitoring with MT5 integration
│   └── telegram_direct_mt5.py # Direct MT5 trading system
│
├── mt5-integration/           # MT5 API server and Expert Advisors
│   ├── mt5_api_server.py      # HTTP API for MT5 
│   ├── mt5_expert_advisor.mq5 # Polling-based EA
│   ├── simple_signal_ea.mq5   # File-based EA
│   └── signal_file_writer.py  # File bridge service
│
├── n8n-workflows/             # n8n automation workflows
│   ├── telegram_signal_storage.json
│   ├── mt5_api_endpoint.json
│   └── n8n_trading_logs_workflow.json
│
└── docs/                      # Documentation
    ├── README.md              # Main documentation
    ├── SETUP_GUIDE.md         # Setup instructions
    └── TELEGRAM_LOGGING_SETUP.md
```

## 🎯 Features

### Signal Processing
- **Real-time Telegram monitoring** - Monitor any Telegram group for trading signals
- **Intelligent signal parsing** - Extract symbol, direction, range, SL, TP from messages
- **Multiple entry strategies** - Adaptive, midpoint, range break, momentum strategies
- **Single entry logic** - Avoid duplicate trades with smart entry calculations

### Trading Integration
- **Direct MT5 connection** - Execute trades directly via MetaTrader5 Python API
- **HTTP API server** - RESTful API for remote MT5 control
- **Expert Advisors** - Native MQL5 solutions for polling and file-based integration
- **Comprehensive logging** - Real-time trade notifications via Telegram

### Automation & Monitoring
- **n8n workflows** - Store signals, manage APIs, send notifications
- **Telegram logging** - Get trade updates directly in Telegram
- **Error handling** - Robust error recovery and notification system
- **Multi-deployment** - Local, VPS, and cloud deployment options

## 🚀 Quick Start

### 1. Basic Telegram Monitor
Monitor a Telegram group and send events to n8n:

```bash
cd telegram-monitor
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your credentials
python list_groups.py  # Find your group ID
python telegram_monitor.py
```

### 2. Direct MT5 Trading
Monitor signals and trade directly with MT5:

```bash
cd direct-trading
# Copy environment from telegram-monitor and add MT5 settings
python telegram_direct_mt5.py
```

### 3. MT5 API Server
Run an HTTP API for remote MT5 control:

```bash
cd mt5-integration
pip install -r mt5_requirements.txt
python mt5_api_server.py
```

## 🔧 Configuration

### Environment Variables
Create `.env` files in each folder with:

```env
# Telegram API (get from https://my.telegram.org)
TELEGRAM_API_ID=your_api_id
TELEGRAM_API_HASH=your_api_hash
TELEGRAM_PHONE=+1234567890
TELEGRAM_GROUP_ID=-1001234567890

# Trading Configuration
ENTRY_STRATEGY=adaptive          # adaptive, midpoint, range_break, momentum
DEFAULT_VOLUME=0.01
MT5_API_URL=http://localhost:8080/trade

# n8n Integration
N8N_WEBHOOK_URL=https://your-n8n.com/webhook/telegram
N8N_LOG_WEBHOOK=https://your-n8n.com/webhook/trading-logs
```

### Entry Strategies

1. **Adaptive** (Recommended): Smart entry based on current price vs signal range
2. **Midpoint**: Enter at the middle of the signal range
3. **Range Break**: Enter when price breaks into the signal range
4. **Momentum**: Aggressive entry at range start/end

## 📊 Signal Format

The system recognizes signals in this format:

```
EURUSD BUY RANGE: 1.0850 - 1.0880
SL: 1.0820
TP: 1.0920
```

## 🔄 Integration Options

### Option 1: Direct MT5 (Recommended)
- `telegram_direct_mt5.py` → Direct MT5 execution
- Real-time processing, minimal latency
- Best for live trading

### Option 2: n8n + HTTP API
- `telegram_monitor.py` → n8n → `mt5_api_server.py` → MT5
- Flexible workflow automation
- Great for complex logic and monitoring

### Option 3: Expert Advisor Polling
- `telegram_monitor.py` → n8n → Database → `mt5_expert_advisor.mq5` → MT5
- Native MT5 integration
- Works with any broker

## 📱 Telegram Logging

Get real-time trade notifications:

1. Set up n8n workflow from `n8n-workflows/n8n_trading_logs_workflow.json`
2. Configure `N8N_LOG_WEBHOOK` in your environment
3. Create a Telegram bot and add to n8n workflow
4. Receive notifications for:
   - 📊 New signals received
   - 🎯 Entry calculations
   - ✅ Successful trades
   - ❌ Failed trades
   - 📈 Market analysis
   - 🚨 System errors

## 🖥️ VPS Deployment

### Hostinger VPS Setup
```bash
# Install Python and dependencies
sudo apt update && sudo apt install python3 python3-pip
pip3 install telethon requests python-dotenv

# Clone and setup
git clone <your-repo>
cd telegram-trading
cp telegram-monitor/.env.example telegram-monitor/.env
# Edit .env with your credentials

# Run in screen session
screen -S telegram-monitor
cd telegram-monitor && python3 telegram_monitor.py
# Ctrl+A+D to detach
```

### With n8n
If you already have n8n running, you can add the Telegram monitor alongside it:

```bash
# Run both n8n and telegram monitor
screen -S n8n         # Your existing n8n
screen -S telegram    # New Telegram monitor
```

## 🛠️ Development

### Adding New Strategies
Add your strategy to `EntryStrategyCalculator.calculate_entry_price()` in the direct trading system.

### Custom Signal Parsing
Modify `TradingSignalParser.parse_signal()` to support different signal formats.

### MT5 API Extensions
Extend `mt5_api_server.py` with additional endpoints for account info, history, etc.

## 📋 Requirements

- Python 3.8+
- MetaTrader 5 (for direct trading)
- Telegram API credentials
- n8n instance (for workflow automation)

## 🔐 Security

- Keep your `.env` files secure and never commit them
- Use different API keys for development and production
- Monitor your trading bot carefully, especially in live markets
- Set appropriate position sizes and risk limits

## 📚 Documentation

- [Setup Guide](docs/SETUP_GUIDE.md) - Detailed installation instructions
- [Telegram Logging Setup](docs/TELEGRAM_LOGGING_SETUP.md) - Configure notifications
- [n8n Workflows](n8n-workflows/) - Ready-to-import workflows

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly (preferably on a demo account)
5. Submit a pull request

## ⚠️ Disclaimer

This is for educational and research purposes. Always test on demo accounts first. Trading involves risk, and you should never risk money you cannot afford to lose. The authors are not responsible for any trading losses.

## 📄 License

MIT License - see LICENSE file for details