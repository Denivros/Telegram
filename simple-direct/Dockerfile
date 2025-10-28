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

# Install Python dependencies
COPY requirements.txt /tmp/requirements.txt
RUN python3 -m pip install --no-cache-dir -r /tmp/requirements.txt

# Create working directory
WORKDIR /app

# Copy application files
COPY direct_mt5_monitor.py /app/
COPY docker/ /app/docker/

# Create .env file from environment variables at runtime
RUN echo '#!/bin/bash\necho "Creating .env from environment variables..."\ncat > /app/.env << EOF\nTELEGRAM_API_ID=${TELEGRAM_API_ID}\nTELEGRAM_API_HASH=${TELEGRAM_API_HASH}\nTELEGRAM_PHONE=${TELEGRAM_PHONE}\nTELEGRAM_GROUP_ID=${TELEGRAM_GROUP_ID}\nSESSION_NAME=${SESSION_NAME}\nMT5_LOGIN=${MT5_LOGIN}\nMT5_PASSWORD=${MT5_PASSWORD}\nMT5_SERVER=${MT5_SERVER}\nDEFAULT_VOLUME=${DEFAULT_VOLUME}\nENTRY_STRATEGY=${ENTRY_STRATEGY}\nMAGIC_NUMBER=${MAGIC_NUMBER}\nN8N_LOG_WEBHOOK=${N8N_LOG_WEBHOOK}\nEOF' > /app/create_env.sh && chmod +x /app/create_env.sh

# Make scripts executable
RUN chmod +x /app/docker/*.sh

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD /app/docker/healthcheck.sh

# Start script
CMD ["/app/docker/start.sh"]
