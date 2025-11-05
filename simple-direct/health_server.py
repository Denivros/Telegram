"""
Health Server Module
Contains HTTP server classes for bot health monitoring and status checks.
"""

import json
import logging
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime
from config import *

logger = logging.getLogger(__name__)

# Import MT5 for health checks
try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
except ImportError:
    MT5_AVAILABLE = False
    logger.warning("MetaTrader5 not available for health checks")


class BotHealthHandler(BaseHTTPRequestHandler):
    """Simple HTTP handler for bot health checks"""
    
    def __init__(self, request, client_address, server, bot_instance=None):
        self.bot_instance = bot_instance
        super().__init__(request, client_address, server)
    
    def do_GET(self):
        """Handle GET requests"""
        if self.path == '/health' or self.path == '/status':
            self.send_health_response()
        elif self.path == '/':
            self.send_simple_response()
        else:
            self.send_error(404, "Not Found")
    
    def send_health_response(self):
        """Send detailed bot health status"""
        try:
            # Get current time
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Check MT5 connection
            mt5_connected = mt5.terminal_info() is not None if MT5_AVAILABLE else False
            
            # Get positions and orders count
            positions_count = len(mt5.positions_get()) if MT5_AVAILABLE and mt5_connected else 0
            orders_count = len(mt5.orders_get()) if MT5_AVAILABLE and mt5_connected else 0
            
            # Get account info
            account_info = mt5.account_info() if MT5_AVAILABLE and mt5_connected else None
            balance = f"{account_info.balance:.2f}" if account_info else "N/A"
            equity = f"{account_info.equity:.2f}" if account_info else "N/A"
            
            # Bot status
            bot_running = hasattr(self.bot_instance, 'running') and self.bot_instance.running if self.bot_instance else True
            
            # Build JSON response
            health_data = {
                "status": "healthy" if bot_running and (not MT5_AVAILABLE or mt5_connected) else "unhealthy",
                "timestamp": current_time,
                "bot_running": bot_running,
                "mt5_available": MT5_AVAILABLE,
                "mt5_connected": mt5_connected,
                "account": {
                    "balance": balance,
                    "equity": equity
                },
                "trades": {
                    "open_positions": positions_count,
                    "pending_orders": orders_count
                },
                "config": {
                    "strategy": ENTRY_STRATEGY,
                    "volume": DEFAULT_VOLUME
                }
            }
            
            response = json.dumps(health_data, indent=2)
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Content-length', str(len(response)))
            self.end_headers()
            self.wfile.write(response.encode())
            
        except Exception as e:
            error_response = json.dumps({
                "status": "error", 
                "message": str(e),
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('Content-length', str(len(error_response)))
            self.end_headers()
            self.wfile.write(error_response.encode())
    
    def send_simple_response(self):
        """Send simple 'Bot is running' response"""
        response = json.dumps({
            "message": "MT5 Trading Bot is running",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "status": "online"
        })
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Content-length', str(len(response)))
        self.end_headers()
        self.wfile.write(response.encode())
    
    def log_message(self, format, *args):
        """Override to suppress HTTP server logs"""
        pass


class BotHealthServer:
    """HTTP server for bot health checks"""
    
    def __init__(self, port=8080, bot_instance=None):
        self.port = port
        self.bot_instance = bot_instance
        self.server = None
        self.thread = None
    
    def start(self):
        """Start the HTTP server in a separate thread"""
        try:
            # Create custom handler class with bot instance
            def handler(*args):
                BotHealthHandler(*args, bot_instance=self.bot_instance)
            
            self.server = HTTPServer(('0.0.0.0', self.port), handler)
            self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
            self.thread.start()
            
            logger.info(f"🌐 Health check server started on port {self.port}")
            logger.info(f"   GET http://localhost:{self.port}/health - Detailed status")
            logger.info(f"   GET http://localhost:{self.port}/ - Simple status")
            
        except Exception as e:
            logger.error(f"Failed to start health server: {e}")
    
    def stop(self):
        """Stop the HTTP server"""
        if self.server:
            self.server.shutdown()
            self.server.server_close()
            logger.info("🌐 Health check server stopped")