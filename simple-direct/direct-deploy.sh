#!/bin/bash
# Direct file deployment to Hostinger VPS
# This script uploads files directly without using Git

set -e

echo "🚀 Direct MT5 Trading Bot Deployment"
echo "===================================="

VPS_IP="31.97.183.241"
PROJECT_DIR="/root/telegram-bot"

echo "📡 Connecting to VPS: $VPS_IP"
echo "📂 Project directory: $PROJECT_DIR"
echo ""

# Create the project directory on VPS
echo "📁 Creating project directory on VPS..."
ssh root@$VPS_IP "mkdir -p $PROJECT_DIR"

# Upload all necessary files
echo "📤 Uploading project files..."

# Upload main Python file
echo "  - Uploading direct_mt5_monitor.py..."
scp direct_mt5_monitor.py root@$VPS_IP:$PROJECT_DIR/

# Upload requirements
echo "  - Uploading requirements.txt..."
scp requirements.txt root@$VPS_IP:$PROJECT_DIR/

# Upload .env template
echo "  - Uploading .env template..."
scp .env root@$VPS_IP:$PROJECT_DIR/

# Upload Docker files
echo "  - Uploading Docker configuration..."
scp Dockerfile root@$VPS_IP:$PROJECT_DIR/
scp docker-compose.yml root@$VPS_IP:$PROJECT_DIR/
scp docker-manage.sh root@$VPS_IP:$PROJECT_DIR/

# Upload docker helper scripts
echo "  - Uploading Docker helper scripts..."
ssh root@$VPS_IP "mkdir -p $PROJECT_DIR/docker"
scp docker/*.sh root@$VPS_IP:$PROJECT_DIR/docker/

# Upload documentation
echo "  - Uploading documentation..."
scp *.md root@$VPS_IP:$PROJECT_DIR/ 2>/dev/null || true

# Create setup script that will run on VPS
cat > /tmp/vps_setup.sh << 'EOF'
#!/bin/bash
set -e

PROJECT_DIR="/root/telegram-bot"
cd $PROJECT_DIR

echo "🔧 Setting up MT5 Trading Bot on Ubuntu 24.04..."

# Update system
echo "📦 Updating system packages..."
apt update

# Install essential tools
echo "🛠️ Installing essential tools..."
apt install -y git curl wget nano htop screen

# Install Docker if not present
echo "🐳 Installing Docker..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
fi

# Install Docker Compose if not present
echo "🐙 Installing Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    chmod +x /usr/local/bin/docker-compose
fi

# Start Docker service
systemctl start docker
systemctl enable docker

# Make scripts executable
echo "🔑 Making scripts executable..."
chmod +x *.sh
chmod +x docker/*.sh

# Display project info
echo ""
echo "✅ Setup completed successfully!"
echo ""
echo "📁 Project location: $PROJECT_DIR"
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
echo ""
echo "📁 Project files:"
ls -la
EOF

# Upload and run setup script
echo "📤 Uploading setup script..."
scp /tmp/vps_setup.sh root@$VPS_IP:$PROJECT_DIR/

echo "🚀 Running setup on VPS..."
ssh root@$VPS_IP "chmod +x $PROJECT_DIR/vps_setup.sh && $PROJECT_DIR/vps_setup.sh"

echo ""
echo "🎉 Deployment completed! Your trading bot is ready."
echo ""
echo "🔌 To access your VPS:"
echo "   ssh root@$VPS_IP"
echo "   cd $PROJECT_DIR"
echo ""
echo "⚙️ To configure and start:"
echo "   nano .env  # Add your credentials"
echo "   ./docker-manage.sh build"
echo "   ./docker-manage.sh start"

# Cleanup
rm /tmp/vps_setup.sh

echo ""
echo "🔗 Quick start commands:"
echo "   ssh root@$VPS_IP 'cd $PROJECT_DIR && nano .env'"
echo "   ssh root@$VPS_IP 'cd $PROJECT_DIR && ./docker-manage.sh build'"
echo "   ssh root@$VPS_IP 'cd $PROJECT_DIR && ./docker-manage.sh start'"