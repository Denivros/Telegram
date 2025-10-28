# MT5 Integration

Multiple approaches for integrating MetaTrader 5 with the Telegram monitoring system.

## Components

### HTTP API Server (`mt5_api_server.py`)
Flask-based REST API for remote MT5 control:

- **Market Orders**: Buy/sell at current price
- **Pending Orders**: Limit and stop orders  
- **Position Management**: Modify SL/TP, close positions
- **Account Info**: Balance, equity, margin
- **Symbol Info**: Current prices, spreads

**Usage:**
```bash
pip install -r mt5_requirements.txt
python mt5_api_server.py
```

### Expert Advisors

#### Polling EA (`mt5_expert_advisor.mq5`)
Polls n8n API every few seconds for new signals:
- Checks for unprocessed signals
- Executes trades in MT5
- Updates signal status back to n8n

#### File-based EA (`simple_signal_ea.mq5`)  
Reads signals from local files:
- Monitors `signals/` folder for new files
- Processes signal files and executes trades
- Moves processed files to `processed/` folder

### Bridge Services

#### Signal File Writer (`signal_file_writer.py`)
Converts n8n signals to files for the file-based EA:
- Receives signals from n8n webhook
- Writes formatted signal files
- Handles file locking and error recovery

## Setup Options

### Option 1: HTTP API Integration
```
Telegram → n8n → HTTP API → MT5
```

1. Run `mt5_api_server.py` on your MT5 machine
2. Configure n8n to POST signals to the API
3. API executes trades directly in MT5

### Option 2: Expert Advisor Polling  
```
Telegram → n8n → Database → EA → MT5
```

1. Set up n8n workflow to store signals in database
2. Compile and run `mt5_expert_advisor.mq5` in MT5
3. EA polls n8n API and executes trades

### Option 3: File-based Integration
```
Telegram → n8n → File Writer → File EA → MT5  
```

1. Run `signal_file_writer.py` to receive n8n webhooks
2. Compile and run `simple_signal_ea.mq5` in MT5
3. EA monitors files and executes trades

## Configuration

### HTTP API (`mt5_config.env`)
```env
MT5_LOGIN=your_account_number
MT5_PASSWORD=your_password  
MT5_SERVER=your_broker_server
API_HOST=0.0.0.0
API_PORT=8080
```

### Expert Advisor Settings
Configure in MT5 Expert Advisor settings:
- **Magic Number**: Unique EA identifier
- **Max Risk**: Maximum risk per trade
- **Max Spread**: Maximum allowed spread
- **API URLs**: n8n endpoint URLs for polling EA

## Deployment Scripts

### VPS Setup (`setup_mt5_vps.sh`)
Automated script for VPS deployment:
- Installs Python and dependencies
- Downloads and configures MT5
- Sets up API server and monitoring
- Configures systemd services

```bash
chmod +x setup_mt5_vps.sh
./setup_mt5_vps.sh
```

## Testing

### API Testing
```bash
# Test API connection
curl -X POST http://localhost:8080/trade \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "EURUSD",
    "side": "buy", 
    "type": "market",
    "volume": 0.01,
    "stopLoss": 1.0800,
    "takeProfit": 1.0900
  }'
```

### EA Testing
1. Load EA on demo account
2. Send test signal via n8n
3. Verify trade execution in MT5
4. Check logs for any errors

## Monitoring

### Logs
- **API Server**: `mt5_api.log`  
- **Expert Advisors**: Check MT5 Experts tab
- **File Writer**: `signal_writer.log`

### Health Checks
- API server `/health` endpoint
- EA heartbeat in MT5 logs
- File writer process monitoring

## Production Considerations

### Security
- Use HTTPS for API in production
- Implement authentication/API keys
- Restrict API access to known IPs
- Monitor for suspicious activity

### Reliability  
- Use multiple MT5 instances for redundancy
- Implement circuit breakers for API calls
- Set up monitoring and alerting
- Have rollback procedures ready

### Performance
- Optimize polling intervals
- Use connection pooling for APIs
- Monitor latency and execution times
- Implement proper error handling

## Troubleshooting

**"MT5 connection failed"**:
- Check MT5 is running and logged in
- Verify account credentials in config
- Ensure algorithmic trading is enabled

**"EA not executing trades"**:
- Check EA is active (green smiley face)
- Verify signal format and parsing
- Check account permissions and balance
- Look for errors in MT5 Experts tab

**"API server not responding"**:
- Check if Python process is running
- Verify port is not blocked by firewall
- Check MT5 connection in API server logs
- Restart API server if needed