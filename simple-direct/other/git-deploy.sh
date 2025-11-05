#!/bin/bash
# Git-based deployment script for Hostinger VPS
# This script will clone your repository and set up the trading bot

set -e

echo "🚀 Git-based MT5 Trading Bot Deployment"
echo "======================================="

VPS_IP="31.97.183.241"
REPO_URL="https://github.com/Denivros/Telegram.git"

echo "📡 Connecting to VPS: $VPS_IP"
echo "📦 Repository: $REPO_URL"
echo ""

# Create deployment script that will run on VPS
cat > /tmp/vps_deploy.sh << 'EOF'
#!/bin/bash
set -e

echo "🔧 Setting up MT5 Trading Bot on Ubuntu 24.04..."

# Update system
echo "📦 Updating system packages..."
apt update && apt upgrade -y

# Install essential tools
echo "🛠️ Installing essential tools..."
apt install -y git curl wget nano htop screen

# Install Docker
echo "🐳 Installing Docker..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
fi

# Install Docker Compose
echo "🐙 Installing Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
fi

# Start Docker service
systemctl start docker
systemctl enable docker

# Clone repository
echo "📂 Cloning repository..."
cd /root
if [ -d "Telegram" ]; then
    rm -rf Telegram
fi
git clone https://github.com/Denivros/Telegram.git

# Navigate to project directory
cd /root/Telegram/simple-direct

# Make scripts executable
chmod +x *.sh
chmod +x docker/*.sh

# Display deployment status
echo ""
echo "✅ Deployment completed successfully!"
echo ""
echo "📁 Project location: /root/Telegram/simple-direct"
echo "📋 Next steps:"
echo "   1. Configure your .env file: nano .env"
echo "   2. Build container: ./docker-manage.sh build"
echo "   3. Start bot: ./docker-manage.sh start"
echo "   4. Monitor logs: ./docker-manage.sh logs -f"
echo ""
echo "🔍 Useful commands:"
echo "   - Check status: ./docker-manage.sh status"
echo "   - View logs: ./docker-manage.sh logs"
echo "   - Restart: ./docker-manage.sh restart"
echo "   - Shell access: ./docker-manage.sh shell"
echo ""
echo "📊 System info:"
docker --version
docker-compose --version
echo "Git repository cloned successfully"
ls -la /root/Telegram/simple-direct/
EOF

# Upload and run deployment script
echo "📤 Uploading deployment script to VPS..."
scp /tmp/vps_deploy.sh root@$VPS_IP:/tmp/

echo "🚀 Running deployment on VPS..."
ssh root@$VPS_IP "chmod +x /tmp/vps_deploy.sh && /tmp/vps_deploy.sh"

echo ""
echo "🎉 Deployment completed! Your trading bot is ready."
echo ""
echo "🔌 To access your VPS:"
echo "   ssh root@$VPS_IP"
echo "   cd /root/Telegram/simple-direct"
echo ""
echo "⚙️ To configure and start:"
echo "   nano .env  # Add your credentials"
echo "   ./docker-manage.sh build"
echo "   ./docker-manage.sh start"

# Cleanup
rm /tmp/vps_deploy.sh