#!/bin/bash

# Fix Dockerfile for Ubuntu 24.04 and upload to VPS
echo "🔧 Creating updated Dockerfile for Ubuntu 24.04..."

# Create updated Dockerfile
cat > Dockerfile << 'EOF'
# Multi-stage Docker build for MT5 Trading Bot with Wine
FROM ubuntu:24.04 as wine-base

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV WINEARCH=win64
ENV WINEPREFIX=/root/.wine
ENV DISPLAY=:99

# Set timezone
RUN ln -snf /usr/share/zoneinfo/UTC /etc/localtime && echo UTC > /etc/timezone

# Install system dependencies
RUN apt-get update && apt-get install -y \
    # Essential tools
    curl \
    wget \
    unzip \
    software-properties-common \
    ca-certificates \
    gnupg \
    # Wine dependencies for Ubuntu 24.04
    wine \
    winetricks \
    # Display system for MT5 GUI
    xvfb \
    x11vnc \
    fluxbox \
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

# Initialize Wine
RUN wine --version && \
    wineboot --init && \
    winetricks -q vcrun2019 && \
    echo "Wine initialized successfully"

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

# Expose VNC port for debugging (optional)
EXPOSE 5900

# Start script
CMD ["/app/docker/start.sh"]
EOF

echo "✅ Updated Dockerfile created for Ubuntu 24.04"
echo "📤 Uploading to VPS..."

# Upload the fixed Dockerfile
scp Dockerfile root@31.97.183.241:/root/telegram-bot/

echo "🎉 Upload completed! Now you can build the container."