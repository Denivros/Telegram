# Multi-stage Docker build for MT5 Trading Bot
FROM ubuntu:22.04 as base

# Prevent interactive prompts during installation
ENV DEBIAN_FRONTEND=noninteractive

# Set timezone
ENV TZ=UTC
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Install system dependencies
RUN apt-get update && apt-get install -y \
    # Essential tools
    curl \
    wget \
    unzip \
    software-properties-common \
    ca-certificates \
    gnupg \
    # Wine dependencies
    wine \
    wine32 \
    wine64 \
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

# Configure Wine
ENV WINEARCH=win64
ENV WINEPREFIX=/opt/.wine
ENV DISPLAY=:99

# Create wine prefix and configure
RUN mkdir -p /opt/.wine \
    && wineboot --init \
    && winetricks -q corefonts vcrun2019 vcrun2015 msvcrt

# Create application directory
WORKDIR /app

# Create non-root user for security
RUN groupadd -r trader && useradd -r -g trader trader \
    && chown -R trader:trader /app \
    && chown -R trader:trader /opt/.wine

# Copy requirements first (for better Docker layer caching)
COPY requirements.txt .

# Install Python dependencies (native Linux)
RUN pip3 install --no-cache-dir -r requirements.txt

# Download installers
RUN mkdir -p /tmp/installers \
    && wget -O /tmp/installers/mt5setup.exe \
       "https://download.mql5.com/cdn/web/metaquotes.software.corp/mt5/mt5setup.exe" \
    && wget -O /tmp/installers/python-installer.exe \
       "https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe"

# Copy Docker setup scripts
COPY docker/ /docker/
RUN chmod +x /docker/*.sh

# Copy application files
COPY . .

# Install MT5 and Python in Wine (as trader user)
USER trader
RUN /docker/setup.sh

# Create volume mount points
USER root
RUN mkdir -p /app/logs /app/data /app/config \
    && chown -R trader:trader /app/logs /app/data /app/config

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD /docker/healthcheck.sh

# Expose VNC port for debugging (optional)
EXPOSE 5900

# Switch back to trader user
USER trader

# Set working directory
WORKDIR /app

# Start command
CMD ["/docker/start.sh"]