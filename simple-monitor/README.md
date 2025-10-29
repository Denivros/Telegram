# Telegram Monitor - Simple Version

A lightweight Telegram signal monitoring bot designed for easy deployment on Hostinger VPS.

## Features

- 📱 Real-time Telegram group monitoring
- 🔍 Signal detection and parsing
- 💊 Health check endpoint for monitoring
- 🐳 Docker containerized for easy deployment
- 📊 Logging and error handling
- 🔄 Auto-restart capability

## Quick Deployment to Hostinger VPS

### Step 1: Upload Files to VPS

```bash
# On your local machine, compress the files
tar -czf telegram-monitor.tar.gz simple-monitor/

# Upload to your Hostinger VPS (replace with your details)
scp telegram-monitor.tar.gz user@your-vps-ip:/home/
```

### Step 2: Setup on Hostinger VPS

```bash
# SSH into your VPS
ssh user@your-vps-ip

# Extract files
cd /home
tar -xzf telegram-monitor.tar.gz
cd simple-monitor

# Make deployment script executable
chmod +x deploy.sh

# Run deployment
./deploy.sh
```

### Step 3: Configure Telegram API

1. Get your Telegram API credentials from https://my.telegram.org
2. Edit the `.env` file:
   ```bash
   nano .env
   ```
3. Fill in your credentials:
   ```
   TELEGRAM_API_ID=your_api_id
   TELEGRAM_API_HASH=your_api_hash
   TELEGRAM_PHONE=+1234567890
   GROUP_NAME=your_group_name
   ```

### Step 4: Start the Monitor

```bash
# If first time setup, run deploy again after configuring .env
./deploy.sh
```

## Manual Docker Commands

```bash
# Build image
docker build -t telegram-monitor .

# Run container
docker run -d \
    --name telegram-monitor \
    --restart unless-stopped \
    -p 8000:8000 \
    -v $(pwd)/.env:/app/.env \
    -v $(pwd)/logs:/app/logs \
    telegram-monitor

# View logs
docker logs telegram-monitor -f

# Stop container
docker stop telegram-monitor && docker rm telegram-monitor
```

## Health Check

The monitor provides a health check endpoint:

- URL: `http://your-vps-ip:8000/health`
- Returns: JSON status of the monitor

## Monitoring

```bash
# Check if running
docker ps | grep telegram-monitor

# View recent logs
docker logs telegram-monitor --tail 50

# Follow live logs
docker logs telegram-monitor -f
```

## Future MetaAPI Integration

This simplified version is ready for MetaAPI integration:

- Signals are parsed and stored
- Health monitoring is in place
- Easy to extend with MetaAPI endpoints

## Troubleshooting

### Container won't start

```bash
# Check logs
docker logs telegram-monitor

# Common issues:
# 1. Missing .env file
# 2. Invalid Telegram credentials
# 3. Port 8000 already in use
```

### Permission issues

```bash
# Fix file permissions
sudo chown -R $USER:$USER /home/telegram-monitor
```

### Network issues

```bash
# Check if port is open
sudo ufw allow 8000
```

## File Structure

```
simple-monitor/
├── telegram_monitor.py    # Main monitoring script
├── requirements.txt       # Python dependencies
├── Dockerfile            # Container configuration
├── deploy.sh            # Deployment script
├── .env.example         # Environment template
└── README.md           # This file
```

## Dependencies

- Python 3.11+
- Telethon (Telegram client)
- Docker (for containerization)
- Basic HTTP server for health checks

Minimal dependencies = easier deployment and maintenance!
