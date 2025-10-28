# Telegram Monitor

Monitor Telegram groups and send events to n8n webhooks for automated processing.

## Features

- Real-time monitoring of Telegram group messages
- Comprehensive event tracking (messages, edits, deletions, member actions)
- Automatic forwarding to n8n webhooks
- Media file detection and information extraction
- Robust error handling and reconnection
- Detailed logging

## Quick Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Get Telegram API credentials:**
   - Go to https://my.telegram.org
   - Create an application and get your `API_ID` and `API_HASH`

3. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

4. **Find your target group:**
   ```bash
   python list_groups.py
   ```

5. **Run the monitor:**
   ```bash
   python telegram_monitor.py
   ```

## Configuration

Edit `.env` file with your settings:

```env
TELEGRAM_API_ID=your_api_id
TELEGRAM_API_HASH=your_api_hash  
TELEGRAM_PHONE=+1234567890
TELEGRAM_GROUP_ID=-1001234567890
N8N_WEBHOOK_URL=https://your-n8n.domain.com/webhook/telegram
```

## Event Types

The monitor sends different event types to your n8n webhook:

### New Messages
- `event_type`: "new_message"
- Message content, sender info, media details
- Reply and forward information

### Message Edits  
- `event_type`: "message_edited"
- Original and new content
- Edit timestamp

### Message Deletions
- `event_type`: "message_deleted" 
- Deleted message IDs

### Chat Actions
- `event_type`: "chat_action"
- User joins, leaves, promotions, etc.

### System Events
- `event_type`: "monitor_started" / "monitor_stopped"
- Monitor status updates

## Usage Tips

- Run in a screen/tmux session for persistent monitoring
- Monitor logs at `telegram_monitor.log`
- Use `list_groups.py` to find correct group IDs
- Test with a small group first

## Troubleshooting

**"Could not find group"**: Use the exact ID from `list_groups.py`
**"Session password needed"**: Disable 2FA temporarily or implement 2FA handling
**"Flood wait error"**: Telegram rate limiting - the script will wait automatically

For more help, check the logs or raise an issue.