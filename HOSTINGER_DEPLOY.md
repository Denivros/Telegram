# 🚀 Hostinger Docker Compose Deployment Guide

## Quick Deploy via Hostinger Dashboard

### Step 1: Repository Setup

Your MT5 Trading Bot is ready for deployment! All files are in the `simple-direct/` folder.

### Step 2: Hostinger Deployment

1. **Go to Hostinger Dashboard** → VPS Management
2. **Select Docker Compose from URL**
3. **Use this repository URL:**
   ```
   https://github.com/Denivros/Telegram
   ```
4. **Set the context path:**
   ```
   simple-direct/
   ```

### Step 3: Environment Configuration

The deployment will automatically use the `.env` file which contains:

- ✅ Telegram API credentials
- ✅ MT5 VPS connection details
- ✅ Trading configuration
- ✅ N8N webhook URL

### Step 4: Monitor Deployment

After deployment, you can:

- **View logs**: Check container logs in Hostinger dashboard
- **Monitor status**: Container health checks are configured
- **Access VNC**: Port 5900 (if needed for debugging)

## Repository Structure

```
simple-direct/
├── docker-compose.yml     # Main deployment configuration
├── Dockerfile            # Container build instructions
├── direct_mt5_monitor.py # Main trading bot
├── .env                  # Environment variables (configured)
├── requirements.txt      # Python dependencies
├── docker/              # Helper scripts
│   ├── start.sh         # Container startup
│   ├── healthcheck.sh   # Health monitoring
│   └── setup.sh         # Environment setup
└── README.md           # Documentation
```

## 🎯 What Happens After Deploy

1. **Container Build**: Ubuntu 24.04 + Python 3.12 + Dependencies
2. **Bot Startup**: Connects to Telegram API and MT5 VPS
3. **Signal Processing**: Monitors group for trading signals
4. **Automated Trading**: Executes trades on PUPrime Demo

## 🔧 Troubleshooting

- **Build fails**: Check logs in Hostinger dashboard
- **Connection issues**: Verify .env credentials
- **Trading problems**: Check MT5 VPS connection

## 📊 Features Included

- ✅ Remote MT5 connection (no local Wine needed)
- ✅ Telegram signal monitoring
- ✅ Adaptive entry strategies
- ✅ Health monitoring
- ✅ Comprehensive logging
- ✅ N8N webhook integration

Ready to deploy! 🚀
