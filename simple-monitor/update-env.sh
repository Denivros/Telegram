#!/bin/bash

# Quick update script for .env changes
echo "🔄 Updating Telegram Monitor with new .env configuration..."

# Create updated package
tar -czf telegram-monitor-update.tar.gz \
    telegram_monitor.py \
    setup_session.py \
    requirements.txt \
    .env \
    Dockerfile \
    telegram_monitor.session

echo "📤 Uploading updated package..."
scp telegram-monitor-update.tar.gz root@31.97.183.241:~/

# Create quick update script for VPS
cat > quick-update.sh << 'EOF'
#!/bin/bash
echo "🔄 Applying .env updates..."

# Extract updated files
tar -xzf telegram-monitor-update.tar.gz
rm -rf telegram-monitor-old
mv telegram-monitor telegram-monitor-old 2>/dev/null || true
mkdir -p telegram-monitor
mv telegram_monitor.py setup_session.py requirements.txt .env Dockerfile telegram_monitor.session telegram-monitor/
cd telegram-monitor

# Stop current container
echo "🛑 Stopping current monitor..."
docker stop telegram-monitor
docker rm telegram-monitor

# Rebuild with new .env
echo "🔨 Rebuilding with updated configuration..."
docker build -t telegram-monitor .

# Start with new config
echo "🚀 Starting updated monitor..."
docker run -d \
    --name telegram-monitor \
    --restart unless-stopped \
    -v $(pwd)/logs:/app/logs \
    telegram-monitor

echo "✅ Monitor updated successfully!"
docker ps --filter "name=telegram-monitor"

# Clean up
cd ..
rm -f telegram-monitor-update.tar.gz
EOF

scp quick-update.sh root@31.97.183.241:~/

echo "✅ Update package uploaded!"
echo ""
echo "🔗 Now run on your VPS:"
echo "   ssh root@31.97.183.241"
echo "   chmod +x quick-update.sh"
echo "   ./quick-update.sh"

# Clean up local files
rm telegram-monitor-update.tar.gz quick-update.sh