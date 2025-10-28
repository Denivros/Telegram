#!/bin/bash
# Docker Health Check Script - Simplified for Remote MT5

# Check if trading bot process is running
if ! pgrep -f "direct_mt5_monitor.py" > /dev/null; then
    echo "❌ Trading bot process not running"
    exit 1
fi

# Check if health endpoint is responding
if command -v curl > /dev/null; then
    if ! curl -f http://localhost:8000/health > /dev/null 2>&1; then
        echo "❌ Health endpoint not responding"
        exit 1
    fi
fi

# Check if log file exists and is being updated (within last 10 minutes)
if [ -f "/app/logs/direct_mt5_monitor.log" ]; then
    if [ $(find /app/logs/direct_mt5_monitor.log -mmin -10 | wc -l) -eq 0 ]; then
        echo "⚠️ Log file not updated recently"
        exit 1
    fi
else
    # If no log file exists yet, check if container just started
    if [ $(cat /proc/uptime | cut -d. -f1) -gt 300 ]; then  # 5 minutes
        echo "❌ No log file after 5 minutes"
        exit 1
    fi
fi

# Check network connectivity
if ! ping -c 1 8.8.8.8 > /dev/null 2>&1; then
    echo "❌ No network connectivity"
    exit 1
fi

# All checks passed
echo "✅ Container is healthy"
exit 0