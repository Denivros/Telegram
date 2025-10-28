#!/bin/bash
# Container startup script - Simplified for Remote MT5 Connection
set -e

echo "🚀 Starting MT5 Trading Bot Container (Remote Connection)..."

# Function to cleanup on exit
cleanup() {
    echo "🛑 Shutting down trading bot..."
    pkill -f "direct_mt5_monitor.py" 2>/dev/null || true
    exit 0
}

# Setup signal handlers
trap cleanup SIGTERM SIGINT

# Create .env file from environment variables
echo "� Creating .env file from environment variables..."
cat > /app/.env << EOF
TELEGRAM_API_ID=${TELEGRAM_API_ID}
TELEGRAM_API_HASH=${TELEGRAM_API_HASH}
TELEGRAM_PHONE=${TELEGRAM_PHONE}
TELEGRAM_GROUP_ID=${TELEGRAM_GROUP_ID}
SESSION_NAME=${SESSION_NAME}
MT5_LOGIN=${MT5_LOGIN}
MT5_PASSWORD=${MT5_PASSWORD}
MT5_SERVER=${MT5_SERVER}
DEFAULT_VOLUME=${DEFAULT_VOLUME}
ENTRY_STRATEGY=${ENTRY_STRATEGY}
MAGIC_NUMBER=${MAGIC_NUMBER}
N8N_LOG_WEBHOOK=${N8N_LOG_WEBHOOK}
EOF

echo "✅ Environment file created"

# Test Python installation
echo "🐍 Testing Python installation..."
if python3 --version; then
    echo "✅ Python is working"
else
    echo "❌ Python not working properly"
    exit 1
fi

# Test MetaTrader5 library
echo "📊 Testing MetaTrader5 library..."
if python3 -c "import MetaTrader5; print('MT5 library version:', MetaTrader5.__version__)"; then
    echo "✅ MetaTrader5 library is working"
else
    echo "❌ MetaTrader5 library not working - installing..."
    pip install MetaTrader5
fi

# Create log directory if it doesn't exist
mkdir -p /app/logs

# Start the trading bot
echo "🤖 Starting MT5 Trading Bot (Remote Connection)..."
cd /app

# Run with native Python
python3 direct_mt5_monitor.py &
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