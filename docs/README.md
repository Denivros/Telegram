# Telegram Group Monitor for n8n

A Python script that monitors Telegram groups using your personal account and sends all events to n8n via webhooks.

## Features

- 🔍 **Real-time monitoring** of Telegram groups using your personal account
- 📱 **No bot required** - uses your existing Telegram account
- 🚀 **Direct n8n integration** via webhooks
- 📝 **Comprehensive event tracking**:
  - New messages (text, media, documents)
  - Message edits and deletions
  - User joins and leaves
  - Media information (photos, videos, documents, etc.)
  - Forward and reply information
- 🛡️ **Robust error handling** with automatic reconnection
- 📊 **Detailed logging** for debugging and monitoring
- ⚡ **Async/await** for high performance

## What Data is Sent to n8n

The script sends structured JSON data to your n8n webhook for each event:

### Message Events

```json
{
  "event_type": "new_message",
  "message_id": 12345,
  "message_text": "Hello world!",
  "message_date": "2023-10-27T10:30:00",
  "sender": {
    "id": 123456789,
    "first_name": "John",
    "last_name": "Doe",
    "username": "johndoe",
    "is_bot": false
  },
  "media": {
    "has_media": true,
    "media_type": "photo",
    "photo_id": 98765
  },
  "group_info": {
    "id": -1001234567890,
    "title": "My Group",
    "username": "mygroup"
  },
  "timestamp": "2023-10-27T10:30:01.123456"
}
```

### Other Event Types

- `message_edited` - When messages are edited
- `message_deleted` - When messages are deleted
- `chat_action` - User joins, leaves, etc.
- `monitor_started` - When monitoring begins
- `monitor_stopped` - When monitoring stops

## Installation & Setup

### 1. Get Telegram API Credentials

1. Go to https://my.telegram.org
2. Log in with your phone number
3. Click "API Development Tools"
4. Create a new application:
   - App title: "Telegram Monitor"
   - Short name: "tg_monitor"
   - Platform: "Desktop"
5. Save your `API ID` and `API Hash`

### 2. Get Group ID

**Method 1: Using Bot (Easiest)**

1. Forward any message from the target group to @userinfobot
2. It will reply with the group ID (starts with -100)

**Method 2: Using Group Username**

- If the group has a public username, you can use `@groupname` or just `groupname`

### 3. Set up n8n Webhook

1. In your n8n workflow, add a **Webhook** trigger node
2. Set the method to `POST`
3. Copy the webhook URL (something like `https://your-n8n.com/webhook/telegram-monitor`)

### 4. Configure the Script

1. Copy the configuration template:

   ```bash
   cp .env.example .env
   ```

2. Edit `.env` with your credentials:

   ```bash
   # Your Telegram API credentials
   TELEGRAM_API_ID=1234567
   TELEGRAM_API_HASH=abcdef1234567890abcdef1234567890

   # Your phone number (with country code)
   TELEGRAM_PHONE=+1234567890

   # Target group (ID or username)
   TELEGRAM_GROUP_ID=-1001234567890
   # OR
   TELEGRAM_GROUP_ID=@groupname

   # Your n8n webhook URL
   N8N_WEBHOOK_URL=https://your-n8n.com/webhook/telegram-monitor
   ```

### 5. Install Dependencies

```bash
# The script uses a virtual environment
/Users/victorivros/Documents/Analyte/Python/Test/.venv/bin/python -m pip install telethon requests python-dotenv
```

### 6. Run the Monitor

```bash
/Users/victorivros/Documents/Analyte/Python/Test/.venv/bin/python telegram_monitor.py
```

## First Run Authentication

On the first run, Telegram will ask you to:

1. Enter the verification code sent to your phone
2. If you have 2FA enabled, enter your password

The session will be saved locally, so you won't need to authenticate again.

## Example n8n Workflow

Here's a simple n8n workflow to get started:

1. **Webhook Trigger** - Receives data from the script
2. **Switch Node** - Routes based on `event_type`
3. **Function Nodes** - Process different event types
4. **Database/API Nodes** - Store or forward the data

Example Switch conditions:

- `new_message` → Process new messages
- `message_edited` → Handle edits
- `chat_action` → Track member changes

## Monitoring and Logs

The script creates detailed logs in `telegram_monitor.log`:

- Connection status
- Messages sent to n8n
- Errors and reconnection attempts
- Performance metrics

## Security Notes

- ⚠️ **Keep your API credentials secure** - Never commit `.env` to version control
- 🔒 **Session files** contain authentication tokens - keep them private
- 🛡️ **Network security** - Ensure your n8n webhook URL is secure (HTTPS)
- 📱 **Account access** - The script uses your personal Telegram account

## Troubleshooting

### Common Issues

**"Could not find group"**

- Verify the group ID/username in `.env`
- Make sure you're a member of the group
- Try using the numeric ID instead of username

**"Failed to authorize user"**

- Check your API credentials
- Delete the session file and re-authenticate
- Disable 2FA temporarily if needed

**"Connection failed"**

- Check your internet connection
- Verify n8n webhook URL is accessible
- Check firewall settings

**"Flood wait error"**

- Telegram is rate limiting - the script will wait automatically
- Reduce monitoring frequency if this happens often

### Debug Mode

Add this to see more detailed logs:

```python
# In telegram_monitor.py, change logging level
logging.basicConfig(level=logging.DEBUG, ...)
```

## Limitations

- **Rate limits**: Telegram has API limits - don't spam
- **Message history**: Only sees messages sent after the script starts
- **Group permissions**: Must be a member of the group
- **2FA**: Two-factor authentication makes setup more complex

## Advanced Usage

### Custom Event Filtering

Modify the event handlers to filter specific content:

```python
@self.client.on(events.NewMessage(chats=self.target_group))
async def handle_new_message(event):
    # Only send messages with specific keywords
    if 'important' in event.message.text.lower():
        # ... send to n8n
```

### Multiple Groups

To monitor multiple groups, modify `TELEGRAM_GROUP_ID` to include multiple IDs:

```python
# In the script, you can extend to handle multiple groups
groups = [group1_id, group2_id, group3_id]
```

### Media Download

The script can be extended to download media files:

```python
# Add to handle_new_message
if message.media:
    file_path = await message.download_media('downloads/')
    data['media']['local_path'] = file_path
```

## Contributing

Feel free to submit issues and pull requests to improve the script!

## License

This project is open source. Use responsibly and respect Telegram's Terms of Service.
