#!/bin/bash
# Docker Container Setup Script
# This script runs inside the Docker container during build

set -e

echo "🔧 Setting up MT5 and Python in Wine container..."

# Wine environment
export WINEARCH=win64
export WINEPREFIX=/opt/.wine
export DISPLAY=:99

# Start virtual display
echo "Starting virtual display..."
Xvfb :99 -screen 0 1024x768x24 -ac &
sleep 3

# Install MetaTrader 5
echo "Installing MetaTrader 5..."
if [ -f "/tmp/installers/mt5setup.exe" ]; then
    wine /tmp/installers/mt5setup.exe /S
    echo "MT5 installation completed"
else
    echo "Warning: MT5 installer not found"
fi

# Install Python in Wine
echo "Installing Python in Wine..."
if [ -f "/tmp/installers/python-installer.exe" ]; then
    wine /tmp/installers/python-installer.exe /quiet InstallAllUsers=0 PrependPath=1
    echo "Python installation completed"
else
    echo "Warning: Python installer not found"
fi

# Wait for installations to complete
sleep 30

# Install Python packages in Wine
echo "Installing Python packages in Wine..."
wine python -m pip install --upgrade pip || true
wine python -m pip install MetaTrader5 telethon requests python-dotenv || true

# Cleanup
echo "Cleaning up..."
rm -rf /tmp/installers

# Create necessary directories
mkdir -p /app/logs /app/data

echo "✅ Container setup completed successfully"