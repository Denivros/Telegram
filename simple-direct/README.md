# Simple Direct MT5 Integration

The **simplest and most reliable** approach: One Python script that does everything.

## ✅ Why This Approach is Best

- **Single component** - No EA, no socket servers, no complex setup
- **Direct MT5 connection** - Uses official MetaTrader5 Python library
- **Real-time logging** - Sends notifications directly to n8n → Telegram
- **Easy deployment** - Just run one Python script
- **Fewer failure points** - Less complexity = more reliability

## Architecture

```
Python Script → MT5 Terminal → n8n → Telegram Notifications
     ↓              ↓
 Telegram      Trade Execution
 Monitor
```

## Quick Setup

### 1. **Install Requirements**

```bash
pip install -r requirements.txt
```

### 2. **Configure Environment**

```bash
cp .env.example .env
# Edit .env with your credentials
```

### 3. **Install MT5 on Same Machine**

- Download MT5 from your broker
- Login to your account
- Enable algorithmic trading

### 4. **Run the Monitor**

```bash
python direct_mt5_monitor.py
```

## Features

### 📊 **Signal Processing**

- Parses Telegram messages for trading signals
- Supports standard signal format:
  ```
  EURUSD BUY RANGE: 1.0850 - 1.0880
  SL: 1.0820
  TP: 1.0920
  ```

### 🎯 **Entry Strategies**

- **Adaptive** (recommended): Smart entry based on current price vs range
- **Midpoint**: Enter at middle of range
- **Range Break**: Enter when price breaks into range
- **Momentum**: Aggressive entry at range start/end

### ⚡ **Direct Trading**

- Market orders for immediate execution
- Pending orders (limit/stop) when price is outside range
- Automatic SL/TP setting
- Position size management

### 📱 **Telegram Logging**

Get real-time notifications:

- 📊 Signal received
- 🎯 Entry calculated
- ✅ Trade executed successfully
- ❌ Trade execution failed
- 🚀 System status updates
- 🚨 Error notifications

## Configuration

### Environment Variables

```env
# Telegram
TELEGRAM_API_ID=22159421
TELEGRAM_API_HASH=your_hash
TELEGRAM_PHONE=+32474071892
TELEGRAM_GROUP_ID=4867740501

# Trading
ENTRY_STRATEGY=adaptive
DEFAULT_VOLUME=0.01
MAGIC_NUMBER=123456

# Logging
N8N_LOG_WEBHOOK=https://n8n.srv881084.hstgr.cloud/webhook/trading-logs
```

### Entry Strategy Details

#### Adaptive (Recommended)

```python
if direction == 'buy':
    if current_price > range_end:
        # Wait for pullback - use limit order at range top
    elif current_price < range_start:
        # Price below range - enter at market immediately
    else:
        # Price in range - enter at market
```

#### Midpoint

Always enters at `(range_start + range_end) / 2`

#### Range Break

- **Buy**: Enter at range_end
- **Sell**: Enter at range_start

#### Momentum

- **Buy**: Enter at range_start (aggressive)
- **Sell**: Enter at range_end (aggressive)

## Deployment Options

### Option 1: Local (Mac/Windows)

Run on your local machine where MT5 is installed:

```bash
python direct_mt5_monitor.py
```

### Option 2: Windows VPS

If you have a Windows VPS with MT5:

1. Copy the script to your VPS
2. Install Python and requirements
3. Run the script

### Option 3: Your MT5 VPS

Since you mentioned having an MT5 VPS:

1. Install Python on your MT5 VPS
2. Copy this folder to the VPS
3. Run the monitor on the same machine as MT5

## Testing

### Demo Account Testing

⚠️ **Always test on demo first!**

1. Switch MT5 to demo account
2. Set `DEFAULT_VOLUME=0.01`
3. Send test signal to monitored group:
   ```
   EURUSD BUY RANGE: 1.0850 - 1.0880
   SL: 1.0820
   TP: 1.0920
   ```
4. Check MT5 terminal for new position
5. Verify Telegram notifications arrive

### Error Testing

Test error handling:

- Invalid symbol names
- Malformed signals
- MT5 connection loss
- Network issues

## Monitoring

### Log Files

- `direct_mt5_monitor.log` - Local log file
- Telegram notifications via n8n

### Health Checks

```bash
# Check if script is running
ps aux | grep direct_mt5_monitor

# Monitor real-time logs
tail -f direct_mt5_monitor.log

# Check for errors
grep -i error direct_mt5_monitor.log
```

## Troubleshooting

### "MT5 initialize() failed"

- Ensure MT5 terminal is running and logged in
- Check algorithmic trading is enabled
- Verify account has trading permissions

### "Could not find group"

- Use exact group ID from `../telegram-monitor/list_groups.py`
- Include minus sign if present: `-1001234567890`

### "Failed to send log to Telegram"

- Check n8n webhook URL is correct
- Verify n8n workflow is active
- Test webhook manually with curl

### "Order failed"

- Check symbol exists and market is open
- Verify sufficient account balance
- Ensure SL/TP levels are valid for broker

## Advantages Over Complex Setups

✅ **vs Socket Approach**: No network communication issues  
✅ **vs EA Approach**: No MQL5 compilation needed  
✅ **vs HTTP API**: No server maintenance required  
✅ **vs File-based**: No file system dependencies

## Production Checklist

- [ ] Test thoroughly on demo account
- [ ] Set appropriate position sizes
- [ ] Configure proper risk management
- [ ] Set up monitoring and alerts
- [ ] Have backup/recovery procedures
- [ ] Monitor system resources
- [ ] Keep logs for analysis

This is the **recommended approach** for most users - simple, reliable, and effective!
