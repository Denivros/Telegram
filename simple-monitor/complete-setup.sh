#!/bin/bash

# Simple setup script for Docker deployment with session creation

echo "🔧 Telegram Monitor Docker Setup"
echo "================================"

# First, let's create the session interactively on your local machine
echo "Step 1: Creating Telegram session locally..."
echo "You'll need to enter the verification code from Telegram"

cd /Users/victorivros/Documents/Analyte/Python/Telegram/simple-monitor

# Run session setup locally
python3 setup_session.py

if [ -f "telegram_monitor.session" ]; then
    echo "✅ Session created successfully!"
    
    # Now package everything including the session file
    echo "📦 Creating deployment package with session..."
    tar -czf telegram-monitor-complete.tar.gz \
        telegram_monitor.py \
        setup_session.py \
        requirements.txt \
        .env \
        Dockerfile \
        telegram_monitor.session
    
    echo "📤 Uploading complete package to VPS..."
    scp telegram-monitor-complete.tar.gz root@31.97.183.241:~/
    
    # Create final deployment script
    cat > final-deploy.sh << 'EOF'
#!/bin/bash
echo "🚀 Final Docker deployment with session..."

# Extract all files
tar -xzf telegram-monitor-complete.tar.gz
mkdir -p telegram-monitor
mv telegram_monitor.py setup_session.py requirements.txt .env Dockerfile telegram_monitor.session telegram-monitor/
cd telegram-monitor

# Stop existing container
docker stop telegram-monitor 2>/dev/null || true
docker rm telegram-monitor 2>/dev/null || true

# Build new image
docker build -t telegram-monitor .

# Run with session file mounted
docker run -d \
    --name telegram-monitor \
    --restart unless-stopped \
    -v $(pwd)/telegram_monitor.session:/app/telegram_monitor.session \
    -v $(pwd)/logs:/app/logs \
    telegram-monitor

echo "✅ Telegram Monitor is running!"
docker ps --filter "name=telegram-monitor"
EOF

    scp final-deploy.sh root@31.97.183.241:~/
    
    echo "✅ Everything uploaded!"
    echo ""
    echo "🔗 Now SSH into your VPS and run:"
    echo "   ssh root@31.97.183.241"
    echo "   chmod +x final-deploy.sh"
    echo "   ./final-deploy.sh"
    
    # Clean up
    rm telegram-monitor-complete.tar.gz final-deploy.sh
    
else
    echo "❌ Session creation failed. Please check your Telegram credentials."
fi