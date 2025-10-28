# n8n Workflows

Ready-to-import n8n workflows for Telegram trading automation.

## Workflows

### 1. Telegram Signal Storage (`telegram_signal_storage.json`)

Receives Telegram events and stores trading signals in a database.

**Features:**

- Webhook trigger for Telegram monitor
- Signal parsing and validation
- SQLite/PostgreSQL storage
- Duplicate signal prevention
- Signal status tracking

**Setup:**

1. Import workflow in n8n
2. Configure database connection
3. Update webhook URL in Telegram monitor
4. Test with sample signal

### 2. MT5 API Endpoint (`mt5_api_endpoint.json`)

Provides REST API endpoints for MT5 trading operations.

**Features:**

- RESTful API for signal submission
- Input validation and sanitization
- MT5 HTTP API integration
- Response formatting
- Error handling

**Endpoints:**

- `POST /webhook/trade` - Execute new trade
- `GET /api/signals` - Get stored signals
- `PUT /api/signals/{id}` - Update signal status
- `GET /api/account` - Get account info

**Setup:**

1. Import workflow in n8n
2. Configure MT5 API server URL
3. Set up authentication (optional)
4. Test endpoints with Postman/curl

### 3. Trading Logs Workflow (`n8n_trading_logs_workflow.json`)

Sends trading notifications to Telegram via bot.

**Features:**

- Webhook trigger for log events
- Message formatting with emojis
- Multiple chat support
- Log level filtering
- Rate limiting protection

**Log Types:**

- 📊 Signal received
- 🎯 Entry calculated
- ✅ Trade executed
- ❌ Trade failed
- 📈 Market analysis
- 🚨 System errors
- 🚀 System status

**Setup:**

1. Create Telegram bot with @BotFather
2. Get bot token and add to workflow
3. Add your chat ID for notifications
4. Import workflow in n8n
5. Configure webhook URL in trading systems

## Installation

### Import Workflows

1. Open n8n interface
2. Go to Workflows → Import from File
3. Select JSON file from this folder
4. Review and activate workflow

### Required n8n Nodes

Install these community nodes if not available:

```bash
# In n8n Docker container or installation
npm install n8n-nodes-sqlite
npm install n8n-nodes-postgres
npm install n8n-nodes-telegram
```

## Configuration

### Database Setup (Signal Storage)

```sql
-- SQLite/PostgreSQL table for signals
CREATE TABLE trading_signals (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  symbol VARCHAR(20) NOT NULL,
  direction VARCHAR(10) NOT NULL,
  range_start DECIMAL(10,5) NOT NULL,
  range_end DECIMAL(10,5) NOT NULL,
  stop_loss DECIMAL(10,5) NOT NULL,
  take_profit DECIMAL(10,5) NOT NULL,
  status VARCHAR(20) DEFAULT 'pending',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  processed_at TIMESTAMP NULL,
  original_message TEXT,
  execution_result TEXT
);
```

### Environment Variables

Set these in n8n environment or workflow settings:

```env
# Database
DB_TYPE=sqlite
DB_PATH=/data/signals.db
# or for PostgreSQL:
# DB_HOST=localhost
# DB_PORT=5432
# DB_USER=n8n
# DB_PASSWORD=password
# DB_NAME=trading

# MT5 API
MT5_API_URL=http://mt5-server:8080
MT5_API_KEY=optional_api_key

# Telegram Bot
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
```

## Webhook URLs

After importing workflows, you'll get webhook URLs like:

```
https://your-n8n.domain.com/webhook/telegram
https://your-n8n.domain.com/webhook/trading-logs
https://your-n8n.domain.com/api/signals
```

Update these URLs in:

- Telegram monitor configuration
- Direct trading system configuration
- MT5 Expert Advisor settings

## Testing

### Signal Storage Workflow

```bash
curl -X POST https://your-n8n.com/webhook/telegram \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "new_message",
    "message_text": "EURUSD BUY RANGE: 1.0850 - 1.0880\nSL: 1.0820\nTP: 1.0920",
    "timestamp": "2024-01-01T12:00:00Z"
  }'
```

### Trading Logs Workflow

```bash
curl -X POST https://your-n8n.com/webhook/trading-logs \
  -H "Content-Type: application/json" \
  -d '{
    "log_type": "trade_execution",
    "level": "SUCCESS",
    "message": "✅ TRADE EXECUTED: EURUSD\\nSide: BUY\\nEntry: 1.0865",
    "data": {"symbol": "EURUSD", "side": "buy"}
  }'
```

## Monitoring

### Workflow Execution Logs

- Check n8n execution history for errors
- Monitor webhook response times
- Set up workflow failure notifications

### Database Monitoring

```sql
-- Check recent signals
SELECT * FROM trading_signals
WHERE created_at > datetime('now', '-1 hour');

-- Signal processing statistics
SELECT
  status,
  COUNT(*) as count,
  AVG(julianday(processed_at) - julianday(created_at)) * 24 * 60 as avg_processing_minutes
FROM trading_signals
WHERE created_at > datetime('now', '-24 hours')
GROUP BY status;
```

## Customization

### Adding New Signal Formats

Modify the signal parsing logic in the signal storage workflow:

1. Update regex patterns for new formats
2. Add field mapping for extracted data
3. Test with sample messages

### Additional Notifications

Extend the logging workflow:

1. Add new log types and emojis
2. Create message templates
3. Add conditional routing for different chats
4. Implement message threading/topics

### API Extensions

Add new endpoints to MT5 API workflow:

1. Account information endpoint
2. Position management endpoints
3. Historical data endpoints
4. Risk management endpoints

## Backup and Recovery

### Export Workflows

Regularly export your customized workflows:

```bash
# From n8n CLI
n8n export:workflow --id=workflow_id --output=backup.json
```

### Database Backups

```bash
# SQLite backup
sqlite3 /data/signals.db ".backup /backups/signals_$(date +%Y%m%d).db"

# PostgreSQL backup
pg_dump trading > /backups/trading_$(date +%Y%m%d).sql
```

## Production Tips

### Scaling

- Use PostgreSQL for high-volume trading
- Implement connection pooling
- Set up n8n clustering for reliability
- Use Redis for caching if needed

### Security

- Use HTTPS for all webhook URLs
- Implement API key authentication
- Restrict webhook access by IP
- Encrypt sensitive data in database

### Monitoring

- Set up uptime monitoring for webhooks
- Create alerts for failed executions
- Monitor database performance
- Log all API calls for audit trails
