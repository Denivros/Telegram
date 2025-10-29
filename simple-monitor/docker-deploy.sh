#!/bin/bash

# Docker deployment script for Hostinger VPS
# Simple one-command deployment

VPS_IP="31.97.183.241"
VPS_USER="root"

echo "🐳 Docker Deployment to Hostinger VPS"
echo "======================================"

# Create deployment package
echo "📦 Creating deployment package..."
tar -czf telegram-monitor-docker.tar.gz \
    telegram_monitor.py \
    requirements.txt \
    .env \
    Dockerfile

echo "📤 Uploading to VPS..."
scp telegram-monitor-docker.tar.gz $VPS_USER@$VPS_IP:~/

# Create setup script for VPS
cat > docker-setup.sh << 'EOF'
#!/bin/bash
echo "🔧 Setting up Docker deployment..."

# Extract files
tar -xzf telegram-monitor-docker.tar.gz
mkdir -p telegram-monitor
mv telegram_monitor.py requirements.txt .env Dockerfile telegram-monitor/
cd telegram-monitor

# Install Docker if not present
if ! command -v docker &> /dev/null; then
    echo "🐳 Installing Docker..."
    apt update
    apt install -y docker.io
    systemctl start docker
    systemctl enable docker
fi

# Stop existing container if running
if docker ps -q --filter "name=telegram-monitor" | grep -q .; then
    echo "🛑 Stopping existing container..."
    docker stop telegram-monitor
    docker rm telegram-monitor
fi

# Build Docker image
echo "🔨 Building Docker image..."
docker build -t telegram-monitor .

# Run container with restart policy
echo "🚀 Starting Telegram Monitor container..."
docker run -d \
    --name telegram-monitor \
    --restart unless-stopped \
    -v $(pwd)/logs:/app/logs \
    telegram-monitor

# Check status
echo "✅ Deployment complete!"
echo ""
docker ps --filter "name=telegram-monitor"
echo ""
echo "📋 Useful commands:"
echo "   docker logs telegram-monitor -f    # View live logs"
echo "   docker restart telegram-monitor    # Restart container"
echo "   docker stop telegram-monitor       # Stop container"

# Clean up
cd ..
rm -f telegram-monitor-docker.tar.gz docker-setup.sh
EOF

# Upload setup script
scp docker-setup.sh $VPS_USER@$VPS_IP:~/

echo "✅ Files uploaded successfully!"
echo ""
echo "🔗 Now SSH into your VPS and run:"
echo "   ssh $VPS_USER@$VPS_IP"
echo "   chmod +x docker-setup.sh"
echo "   ./docker-setup.sh"
echo ""
echo "🐳 Your Telegram monitor will run in Docker with auto-restart!"

# Clean up local files
rm docker-setup.sh telegram-monitor-docker.tar.gz