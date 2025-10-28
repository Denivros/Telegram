# Direct Trading with MT5

Enhanced Telegram monitor that connects directly to MetaTrader 5 for automated trading.

## Features

- **Real-time signal processing** - Parse trading signals from Telegram messages
- **Multiple entry strategies** - Adaptive, midpoint, range break, momentum
- **Direct MT5 integration** - Execute trades directly via MetaTrader5 Python API
- **Telegram logging** - Get trade notifications sent back to Telegram via n8n
- **Single entry logic** - Prevent duplicate trades with intelligent entry calculations

## Quick Start

1. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment:**

   ```bash
   cp ../telegram-monitor/.env.example .env
   # Add MT5 and logging configuration to .env
   ```

3. **Required environment variables:**

   ```env
   # Telegram API
   TELEGRAM_API_ID=your_api_id
   TELEGRAM_API_HASH=your_api_hash
   TELEGRAM_PHONE=+1234567890
   TELEGRAM_GROUP_ID=-1001234567890

   # Trading Strategy
   ENTRY_STRATEGY=adaptive
   DEFAULT_VOLUME=0.01

   # MT5 API (if using HTTP API instead of direct)
   MT5_API_URL=http://localhost:8080/trade

   # Telegram Logging
   N8N_LOG_WEBHOOK=https://your-n8n.com/webhook/trading-logs
   ```

4. **Run the enhanced monitor:**
   ```bash
   python telegram_direct_mt5.py
   ```

## Entry Strategies

### Adaptive (Recommended)

Intelligent entry based on current market price vs signal range:

- **Price above range**: Wait for pullback to range top
- **Price below range**: Enter immediately at market
- **Price in range**: Enter at current market price

### Midpoint

Simple entry at the middle of the signal range. Safe but may miss optimal entries.

### Range Break

Enter when price breaks into the signal range:

- **Buy signals**: Enter at range top
- **Sell signals**: Enter at range bottom

### Momentum

Aggressive entry at the start of the range for maximum profit potential.

## Signal Processing

The system automatically parses signals in this format:

```
EURUSD BUY RANGE: 1.0850 - 1.0880
SL: 1.0820
TP: 1.0920
```

Extracted data:

- **Symbol**: EURUSD
- **Direction**: BUY
- **Entry Range**: 1.0850 - 1.0880
- **Stop Loss**: 1.0820
- **Take Profit**: 1.0920

## Telegram Logging

Get real-time notifications about:

📊 **Signal Received**

```
📊 NEW SIGNAL: EURUSD BUY
Range: 1.0850-1.0880
SL: 1.0820 | TP: 1.0920
```

🎯 **Entry Calculated**

```
🎯 ENTRY CALCULATED: EURUSD
Strategy: adaptive
Entry Price: 1.0865
Order Type: limit
```

✅ **Trade Executed**

```
✅ TRADE EXECUTED: EURUSD
Side: BUY
Entry: 1.0865
Volume: 0.01
SL: 1.0820 | TP: 1.0920
Order ID: 12345
```

## Setup Telegram Logging

1. Import the n8n workflow: `../n8n-workflows/n8n_trading_logs_workflow.json`
2. Create a Telegram bot with @BotFather
3. Add bot token to the n8n workflow
4. Set `N8N_LOG_WEBHOOK` to your n8n webhook URL
5. Add your chat ID to receive notifications

## MetaTrader 5 Setup

1. **Install MT5**: Download from your broker
2. **Enable Algo Trading**: Tools → Options → Expert Advisors → Allow algorithmic trading
3. **Install Python package**: `pip install MetaTrader5`
4. **Test connection**: Run a simple script to verify MT5 connection

## Troubleshooting

**"MT5 initialize() failed"**:

- Ensure MT5 is running and logged in
- Check that algorithmic trading is enabled
- Verify your account has trading permissions

**"Could not parse signal"**:

- Check signal format matches expected pattern
- Look for typos in symbol names or numbers
- Enable debug logging to see parsing attempts

**"Failed to send to MT5"**:

- Verify MT5 connection
- Check symbol exists and market is open
- Ensure sufficient account balance
- Verify stop loss and take profit levels are valid

## Testing

Always test on a demo account first:

1. Open demo account with your broker
2. Set `DEFAULT_VOLUME=0.01` for small test trades
3. Monitor logs and Telegram notifications
4. Verify trades appear correctly in MT5

## Production Deployment

For live trading:

1. Use a VPS for 24/7 operation
2. Set appropriate position sizes
3. Monitor system health regularly
4. Have stop-loss safeguards in place
5. Keep detailed logs for analysis

## Integration with Other Systems

This direct trading system can work alongside:

- Basic Telegram monitor for data collection
- n8n workflows for additional automation
- MT5 Expert Advisors for hybrid approaches
- Custom analysis and risk management systems
