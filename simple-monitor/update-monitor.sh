#!/bin/bash
# Auto-update script for Telegram Monitor

echo "🔄 Updating Telegram Monitor on VPS..."
echo "======================================"

# Check if we're in the right directory
if [ ! -f "telegram_monitor.py" ]; then
    echo "❌ Error: Run this script from the simple-monitor directory"
    echo "Current directory: $(pwd)"
    exit 1
fi

echo "📦 Creating update package..."

# Create package with all files
tar -czf telegram-monitor-update.tar.gz \
    telegram_monitor.py \
    setup_session.py \
    requirements.txt \
    .env \
    Dockerfile \
    telegram_monitor.session

if [ ! -f "telegram-monitor-update.tar.gz" ]; then
    echo "❌ Error: Failed to create update package"
    exit 1
fi

echo "📤 Uploading to VPS..."

# Upload to VPS
scp telegram-monitor-update.tar.gz root@31.97.183.241:~/

if [ $? -ne 0 ]; then
    echo "❌ Error: Failed to upload to VPS"
    rm telegram-monitor-update.tar.gz
    exit 1
fi

echo "🔧 Creating VPS update script..."

# Create update script for VPS
cat > vps-update.sh << 'EOF'
#!/bin/bash
echo "🔧 Applying updates on VPS..."

# Extract files
tar -xzf telegram-monitor-update.tar.gz

# Backup old version
echo "📁 Backing up current version..."
rm -rf telegram-monitor-old
mv telegram-monitor telegram-monitor-old 2>/dev/null || true

# Setup new version
mkdir -p telegram-monitor
mv telegram_monitor.py setup_session.py requirements.txt .env Dockerfile telegram_monitor.session telegram-monitor/ 2>/dev/null || true
cd telegram-monitor

# Stop and remove old container
echo "🛑 Stopping old container..."
docker stop telegram-monitor 2>/dev/null || true
docker rm telegram-monitor 2>/dev/null || true

# Rebuild image
echo "🔨 Rebuilding Docker image..."
docker build -t telegram-monitor .

if [ $? -ne 0 ]; then
    echo "❌ Error: Docker build failed"
    exit 1
fi

# Start new container
echo "🚀 Starting updated monitor..."
docker run -d \
    --name telegram-monitor \
    --restart unless-stopped \
    -v $(pwd)/logs:/app/logs \
    telegram-monitor

if [ $? -eq 0 ]; then
    echo "✅ Update complete!"
    echo ""
    echo "📊 Container status:"
    docker ps --filter "name=telegram-monitor"
    echo ""
    echo "📋 Recent logs:"
    sleep 3
    docker logs telegram-monitor --tail 10
else
    echo "❌ Error: Failed to start container"
    exit 1
fi

# Cleanup
cd ..
rm -f telegram-monitor-update.tar.gz
EOF

echo "📤 Uploading and executing update script..."

# Upload and run update script
scp vps-update.sh root@31.97.183.241:~/

if [ $? -eq 0 ]; then
    echo "🚀 Running update on VPS..."
    ssh root@31.97.183.241 'chmod +x vps-update.sh && ./vps-update.sh && rm -f vps-update.sh'
    
    if [ $? -eq 0 ]; then
        echo ""
        echo "🎉 Monitor updated successfully!"
        echo ""
        echo "📋 Useful commands:"
        echo "   View logs: ssh root@31.97.183.241 'docker logs telegram-monitor -f'"
        echo "   Check status: ssh root@31.97.183.241 'docker ps | grep telegram'"
        echo "   Restart: ssh root@31.97.183.241 'docker restart telegram-monitor'"
    else
        echo "❌ Error: Update failed on VPS"
    fi
else
    echo "❌ Error: Failed to upload update script"
fi

# Local cleanup
rm -f telegram-monitor-update.tar.gz vps-update.sh

echo "🧹 Local cleanup complete"