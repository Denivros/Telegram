#!/bin/bash
#
# Quick Upload Script for Trading Bot Files
# Run this from your Mac to upload files to Hostinger VPS
#

# Configuration - UPDATED WITH YOUR HOSTINGER VPS
VPS_IP="31.97.183.241"
VPS_USER="root"
PROJECT_PATH="/root/trading-bot/simple-direct"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}🚀 Trading Bot File Upload Script${NC}"
echo "=================================="

# Check if VPS IP is configured
if [ "$VPS_IP" = "your-vps-ip-address" ]; then
    echo -e "${RED}❌ Please edit this script and set your VPS_IP${NC}"
    echo "Edit the VPS_IP variable at the top of this script"
    exit 1
fi

# Get current directory (should be simple-direct)
CURRENT_DIR=$(pwd)
if [[ ! "$CURRENT_DIR" =~ simple-direct$ ]]; then
    echo -e "${RED}❌ Please run this script from the simple-direct directory${NC}"
    exit 1
fi

echo -e "${BLUE}📂 Current directory: $CURRENT_DIR${NC}"
echo -e "${BLUE}🎯 Target VPS: $VPS_USER@$VPS_IP:$PROJECT_PATH${NC}"
echo ""

# Ask for confirmation
read -p "Do you want to upload all files to the VPS? (y/N): " confirm
if [[ ! $confirm =~ ^[Yy]$ ]]; then
    echo "Upload cancelled"
    exit 0
fi

# Create remote directory if it doesn't exist
echo -e "${BLUE}📁 Creating remote directory...${NC}"
ssh "$VPS_USER@$VPS_IP" "mkdir -p $PROJECT_PATH"

# Upload Python files
echo -e "${BLUE}🐍 Uploading Python files...${NC}"
scp *.py "$VPS_USER@$VPS_IP:$PROJECT_PATH/"

# Upload configuration files
echo -e "${BLUE}⚙️ Uploading configuration files...${NC}"
scp .env.example "$VPS_USER@$VPS_IP:$PROJECT_PATH/"
scp requirements.txt "$VPS_USER@$VPS_IP:$PROJECT_PATH/"

# Upload documentation
echo -e "${BLUE}📚 Uploading documentation...${NC}"
scp *.md "$VPS_USER@$VPS_IP:$PROJECT_PATH/" 2>/dev/null || true

# Copy .env if it exists (contains real credentials)
if [ -f ".env" ]; then
    echo -e "${BLUE}🔐 Uploading .env file...${NC}"
    scp .env "$VPS_USER@$VPS_IP:$PROJECT_PATH/"
else
    echo -e "${BLUE}📝 Creating .env from template on VPS...${NC}"
    ssh "$VPS_USER@$VPS_IP" "cp $PROJECT_PATH/.env.example $PROJECT_PATH/.env"
fi

# Set correct permissions
echo -e "${BLUE}🔒 Setting file permissions...${NC}"
ssh "$VPS_USER@$VPS_IP" "chown -R trader:trader $PROJECT_PATH && chmod +x $PROJECT_PATH/*.py"

# Display upload summary
echo ""
echo -e "${GREEN}✅ Upload completed successfully!${NC}"
echo ""
echo "📋 Files uploaded to: $VPS_USER@$VPS_IP:$PROJECT_PATH"
echo ""
echo "🔄 Next steps on your VPS:"
echo "1. SSH into VPS: ssh $VPS_USER@$VPS_IP"
echo "2. Switch to trader user: sudo -u trader bash"
echo "3. Configure .env file: nano $PROJECT_PATH/.env"
echo "4. Install MT5 & Python: ~/install-mt5-python.sh"
echo "5. Test the bot: ~/manage-bot.sh start"
echo ""

# Offer to SSH into VPS
read -p "Do you want to SSH into the VPS now? (y/N): " ssh_now
if [[ $ssh_now =~ ^[Yy]$ ]]; then
    echo -e "${BLUE}🔌 Connecting to VPS...${NC}"
    ssh "$VPS_USER@$VPS_IP"
fi