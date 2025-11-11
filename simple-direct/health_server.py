"""
Health Server Module
Contains HTTP server classes for bot health monitoring and status checks.
"""

import json
import logging
import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime
from urllib.parse import parse_qs, urlparse
from config import *

logger = logging.getLogger(__name__)

# Import OVH for VPS management
try:
    import ovh
    OVH_AVAILABLE = True
except ImportError:
    OVH_AVAILABLE = False
    ovh = None
    logger.warning("OVH library not available - restart functionality disabled")

# Import MT5 for health checks
try:
    import metatrader5 as mt5
    MT5_AVAILABLE = True
except ImportError:
    MT5_AVAILABLE = False
    mt5 = None
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
        elif self.path == '/alive':
            self.send_alive_response()
        elif self.path == '/restart':
            self.send_restart_response()
        elif self.path.startswith('/log'):
            # Parse query parameters for line count and format
            lines = 40  # default
            format_type = 'json'  # default
            if '?' in self.path:
                parsed_url = urlparse(self.path)
                query_params = parse_qs(parsed_url.query)
                if 'lines' in query_params:
                    try:
                        lines = int(query_params['lines'][0])
                        lines = min(max(lines, 1), 1000)  # Limit between 1 and 1000 lines
                    except (ValueError, IndexError):
                        lines = 40
                if 'format' in query_params:
                    format_type = query_params['format'][0].lower()
                    if format_type not in ['json', 'html']:
                        format_type = 'json'
            
            if format_type == 'html':
                self.send_log_html(lines)
            else:
                self.send_log_response(lines)
        elif self.path == '/':
            self.send_simple_response()
        else:
            self.send_error(404, "Not Found")
    
    def do_POST(self):
        """Handle POST requests"""
        if self.path == '/restart':
            self.send_restart_response()
        elif self.path == '/totalcancel':
            self.send_totalcancel_response()
        elif self.path == '/closeall':
            self.send_closeall_response()
        elif self.path == '/be':
            self.send_be_response()
        elif self.path == '/cancelorders':
            self.send_cancelorders_response()
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
    
    def send_alive_response(self):
        """Send simple alive status - lightweight check"""
        try:
            # Just check if bot is running (minimal overhead)
            bot_running = hasattr(self.bot_instance, 'running') and self.bot_instance.running if self.bot_instance else True
            
            # Simple alive response
            alive_data = {
                "alive": bot_running,
                "status": "running" if bot_running else "stopped",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            response = json.dumps(alive_data)
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Content-length', str(len(response)))
            self.end_headers()
            self.wfile.write(response.encode())
            
        except Exception as e:
            error_response = json.dumps({
                "alive": False,
                "status": "error", 
                "message": str(e),
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('Content-length', str(len(error_response)))
            self.end_headers()
            self.wfile.write(error_response.encode())
    
    def send_restart_response(self):
        """Restart VPS using OVH API"""
        try:
            if not OVH_AVAILABLE:
                error_response = json.dumps({
                    "status": "error",
                    "message": "OVH library not available. Install with: pip install ovh",
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
                
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.send_header('Content-length', str(len(error_response)))
                self.end_headers()
                self.wfile.write(error_response.encode())
                return
            
            # Check if OVH credentials are configured (imported from config.py)
            from config import OVH_ENDPOINT, OVH_APPLICATION_KEY, OVH_APPLICATION_SECRET, OVH_CONSUMER_KEY, OVH_SERVICE_NAME
            
            if not all([OVH_APPLICATION_KEY, OVH_APPLICATION_SECRET, OVH_CONSUMER_KEY, OVH_SERVICE_NAME]):
                error_response = json.dumps({
                    "status": "error",
                    "message": "OVH credentials not configured. Set OVH_APPLICATION_KEY, OVH_APPLICATION_SECRET, OVH_CONSUMER_KEY, OVH_SERVICE_NAME environment variables",
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
                
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.send_header('Content-length', str(len(error_response)))
                self.end_headers()
                self.wfile.write(error_response.encode())
                return
            
            # Initialize OVH client
            client = ovh.Client(
                endpoint=OVH_ENDPOINT,
                application_key=OVH_APPLICATION_KEY,
                application_secret=OVH_APPLICATION_SECRET,
                consumer_key=OVH_CONSUMER_KEY,
            )
            
            # Get user info for verification
            try:
                user_info = client.get('/me')
                logger.info(f"OVH API connected for user: {user_info.get('firstname', 'Unknown')}")
            except Exception as e:
                logger.error(f"OVH API authentication failed: {e}")
                raise Exception(f"OVH authentication failed: {str(e)}")
            
            # Reboot VPS
            logger.info(f"Initiating VPS reboot for service: {OVH_SERVICE_NAME}")
            reboot_result = client.post(f'/vps/{OVH_SERVICE_NAME}/reboot')
            
            success_response = json.dumps({
                "status": "success",
                "message": f"VPS reboot initiated successfully for {OVH_SERVICE_NAME}",
                "ovh_result": reboot_result,
                "user": user_info.get('firstname', 'Unknown'),
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "warning": "Bot will stop responding in ~30 seconds as VPS reboots"
            })
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Content-length', str(len(success_response)))
            self.end_headers()
            self.wfile.write(success_response.encode())
            
            logger.info(f"✅ VPS reboot initiated via OVH API")
            
        except Exception as e:
            logger.error(f"Failed to restart VPS: {e}")
            
            error_response = json.dumps({
                "status": "error",
                "message": f"Failed to restart VPS: {str(e)}",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('Content-length', str(len(error_response)))
            self.end_headers()
            self.wfile.write(error_response.encode())
    
    def send_totalcancel_response(self):
        """Close all positions and cancel all pending orders"""
        try:
            if not self.bot_instance:
                error_response = json.dumps({
                    "status": "error",
                    "message": "Bot instance not available",
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
                
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.send_header('Content-length', str(len(error_response)))
                self.end_headers()
                self.wfile.write(error_response.encode())
                return
            
            logger.info("🚫 TOTAL CANCEL requested via API endpoint")
            
            # Close all remaining positions
            logger.info("🔴 Closing all open positions...")
            self.bot_instance.close_remaining_positions()
            
            # Cancel all pending orders  
            logger.info("🚫 Cancelling all pending orders...")
            cancel_result = self.bot_instance.cancel_all_pending_orders()
            
            # Prepare success response
            success_response = json.dumps({
                "status": "success",
                "message": "All positions closed and orders cancelled successfully",
                "actions_performed": [
                    "Closed all open positions",
                    "Cancelled all pending orders"
                ],
                "cancelled_orders": cancel_result.get('cancelled_count', 0),
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Content-length', str(len(success_response)))
            self.end_headers()
            self.wfile.write(success_response.encode())
            
            logger.info(f"✅ Total cancel completed successfully via API")
            
        except Exception as e:
            logger.error(f"Failed to execute total cancel: {e}")
            
            error_response = json.dumps({
                "status": "error",
                "message": f"Failed to execute total cancel: {str(e)}",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('Content-length', str(len(error_response)))
            self.end_headers()
            self.wfile.write(error_response.encode())
    
    def send_closeall_response(self):
        """Close all open positions"""
        try:
            if not self.bot_instance:
                error_response = json.dumps({
                    "status": "error",
                    "message": "Bot instance not available",
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
                
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.send_header('Content-length', str(len(error_response)))
                self.end_headers()
                self.wfile.write(error_response.encode())
                return
            
            logger.info("🔴 CLOSE ALL POSITIONS requested via API endpoint")
            
            # Close all remaining positions
            self.bot_instance.close_remaining_positions()
            
            # Prepare success response
            success_response = json.dumps({
                "status": "success",
                "message": "All open positions closed successfully",
                "action_performed": "Closed all open positions",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Content-length', str(len(success_response)))
            self.end_headers()
            self.wfile.write(success_response.encode())
            
            logger.info(f"✅ Close all positions completed successfully via API")
            
        except Exception as e:
            logger.error(f"Failed to close all positions: {e}")
            
            error_response = json.dumps({
                "status": "error",
                "message": f"Failed to close all positions: {str(e)}",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('Content-length', str(len(error_response)))
            self.end_headers()
            self.wfile.write(error_response.encode())
    
    def send_be_response(self):
        """Move all positions to break even and cancel pending orders"""
        try:
            if not self.bot_instance:
                error_response = json.dumps({
                    "status": "error",
                    "message": "Bot instance not available",
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
                
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.send_header('Content-length', str(len(error_response)))
                self.end_headers()
                self.wfile.write(error_response.encode())
                return
            
            logger.info("🎯 BREAK EVEN requested via API endpoint")
            
            # Move SL to break even (this also cancels pending orders automatically)
            self.bot_instance.move_sl_to_break_even()
            
            # Prepare success response
            success_response = json.dumps({
                "status": "success",
                "message": "All positions moved to break even and pending orders cancelled",
                "actions_performed": [
                    "Moved all stop losses to break even (entry price)",
                    "Cancelled all pending orders"
                ],
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Content-length', str(len(success_response)))
            self.end_headers()
            self.wfile.write(success_response.encode())
            
            logger.info(f"✅ Break even completed successfully via API")
            
        except Exception as e:
            logger.error(f"Failed to move to break even: {e}")
            
            error_response = json.dumps({
                "status": "error",
                "message": f"Failed to move to break even: {str(e)}",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('Content-length', str(len(error_response)))
            self.end_headers()
            self.wfile.write(error_response.encode())
    
    def send_cancelorders_response(self):
        """Cancel all pending orders"""
        try:
            if not self.bot_instance:
                error_response = json.dumps({
                    "status": "error",
                    "message": "Bot instance not available",
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
                
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.send_header('Content-length', str(len(error_response)))
                self.end_headers()
                self.wfile.write(error_response.encode())
                return
            
            logger.info("🚫 CANCEL ORDERS requested via API endpoint")
            
            # Cancel all pending orders
            cancel_result = self.bot_instance.cancel_all_pending_orders()
            
            # Prepare success response
            success_response = json.dumps({
                "status": "success",
                "message": "All pending orders cancelled successfully",
                "action_performed": "Cancelled all pending orders",
                "cancelled_orders": cancel_result.get('cancelled_count', 0),
                "failed_orders": cancel_result.get('failed_count', 0),
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Content-length', str(len(success_response)))
            self.end_headers()
            self.wfile.write(success_response.encode())
            
            logger.info(f"✅ Cancel orders completed successfully via API")
            
        except Exception as e:
            logger.error(f"Failed to cancel orders: {e}")
            
            error_response = json.dumps({
                "status": "error",
                "message": f"Failed to cancel orders: {str(e)}",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('Content-length', str(len(error_response)))
            self.end_headers()
            self.wfile.write(error_response.encode())
    
    def send_log_response(self, lines=40):
        """Send last N lines from log file"""
        try:
            log_file = 'direct_mt5_monitor.log'
            
            # Check if log file exists
            if not os.path.exists(log_file):
                error_response = json.dumps({
                    "status": "error",
                    "message": "Log file not found",
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
                
                self.send_response(404)
                self.send_header('Content-type', 'application/json')
                self.send_header('Content-length', str(len(error_response)))
                self.end_headers()
                self.wfile.write(error_response.encode())
                return
            
            # Read the last N lines from the log file
            with open(log_file, 'r', encoding='utf-8') as f:
                all_lines = f.readlines()
                last_lines = all_lines[-lines:] if len(all_lines) >= lines else all_lines
            
            # Create JSON response with log data
            log_data = {
                "status": "success",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "log_file": log_file,
                "total_lines": len(all_lines),
                "lines_returned": len(last_lines),
                "lines_requested": lines,
                "log_content": [line.rstrip() for line in last_lines]  # Remove trailing newlines
            }
            
            response = json.dumps(log_data, indent=2)
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Content-length', str(len(response)))
            self.end_headers()
            self.wfile.write(response.encode())
            
        except Exception as e:
            error_response = json.dumps({
                "status": "error",
                "message": f"Failed to read log file: {str(e)}",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('Content-length', str(len(error_response)))
            self.end_headers()
            self.wfile.write(error_response.encode())
    
    def send_log_html(self, lines=40):
        """Send last N lines from log file as HTML"""
        try:
            log_file = 'direct_mt5_monitor.log'
            
            # Check if log file exists
            if not os.path.exists(log_file):
                html_content = """
                <!DOCTYPE html>
                <html><head><title>MT5 Bot Logs</title></head>
                <body><h1>Log File Not Found</h1><p>The log file does not exist yet.</p></body>
                </html>
                """
                
                self.send_response(404)
                self.send_header('Content-type', 'text/html')
                self.send_header('Content-length', str(len(html_content)))
                self.end_headers()
                self.wfile.write(html_content.encode())
                return
            
            # Read the last N lines from the log file
            with open(log_file, 'r', encoding='utf-8') as f:
                all_lines = f.readlines()
                last_lines = all_lines[-lines:] if len(all_lines) >= lines else all_lines
            
            # Create HTML response
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>MT5 Bot Logs - Last {len(last_lines)} Lines</title>
                <style>
                    body {{ font-family: 'Consolas', 'Monaco', monospace; margin: 20px; background-color: #1e1e1e; color: #d4d4d4; }}
                    h1 {{ color: #569cd6; }}
                    .log-info {{ background: #2d2d30; padding: 10px; margin: 10px 0; border-radius: 5px; }}
                    .log-content {{ background: #0c0c0c; padding: 15px; border-radius: 5px; white-space: pre-wrap; font-size: 12px; overflow-x: auto; }}
                    .refresh-btn {{ background: #007acc; color: white; padding: 8px 16px; border: none; border-radius: 4px; cursor: pointer; margin: 10px 0; }}
                    .refresh-btn:hover {{ background: #005a9e; }}
                </style>
            </head>
            <body>
                <h1>📋 MT5 Trading Bot Logs</h1>
                
                <div class="log-info">
                    <strong>File:</strong> {log_file}<br>
                    <strong>Total Lines:</strong> {len(all_lines):,}<br>
                    <strong>Showing:</strong> Last {len(last_lines)} lines<br>
                    <strong>Updated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br>
                    <button class="refresh-btn" onclick="location.reload()">🔄 Refresh</button>
                    <a href="/log?format=html&lines=100" class="refresh-btn">📄 Show 100 Lines</a>
                    <a href="/log?format=json" class="refresh-btn">📊 JSON Format</a>
                </div>
                
                <div class="log-content">{''.join(last_lines).replace('<', '&lt;').replace('>', '&gt;')}</div>
                
                <script>
                    // Auto-refresh every 30 seconds
                    setTimeout(function(){{ location.reload(); }}, 30000);
                </script>
            </body>
            </html>
            """
            
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.send_header('Content-length', str(len(html_content)))
            self.end_headers()
            self.wfile.write(html_content.encode())
            
        except Exception as e:
            error_html = f"""
            <!DOCTYPE html>
            <html><head><title>Error - MT5 Bot Logs</title></head>
            <body><h1>Error Reading Log File</h1><p>{str(e)}</p></body>
            </html>
            """
            
            self.send_response(500)
            self.send_header('Content-type', 'text/html')
            self.send_header('Content-length', str(len(error_html)))
            self.end_headers()
            self.wfile.write(error_html.encode())
    
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
            logger.info(f"   GET http://localhost:{self.port}/alive - Simple alive check")
            logger.info(f"   GET/POST http://localhost:{self.port}/restart - Restart VPS via OVH API")
            logger.info(f"   POST http://localhost:{self.port}/totalcancel - Close all positions & cancel orders")
            logger.info(f"   POST http://localhost:{self.port}/closeall - Close all open positions")
            logger.info(f"   POST http://localhost:{self.port}/be - Move to break even & cancel orders")
            logger.info(f"   POST http://localhost:{self.port}/cancelorders - Cancel all pending orders")
            logger.info(f"   GET http://localhost:{self.port}/log - Last 40 log lines (JSON)")
            logger.info(f"   GET http://localhost:{self.port}/log?format=html - HTML log viewer")
            logger.info(f"   GET http://localhost:{self.port}/log?lines=N - Last N log lines")
            logger.info(f"   GET http://localhost:{self.port}/ - Simple status")
            
        except Exception as e:
            logger.error(f"Failed to start health server: {e}")
    
    def stop(self):
        """Stop the HTTP server"""
        if self.server:
            self.server.shutdown()
            self.server.server_close()
            logger.info("🌐 Health check server stopped")