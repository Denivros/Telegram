#!/bin/bash
# Container startup script
# This script runs when the container starts

set -e

echo "🚀 Starting MT5 Trading Bot Container..."

# Wine environment
export WINEARCH=win64
export WINEPREFIX=/opt/.wine
export DISPLAY=:99

# Function to cleanup on exit
cleanup() {
    echo "🛑 Shutting down trading bot..."
    pkill -f "direct_mt5_monitor.py" 2>/dev/null || true
    pkill -f "Xvfb" 2>/dev/null || true
    pkill -f "fluxbox" 2>/dev/null || true
    exit 0
}

# Setup signal handlers
trap cleanup SIGTERM SIGINT

# Start virtual display
echo "📺 Starting virtual display..."
Xvfb :99 -screen 0 1024x768x24 -ac &
XVFB_PID=$!
sleep 2

# Start window manager
fluxbox &
FLUXBOX_PID=$!
sleep 1

# Optional: Start VNC server for debugging
if [ "$ENABLE_VNC" = "true" ]; then
    echo "🖥️ Starting VNC server on :5900..."
    x11vnc -display :99 -rfbport 5900 -forever -shared -bg
fi

# Check if .env file exists
if [ ! -f "/app/.env" ]; then
    echo "❌ .env file not found!"
    echo "Please make sure your .env file is mounted or copied to the container"
    exit 1
fi

# Validate MT5 installation
if [ ! -d "/opt/.wine/drive_c/Program Files/MetaTrader 5" ]; then
    echo "⚠️ MT5 not found, attempting to install..."
    if [ -f "/tmp/installers/mt5setup.exe" ]; then
        wine /tmp/installers/mt5setup.exe /S
        sleep 30
    else
        echo "❌ MT5 installer not available"
    fi
fi

# Test Wine Python
echo "🐍 Testing Wine Python installation..."
if wine python --version; then
    echo "✅ Wine Python is working"
else
    echo "❌ Wine Python not working properly"
    exit 1
fi

# Test MetaTrader5 library
echo "📊 Testing MetaTrader5 library..."
if wine python -c "import MetaTrader5; print('MT5 library:', MetaTrader5.__version__)"; then
    echo "✅ MetaTrader5 library is working"
else
    echo "❌ MetaTrader5 library not working"
    exit 1
fi

# Create log directory if it doesn't exist
mkdir -p /app/logs

# Start the trading bot
echo "🤖 Starting MT5 Trading Bot..."
cd /app

# Run with Wine Python
wine python direct_mt5_monitor.py &
BOT_PID=$!

echo "✅ Trading bot started with PID: $BOT_PID"
echo "📊 Container is running..."

# Monitor the bot process
while kill -0 $BOT_PID 2>/dev/null; do
    sleep 30
    
    # Optional: Add health checks here
    if [ -f "/app/logs/direct_mt5_monitor.log" ]; then
        # Check if there are recent log entries (less than 5 minutes old)
        if [ $(find /app/logs/direct_mt5_monitor.log -mmin -5 | wc -l) -eq 0 ]; then
            echo "⚠️ No recent log activity detected"
        fi
    fi
done

echo "❌ Trading bot process ended unexpectedly"
cleanup