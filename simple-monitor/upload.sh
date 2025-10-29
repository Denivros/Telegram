#!/bin/bash

# Upload script for Hostinger VPS deployment
# This script helps you upload the simplified monitor to your VPS

echo "📦 Preparing Telegram Monitor for Hostinger Upload"

# Configuration (edit these values)
VPS_IP="your-vps-ip"
VPS_USER="your-username" 
VPS_PORT="22"

echo "⚙️  Configuration:"
echo "   VPS IP: $VPS_IP"
echo "   VPS User: $VPS_USER"
echo "   VPS Port: $VPS_PORT"
echo ""

# Check if we're in the right directory
if [ ! -f "telegram_monitor.py" ]; then
    echo "❌ Error: Run this script from the simple-monitor directory"
    echo "Current directory: $(pwd)"
    exit 1
fi

# Create archive
echo "📁 Creating deployment archive..."
cd ..
tar -czf telegram-monitor-deploy.tar.gz simple-monitor/
echo "✅ Created telegram-monitor-deploy.tar.gz"

# Upload to VPS
echo "🚀 Uploading to Hostinger VPS..."
echo "Note: You'll need to enter your VPS password"

scp -P $VPS_PORT telegram-monitor-deploy.tar.gz $VPS_USER@$VPS_IP:/home/

if [ $? -eq 0 ]; then
    echo "✅ Upload successful!"
    echo ""
    echo "🔗 Now SSH into your VPS and run:"
    echo "   ssh -p $VPS_PORT $VPS_USER@$VPS_IP"
    echo ""
    echo "📋 Then on the VPS, run:"
    echo "   cd /home"
    echo "   tar -xzf telegram-monitor-deploy.tar.gz"
    echo "   cd simple-monitor"
    echo "   chmod +x deploy.sh"
    echo "   ./deploy.sh"
    echo ""
    echo "📝 Don't forget to:"
    echo "   1. Edit the .env file with your Telegram credentials"
    echo "   2. Run ./deploy.sh again after configuring .env"
else
    echo "❌ Upload failed. Please check:"
    echo "   1. VPS IP address is correct"
    echo "   2. Username is correct"
    echo "   3. SSH access is working"
    echo "   4. Network connection"
fi

# Clean up
rm telegram-monitor-deploy.tar.gz
echo "🧹 Cleaned up local archive"