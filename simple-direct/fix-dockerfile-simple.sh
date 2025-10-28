#!/bin/bash

# Create simplified Dockerfile without Wine for remote MT5 connection
echo "🔧 Creating simplified Dockerfile for remote MT5..."

cat > Dockerfile << 'EOF'
# Simplified Docker build for remote MT5 Trading Bot
FROM ubuntu:24.04

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

# Set timezone
RUN ln -snf /usr/share/zoneinfo/UTC /etc/localtime && echo UTC > /etc/timezone

# Install system dependencies
RUN apt-get update && apt-get install -y \
    # Essential tools
    curl \
    wget \
    # Python and development tools
    python3 \
    python3-pip \
    python3-venv \
    # Monitoring tools
    htop \
    procps \
    # Network tools
    netcat-openbsd \
    iputils-ping \
    # Cleanup
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Set up Python virtual environment
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Create working directory
WORKDIR /app

# Copy application files
COPY direct_mt5_monitor.py /app/
COPY .env /app/
COPY docker/ /app/docker/

# Make scripts executable
RUN chmod +x /app/docker/*.sh

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD /app/docker/healthcheck.sh

# Start script
CMD ["/app/docker/start.sh"]
EOF

echo "✅ Simplified Dockerfile created (remote MT5 connection)"
echo "📤 Uploading to VPS..."

# Upload the simplified Dockerfile
scp Dockerfile root@31.97.183.241:/root/telegram-bot/

echo "🎉 Upload completed! This version will work with remote MT5 connection."