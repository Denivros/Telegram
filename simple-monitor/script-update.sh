#!/bin/bash
echo "🔄 Updating Telegram Monitor with modified script..."

# Extract updated files
tar -xzf telegram-monitor-update.tar.gz
rm -rf telegram-monitor-backup
mv telegram-monitor telegram-monitor-backup 2>/dev/null || true
mkdir -p telegram-monitor
mv telegram_monitor.py setup_session.py requirements.txt .env Dockerfile telegram_monitor.session telegram-monitor/
cd telegram-monitor

# Stop current container
echo "🛑 Stopping current monitor..."
docker stop telegram-monitor 2>/dev/null || true
docker rm telegram-monitor 2>/dev/null || true

# Rebuild with updated script
echo "🔨 Rebuilding with updated script..."
docker build -t telegram-monitor .

# Start with updated script
echo "🚀 Starting updated monitor..."
docker run -d \
    --name telegram-monitor \
    --restart unless-stopped \
    -v $(pwd)/logs:/app/logs \
    telegram-monitor

echo "✅ Monitor updated with your script changes!"
echo ""
echo "📊 Container status:"
docker ps --filter "name=telegram-monitor"

echo ""
echo "📋 Checking logs..."
sleep 3
docker logs telegram-monitor

# Clean up
cd ..
rm -f telegram-monitor-update.tar.gz