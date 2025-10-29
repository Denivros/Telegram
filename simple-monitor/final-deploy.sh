#!/bin/bash
echo "🚀 Final Docker deployment with authenticated session..."

# Extract all files
tar -xzf telegram-monitor-complete.tar.gz
mkdir -p telegram-monitor
mv telegram_monitor.py setup_session.py requirements.txt .env Dockerfile telegram_monitor.session telegram-monitor/
cd telegram-monitor

# Stop existing container
docker stop telegram-monitor 2>/dev/null || true
docker rm telegram-monitor 2>/dev/null || true

# Build new image
echo "🔨 Building Docker image..."
docker build -t telegram-monitor .

# Run with session file and proper volume mounts
echo "🐳 Starting Telegram Monitor with authenticated session..."
docker run -d \
    --name telegram-monitor \
    --restart unless-stopped \
    -v $(pwd)/logs:/app/logs \
    telegram-monitor

echo "✅ Telegram Monitor is running with authenticated session!"
echo ""
echo "📊 Container status:"
docker ps --filter "name=telegram-monitor"
echo ""
echo "📋 Useful commands:"
echo "   docker logs telegram-monitor -f    # View live logs"
echo "   docker restart telegram-monitor    # Restart container"
echo "   docker stop telegram-monitor       # Stop container"

# Clean up
cd ..
rm -f telegram-monitor-complete.tar.gz