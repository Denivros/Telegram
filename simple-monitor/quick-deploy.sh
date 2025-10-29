#!/bin/bash

# Quick deployment script for just telegram_monitor.py to Hostinger VPS
# Edit these variables with your VPS details:

VPS_IP="31.97.183.241"
VPS_USER="root"
VPS_PORT="22"

echo "🚀 Quick Telegram Monitor Deployment to Hostinger"
echo "================================================="

# Check if we have the required files
if [ ! -f "telegram_monitor.py" ]; then
    echo "❌ Error: telegram_monitor.py not found"
    exit 1
fi

if [ ! -f "requirements.txt" ]; then
    echo "❌ Error: requirements.txt not found"
    exit 1
fi

echo "✅ Found required files"
echo "📡 VPS: $VPS_USER@$VPS_IP:$VPS_PORT"
echo ""

# Create a simple setup script for the VPS
cat > vps-setup.sh << 'EOF'
#!/bin/bash
echo "🔧 Setting up Telegram Monitor on VPS..."

# Create directory
mkdir -p ~/telegram-monitor
cd ~/telegram-monitor

# Install Python if needed
if ! command -v python3 &> /dev/null; then
    echo "📦 Installing Python..."
    sudo apt update
    sudo apt install -y python3 python3-pip
fi

# Install dependencies
echo "📦 Installing Python packages..."
pip3 install --user telethon requests python-dotenv

echo "✅ Setup complete!"
echo ""
echo "📋 Your .env file is already configured!"
echo ""
echo "🚀 Ready to run:"
echo "   python3 telegram_monitor.py"
echo ""
echo "🔄 Or run in background:"
echo "   nohup python3 telegram_monitor.py > monitor.log 2>&1 &"
echo ""
echo "📊 Check if running:"
echo "   ps aux | grep telegram_monitor"
echo ""
echo "📜 View logs:"
echo "   tail -f monitor.log"
EOF

# Upload files
echo "📤 Uploading files to VPS..."

# Upload main files
scp -P $VPS_PORT telegram_monitor.py $VPS_USER@$VPS_IP:~/telegram-monitor/
scp -P $VPS_PORT requirements.txt $VPS_USER@$VPS_IP:~/telegram-monitor/
scp -P $VPS_PORT .env $VPS_USER@$VPS_IP:~/telegram-monitor/
scp -P $VPS_PORT vps-setup.sh $VPS_USER@$VPS_IP:~/telegram-monitor/

if [ $? -eq 0 ]; then
    echo "✅ Files uploaded successfully!"
    echo ""
    echo "🔗 Now SSH into your VPS:"
    echo "   ssh -p $VPS_PORT $VPS_USER@$VPS_IP"
    echo ""
    echo "📋 Then run on your VPS:"
    echo "   cd ~/telegram-monitor"
    echo "   chmod +x vps-setup.sh"
    echo "   ./vps-setup.sh"
    echo ""
    echo "🎯 That's it! Simple deployment complete."
else
    echo "❌ Upload failed. Please check your VPS details and try again."
fi

# Clean up
rm vps-setup.sh