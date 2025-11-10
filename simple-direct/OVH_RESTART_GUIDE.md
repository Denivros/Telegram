# OVH VPS Restart Functionality

The health server now includes a `/restart` endpoint that allows you to remotely reboot your OVH VPS via the OVH API.

## Setup

### 1. Install OVH Python SDK

```bash
pip install ovh
```

### 2. Generate OVH API Credentials

1. Visit [OVH API Token Creation](https://api.ovh.com/createToken/?GET=/me&POST=/vps/*/reboot)
2. Log in with your OVH account
3. Set the following rights:
   - **GET** `/me` (to verify authentication)
   - **POST** `/vps/*/reboot` (to reboot any VPS)
4. Click "Create keys"
5. Save the generated credentials

### 3. Configure Environment Variables

Add these variables to your `.env` file:

```bash
# OVH VPS Management
OVH_ENDPOINT=ovh-eu
OVH_APPLICATION_KEY=your_application_key_here
OVH_APPLICATION_SECRET=your_application_secret_here
OVH_CONSUMER_KEY=your_consumer_key_here
OVH_SERVICE_NAME=vpsXXXXXX.ovh.net
```

**Note:** Replace `vpsXXXXXX.ovh.net` with your actual VPS service name. You can find this in your OVH control panel.

## Usage

### Restart VPS

```bash
curl http://localhost:8080/restart
```

**Response:**
```json
{
  "status": "success",
  "message": "VPS reboot initiated successfully for vpsXXXXXX.ovh.net",
  "ovh_result": {...},
  "user": "YourName",
  "timestamp": "2025-11-10 15:30:45",
  "warning": "Bot will stop responding in ~30 seconds as VPS reboots"
}
```

### Available Health Endpoints

- `GET /health` - Detailed bot and MT5 status
- `GET /alive` - Simple alive check
- `GET /restart` - **NEW**: Restart VPS via OVH API
- `GET /log` - Last 40 log lines (JSON)
- `GET /log?format=html` - HTML log viewer
- `GET /` - Simple status message

## Security Notes

1. **Credentials**: Keep your OVH API credentials secure
2. **Network**: Consider restricting access to the health server port (8080)
3. **Permissions**: The API key only has minimal permissions (read user info + reboot VPS)

## Troubleshooting

### "OVH library not available"
- Install the library: `pip install ovh`

### "OVH credentials not configured" 
- Check your `.env` file has all required OVH variables
- Verify the variable names match exactly

### "OVH authentication failed"
- Double-check your API credentials
- Ensure the consumer key is properly activated
- Verify your OVH account has VPS management permissions

### "Failed to restart VPS"
- Check your `OVH_SERVICE_NAME` matches your actual VPS service name
- Verify your API key has `POST /vps/*/reboot` permission
- Check OVH service status

## Example Integration

You can now create monitoring scripts that automatically restart the VPS:

```bash
#!/bin/bash
# Check if bot is responding
if ! curl -f http://localhost:8080/alive &>/dev/null; then
    echo "Bot not responding, restarting VPS..."
    curl http://localhost:8080/restart
fi
```

## VPS Service Name

To find your VPS service name:
1. Log into [OVH Manager](https://www.ovh.com/manager/)
2. Go to "Bare Metal Cloud" → "VPS"
3. Your service name will be listed (e.g., `vps123456.ovh.net`)