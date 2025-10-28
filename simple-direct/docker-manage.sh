#!/bin/bash
# Docker Management Script for MT5 Trading Bot
# Easy commands to manage your Docker-based trading bot

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
CONTAINER_NAME="mt5-trading-bot"
IMAGE_NAME="mt5-trading-bot"
COMPOSE_FILE="docker-compose.yml"

# Function to print colored output
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if Docker is installed
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi

    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
}

# Function to show usage
show_usage() {
    echo "🐳 MT5 Trading Bot - Docker Management"
    echo "====================================="
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  build     - Build the Docker image"
    echo "  start     - Start the trading bot"
    echo "  stop      - Stop the trading bot"
    echo "  restart   - Restart the trading bot"
    echo "  logs      - View bot logs"
    echo "  status    - Check bot status"
    echo "  shell     - Open shell in container"
    echo "  vnc       - Connect via VNC (for debugging)"
    echo "  cleanup   - Remove containers and images"
    echo "  update    - Rebuild and restart bot"
    echo "  backup    - Backup bot data"
    echo "  restore   - Restore bot data"
    echo ""
    echo "Examples:"
    echo "  $0 build         # Build the image"
    echo "  $0 start         # Start the bot"
    echo "  $0 logs -f       # Follow logs in real-time"
    echo "  $0 shell         # Open bash in container"
}

# Function to build Docker image
build_image() {
    print_info "Building Docker image..."
    
    if [ -f "$COMPOSE_FILE" ]; then
        docker-compose build --no-cache
    else
        docker build -t $IMAGE_NAME .
    fi
    
    print_success "Docker image built successfully"
}

# Function to start containers
start_bot() {
    print_info "Starting MT5 Trading Bot..."
    
    # Check if .env file exists
    if [ ! -f ".env" ]; then
        print_warning ".env file not found. Creating from template..."
        if [ -f ".env.example" ]; then
            cp .env.example .env
            print_warning "Please edit .env file with your credentials before starting"
            return 1
        else
            print_error "No .env.example file found"
            return 1
        fi
    fi
    
    if [ -f "$COMPOSE_FILE" ]; then
        docker-compose up -d
    else
        docker run -d \
            --name $CONTAINER_NAME \
            --restart unless-stopped \
            -v $(pwd)/logs:/app/logs \
            -v $(pwd)/.env:/app/.env:ro \
            -p 5900:5900 \
            $IMAGE_NAME
    fi
    
    print_success "Trading bot started"
    print_info "Use '$0 logs' to view logs"
    print_info "Use '$0 status' to check status"
}

# Function to stop containers
stop_bot() {
    print_info "Stopping MT5 Trading Bot..."
    
    if [ -f "$COMPOSE_FILE" ]; then
        docker-compose down
    else
        docker stop $CONTAINER_NAME || true
        docker rm $CONTAINER_NAME || true
    fi
    
    print_success "Trading bot stopped"
}

# Function to restart bot
restart_bot() {
    print_info "Restarting MT5 Trading Bot..."
    stop_bot
    sleep 2
    start_bot
}

# Function to view logs
view_logs() {
    if [ -f "$COMPOSE_FILE" ]; then
        docker-compose logs $@
    else
        docker logs $@ $CONTAINER_NAME
    fi
}

# Function to check status
check_status() {
    print_info "Checking bot status..."
    
    if [ -f "$COMPOSE_FILE" ]; then
        docker-compose ps
        echo ""
        docker-compose exec $CONTAINER_NAME /docker/healthcheck.sh || true
    else
        if docker ps | grep -q $CONTAINER_NAME; then
            print_success "Container is running"
            docker exec $CONTAINER_NAME /docker/healthcheck.sh || true
        else
            print_warning "Container is not running"
        fi
    fi
    
    echo ""
    print_info "Recent logs:"
    view_logs --tail 10
}

# Function to open shell in container
open_shell() {
    print_info "Opening shell in container..."
    
    if [ -f "$COMPOSE_FILE" ]; then
        docker-compose exec $CONTAINER_NAME /bin/bash
    else
        docker exec -it $CONTAINER_NAME /bin/bash
    fi
}

# Function to connect via VNC
connect_vnc() {
    print_info "VNC connection information:"
    echo "Host: localhost"
    echo "Port: 5900"
    echo "Password: (none)"
    echo ""
    print_info "Make sure to start the bot with VNC enabled:"
    print_info "docker-compose exec $CONTAINER_NAME bash -c 'ENABLE_VNC=true /docker/start.sh'"
}

# Function to cleanup
cleanup() {
    print_warning "This will remove all containers and images. Are you sure? (y/N)"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        print_info "Cleaning up..."
        
        if [ -f "$COMPOSE_FILE" ]; then
            docker-compose down -v --rmi all
        else
            docker stop $CONTAINER_NAME || true
            docker rm $CONTAINER_NAME || true
            docker rmi $IMAGE_NAME || true
        fi
        
        print_success "Cleanup completed"
    else
        print_info "Cleanup cancelled"
    fi
}

# Function to update bot
update_bot() {
    print_info "Updating trading bot..."
    stop_bot
    build_image
    start_bot
    print_success "Bot updated successfully"
}

# Function to backup data
backup_data() {
    print_info "Creating backup..."
    BACKUP_DIR="backups"
    BACKUP_FILE="mt5-bot-backup-$(date +%Y%m%d-%H%M%S).tar.gz"
    
    mkdir -p $BACKUP_DIR
    
    tar -czf "$BACKUP_DIR/$BACKUP_FILE" \
        --exclude='backups' \
        --exclude='.git' \
        --exclude='__pycache__' \
        .
    
    print_success "Backup created: $BACKUP_DIR/$BACKUP_FILE"
}

# Function to restore data
restore_data() {
    print_info "Available backups:"
    ls -la backups/*.tar.gz 2>/dev/null || {
        print_error "No backups found"
        return 1
    }
    
    echo ""
    print_warning "Enter backup filename to restore:"
    read -r backup_file
    
    if [ -f "backups/$backup_file" ]; then
        print_warning "This will overwrite current files. Continue? (y/N)"
        read -r response
        if [[ "$response" =~ ^[Yy]$ ]]; then
            tar -xzf "backups/$backup_file"
            print_success "Backup restored: $backup_file"
        fi
    else
        print_error "Backup file not found: $backup_file"
    fi
}

# Main script logic
case "${1:-}" in
    build)
        check_docker
        build_image
        ;;
    start)
        check_docker
        start_bot
        ;;
    stop)
        check_docker
        stop_bot
        ;;
    restart)
        check_docker
        restart_bot
        ;;
    logs)
        check_docker
        shift
        view_logs $@
        ;;
    status)
        check_docker
        check_status
        ;;
    shell)
        check_docker
        open_shell
        ;;
    vnc)
        connect_vnc
        ;;
    cleanup)
        check_docker
        cleanup
        ;;
    update)
        check_docker
        update_bot
        ;;
    backup)
        backup_data
        ;;
    restore)
        restore_data
        ;;
    help|--help|-h)
        show_usage
        ;;
    "")
        show_usage
        ;;
    *)
        print_error "Unknown command: $1"
        echo ""
        show_usage
        exit 1
        ;;
esac