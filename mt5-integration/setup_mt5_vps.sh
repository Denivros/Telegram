#!/bin/bash
# MT5 API Server Setup Script for VPS

echo "=== MT5 API Server Setup ==="

# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3 and pip if not already installed
sudo apt install python3 python3-pip python3-venv -y

# Create project directory
mkdir -p ~/mt5-api-server
cd ~/mt5-api-server

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install requirements
pip install Flask==2.3.3 MetaTrader5==5.0.45 requests==2.31.0

echo "=== Installation Complete ==="
echo ""
echo "Next steps:"
echo "1. Copy mt5_api_server.py to ~/mt5-api-server/"
echo "2. Update MT5 credentials in the script"
echo "3. Run: python mt5_api_server.py"
echo ""
echo "Test with: curl http://localhost:8080/health"