#!/bin/bash

# Simple deployment script for Hostinger VPS
# Run this script on your Hostinger VPS

echo "🚀 Deploying Telegram Monitor to Hostinger VPS"

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Please install Docker first:"
    echo "curl -fsSL https://get.docker.com -o get-docker.sh && sh get-docker.sh"
    exit 1
fi

# Create app directory
APP_DIR="/home/telegram-monitor"
sudo mkdir -p $APP_DIR
cd $APP_DIR

echo "📁 Created application directory: $APP_DIR"

# Stop existing container if running
if docker ps -q --filter "name=telegram-monitor" | grep -q .; then
    echo "🛑 Stopping existing container..."
    docker stop telegram-monitor
    docker rm telegram-monitor
fi

# Build the Docker image
echo "🔨 Building Docker image..."
docker build -t telegram-monitor .

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found. Creating from template..."
    cp .env.example .env
    echo "📝 Please edit .env file with your credentials:"
    echo "   nano .env"
    echo ""
    echo "Then run this script again."
    exit 1
fi

# Run the container
echo "🐳 Starting Telegram Monitor container..."
docker run -d \
    --name telegram-monitor \
    --restart unless-stopped \
    -p 8000:8000 \
    -v $(pwd)/.env:/app/.env \
    -v $(pwd)/logs:/app/logs \
    telegram-monitor

# Check if container is running
if docker ps -q --filter "name=telegram-monitor" | grep -q .; then
    echo "✅ Telegram Monitor deployed successfully!"
    echo "📊 Health check: http://your-vps-ip:8000/health"
    echo "📋 View logs: docker logs telegram-monitor"
    echo "🔍 Monitor status: docker ps"
else
    echo "❌ Deployment failed. Check logs:"
    echo "docker logs telegram-monitor"
fi