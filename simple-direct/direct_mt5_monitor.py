#!/usr/bin/env python3
"""
Direct MT5 Telegram Monitor
Connects directly to MT5 via Python library
Sends logs to n8n for Telegram notifications
"""

import asyncio
import json
import logging
import os
import re
import sys
from datetime import datetime
from typing import Dict, Any, Optional
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

# Fix Unicode encoding for Windows console
if sys.platform.startswith('win'):
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

import requests
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.errors import SessionPasswordNeededError, FloodWaitError
from dotenv import load_dotenv

# Try to import MetaTrader5 (available on Windows/Wine only)
try:
    import metatrader5 as mt5
    MT5_AVAILABLE = True
    print(f"✅ MetaTrader5 library loaded successfully - Version: {mt5.version()}")
except ImportError:
    print("❌ MetaTrader5 library not available - using remote MT5 connection mode")
    MT5_AVAILABLE = False
    mt5 = None

# Load environment variables
load_dotenv()

# Configuration
API_ID = os.getenv('TELEGRAM_API_ID')
API_HASH = os.getenv('TELEGRAM_API_HASH')
BOT_TOKEN = os.getenv('BOT_TOKEN')
PHONE_NUMBER = os.getenv('TELEGRAM_PHONE')  # Keep for fallback
STRING_SESSION = os.getenv('STRING_SESSION')  # StringSession for authentication
GROUP_ID = os.getenv('TELEGRAM_GROUP_ID')
SESSION_NAME = os.getenv('SESSION_NAME', 'telegram_monitor')

# MT5 VPS Connection Configuration
MT5_LOGIN = int(os.getenv('MT5_LOGIN', '0'))
MT5_PASSWORD = os.getenv('MT5_PASSWORD', '')
MT5_SERVER = os.getenv('MT5_SERVER', '')

# Trading Configuration
DEFAULT_VOLUME = float(os.getenv('DEFAULT_VOLUME', '0.01'))
BE_PARTIAL_VOLUME = float(os.getenv('BE_PARTIAL_VOLUME', '0.01'))  # Volume to close when moving to BE
PARTIALS_VOLUME = float(os.getenv('PARTIALS_VOLUME', '0.03'))      # Volume to close for partial profits
ENTRY_STRATEGY = os.getenv('ENTRY_STRATEGY', 'adaptive')  # adaptive, midpoint, range_break, momentum
MAGIC_NUMBER = int(os.getenv('MAGIC_NUMBER', '123456'))

# Words/phrases to ignore - won't log as "MESSAGE IGNORED"
IGNORE_WORDS = [
    'weekly trading summary', 'weekly journals', 'fucking', 'elite trader', 'analysis','haha', 'livestream','twitch','how to', 'trading summary',
     'btc','btcusd', 'bitcoin', 'gbpjpy', 'zoom','recaps','recap','shit','w in the chat','stream', 'livestream','channel','batch', 'how to split risk'
]

# N8N Webhooks Configuration - Use feedback URL for all logging
N8N_TELEGRAM_FEEDBACK = os.getenv('N8N_TELEGRAM_FEEDBACK', 'https://n8n.srv881084.hstgr.cloud/webhook/91126b9d-bd23-4e92-8891-5bfb217455c7')
N8N_LOG_WEBHOOK = N8N_TELEGRAM_FEEDBACK  # Use same webhook for all logs

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('direct_mt5_monitor.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


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
            import time
            from datetime import datetime
            
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


class TelegramLogger:
    """Send trading logs to n8n feedback webhook for Telegram notifications"""
    
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
    
    def send_log(self, log_type: str, message: str, level: str = "INFO", data: Dict[str, Any] = None):
        """Send log message to n8n feedback webhook"""
        try:
            # Format as feedback message for consistent handling
            payload = {
                'message': message,
                'timestamp': datetime.now().isoformat(),
                'data': {
                    'log_type': log_type,
                    'level': level,
                    'source': 'mt5_trading_bot',
                    **(data or {})
                }
            }
            
            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=10,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                logger.debug(f"Log sent to Telegram: {message}")
            else:
                logger.warning(f"Failed to send log to Telegram: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Error sending log to Telegram: {e}")
    
    def log_signal_received(self, signal: Dict[str, Any]):
        message = f"📊 NEW SIGNAL: {signal['symbol']} {signal['direction'].upper()}\n"
        message += f"Range: {signal['range_start']}-{signal['range_end']}\n" 
        message += f"SL: {signal['stop_loss']} | TP: {signal['take_profit']}"
        self.send_log("signal_received", message, "INFO", signal)
    
    def log_entry_calculation(self, signal: Dict[str, Any], entry_price: float, order_type: str):
        message = f"🎯 LIMIT ORDER CALCULATED: {signal['symbol']}\n"
        message += f"Strategy: {ENTRY_STRATEGY}\n"
        message += f"Limit Price: {entry_price}\n"
        message += f"Order Type: LIMIT (Pending)"
        
        data = {
            'signal': signal,
            'entry_price': entry_price,
            'order_type': 'limit',
            'strategy': ENTRY_STRATEGY
        }
        self.send_log("entry_calculated", message, "INFO", data)
    
    def log_trade_execution(self, signal: Dict[str, Any], result: Dict[str, Any]):
        if result.get('success'):
            message = f"✅ LIMIT ORDER PLACED: {signal['symbol']}\n"
            message += f"Side: {signal['direction'].upper()}\n"
            message += f"Limit Price: {result['entry_price']}\n"
            message += f"Volume: {result['volume']}\n"
            message += f"SL: {signal['stop_loss']} | TP: {signal['take_profit']}\n"
            message += f"Order Type: LIMIT (Pending Execution)"
            
            if 'order_id' in result:
                message += f"\nOrder ID: {result['order_id']}"
            elif 'order' in result:
                message += f"\nOrder: {result['order']}"
                
            self.send_log("limit_order_placed", message, "SUCCESS", result)
        else:
            message = f"❌ LIMIT ORDER FAILED: {signal['symbol']}\n"
            message += f"Error: {result.get('error', 'Unknown error')}\n"
            message += f"Attempted Limit Price: {result.get('entry_price', 'N/A')}"
            
            self.send_log("limit_order_failed", message, "ERROR", result)
    
    def log_system_status(self, status: str, details: str = ""):
        emoji_map = {
            'starting': '🚀', 'connected': '✅', 'error': '❌', 
            'disconnected': '⚠️', 'stopped': '🛑'
        } 
        
        emoji = emoji_map.get(status, '📝')
        message = f"{emoji} SYSTEM {status.upper()}"
        
        if details:
            message += f"\n{details}"
        
        self.send_log("system_status", message, "INFO", {'status': status})
    
    def log_error(self, error_type: str, error_message: str, context: Dict[str, Any] = None):
        message = f"🚨 ERROR: {error_type}\n{error_message}"   
        self.send_log("error", message, "ERROR", context or { })


class TelegramFeedback:
    """Send trade feedback messages to Telegram via N8N webhook"""
    
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
    
    def send_feedback(self, message: str, data: Dict[str, Any] = None):
        """Send feedback message to Telegram via N8N webhook"""
        try:
            payload = {
                'message': message,
                'timestamp': datetime.now().isoformat(),
                'data': data or {},
                'source': 'mt5_trading_bot'
            }
            
            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=10,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                logger.debug(f"Feedback sent to Telegram: {message[:50]}...")
            else:
                logger.warning(f"Failed to send feedback to Telegram: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Error sending feedback to Telegram: {e}")
    
    def notify_signal_received(self, signal: Dict[str, Any]):
        """Send notification when new signal is received"""
        message = f"📊 **NEW SIGNAL DETECTED**\n\n"
        message += f"**Symbol:** {signal['symbol']}\n"
        message += f"**Direction:** {signal['direction'].upper()}\n"
        message += f"**Range:** {signal['range_start']} - {signal['range_end']}\n"
        message += f"**Stop Loss:** {signal['stop_loss']}\n"
        message += f"**Take Profit:** {signal['take_profit']}\n"
        message += f"**Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        self.send_feedback(message, signal)
    
    def notify_trade_executed(self, signal: Dict[str, Any], result: Dict[str, Any]):
        """Send notification when limit order is placed"""
        if result.get('success'):
            message = f"✅ **LIMIT ORDER PLACED SUCCESSFULLY**\n\n"
            message += f"**Symbol:** {signal['symbol']}\n"
            message += f"**Direction:** {signal['direction'].upper()}\n"
            message += f"**Limit Price:** {result['entry_price']}\n"
            message += f"**Volume:** {result['volume']}\n"
            message += f"**Stop Loss:** {signal['stop_loss']}\n"
            message += f"**Take Profit:** {signal['take_profit']}\n"
            message += f"**Order Type:** LIMIT (Pending)\n"
            
            if 'order_id' in result:
                message += f"**Order ID:** {result['order_id']}\n"
            elif 'order' in result:
                message += f"**Order:** {result['order']}\n"
                
            message += f"**Placement Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            message += f"💡 *Order will execute when market reaches limit price*"
        else:
            message = f"❌ **LIMIT ORDER PLACEMENT FAILED**\n\n"
            message += f"**Symbol:** {signal['symbol']}\n"
            message += f"**Direction:** {signal['direction'].upper()}\n"
            message += f"**Attempted Limit Price:** {result.get('entry_price', 'N/A')}\n"
            message += f"**Error:** {result.get('error', 'Unknown error')}\n"
            message += f"**Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        self.send_feedback(message, {'signal': signal, 'result': result})
    
    def notify_system_status(self, status: str, details: str = ""):
        """Send system status notifications"""
        if status == 'started':
            message = f"🚀 **TRADING BOT STARTED**\n\n"
            message += f"**Status:** Online and monitoring\n"
            message += f"**Group ID:** {GROUP_ID}\n"
            message += f"**MT5 Connection:** {'✅ Connected' if MT5_AVAILABLE else '❌ Not Available'}\n"
            message += f"**Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        elif status == 'stopped':
            message = f"🛑 **TRADING BOT STOPPED**\n\n"
            message += f"**Status:** Offline\n"
            message += f"**Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        else:
            message = f"ℹ️ **SYSTEM UPDATE**\n\n"
            message += f"**Status:** {status}\n"
            if details:
                message += f"**Details:** {details}\n"
            message += f"**Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        self.send_feedback(message, {'status': status, 'details': details})
    
    def notify_error(self, error_type: str, error_message: str, context: Dict[str, Any] = None):
        """Send error notifications"""
        message = f"🚨 **ERROR ALERT**\n\n"
        message += f"**Error Type:** {error_type}\n"
        message += f"**Message:** {error_message}\n"
        if context:
            message += f"**Context:** {str(context)[:200]}...\n"
        message += f"**Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        self.send_feedback(message, {'error_type': error_type, 'error_message': error_message, 'context': context})
    
    def notify_sl_break_even(self, position_id: int, break_even_price: float):
        """Send break even notification"""
        message = f"🎯 **STOP LOSS MOVED TO BREAK EVEN**\n\n"
        message += f"**Position:** {position_id}\n"
        message += f"**New SL Price:** {break_even_price}\n"
        message += f"**Status:** Protected at entry level\n"
        message += f"**Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        self.send_feedback(message, {'action': 'sl_break_even', 'position_id': position_id, 'break_even_price': break_even_price})


class TradingSignalParser:
    """Parse trading signals from Telegram messages"""
    
    @staticmethod
    def parse_signal(message_text: str) -> Optional[Dict[str, Any]]:
        try:
            logger.info(f"🔍 PARSING SIGNAL:")
            logger.info(f"   Input: {repr(message_text)}")
            
            # # Check if message contains BTC-related content and ignore it
            # if re.search(r'BTC|BITCOIN', message_text, re.IGNORECASE):
            #     logger.info(f"   [SKIP] Message contains BTC/BITCOIN - ignoring")
            #     return None
            
            # Also skip if range values are too high (likely crypto, not forex)
            range_check = re.search(r'RANGE\s*:?\s*(\d+)', message_text, re.IGNORECASE)
            if range_check and int(range_check.group(1)) > 50000:  # Increased threshold - 4000 could be legitimate forex
                logger.info(f"   [SKIP] Range values too high for Forex (likely crypto) - ignoring")
                return None
            
            # Always use XAUUSD (Gold) as the trading symbol
            symbol = 'XAUUSD.p'
            logger.info(f"   [OK] Symbol: {symbol} (fixed)")
            
            # Extract direction from emojis: 🔴 = SELL, 🟢 = BUY
            direction = None
            if '🔴' in message_text:
                direction = 'SELL'
            elif '🟢' in message_text:
                direction = 'BUY'
            else:
                # Fallback to text-based detection
                if re.search(r'\bSELL\b', message_text, re.IGNORECASE):
                    direction = 'SELL'
                elif re.search(r'\bBUY\b', message_text, re.IGNORECASE):
                    direction = 'BUY'
            
            if not direction:
                logger.warning(f"   [X] No direction found (expected: 🔴 for SELL or 🟢 for BUY)")
                return None
            
            # Extract range (look for any two numbers that might represent a range)
            range_numbers = re.findall(r'(\d+(?:\.\d+)?)', message_text)
            if len(range_numbers) < 4:  # Need at least range_start, range_end, SL, TP
                logger.warning(f"   [X] Not enough numbers found in message (need at least 4)")
                return None
            
            # Try to find range by looking for patterns or take first two numbers
            range_match = re.search(r'(?:RANGE|:)\s*(\d+(?:\.\d+)?)\s*[-–~]\s*(\d+(?:\.\d+)?)', message_text, re.IGNORECASE)
            if range_match:
                range_start = float(range_match.group(1))
                range_end = float(range_match.group(2))
            else:
                # Fallback: assume first two numbers are the range
                range_start = float(range_numbers[0])
                range_end = float(range_numbers[1])
            
            logger.info(f"   [OK] Direction: {direction} (detected from emoji)")
            logger.info(f"   [OK] Range: {range_start} - {range_end}")
            
            # Extract SL - find number after "SL"
            sl_match = re.search(r'SL\s*:?\s*(\d+(?:\.\d+)?)', message_text, re.IGNORECASE)
            if sl_match:
                stop_loss = float(sl_match.group(1))
                logger.info(f"   [OK] Stop Loss: {stop_loss}")
            else:
                logger.warning(f"   [X] No SL (Stop Loss) found")
                return None
            
            # Extract TP - find number after "TP"
            tp_match = re.search(r'TP\s*:?\s*(\d+(?:\.\d+)?)', message_text, re.IGNORECASE)
            if tp_match:
                take_profit = float(tp_match.group(1))
                logger.info(f"   [OK] Take Profit: {take_profit} (using first TP)")
            else:
                logger.warning(f"   [X] No TP (Take Profit) found")
                return None
            # Extract volume/lot size if specified, otherwise use default
            volume_match = re.search(r'(?:lot|lots|volume)s?\s*[:=]?\s*(\d+\.?\d*)', message_text, re.IGNORECASE)
            if volume_match:
                volume = float(volume_match.group(1))
                logger.info(f"   [OK] Volume specified: {volume}")
            else:
                volume = DEFAULT_VOLUME
                logger.info(f"   [OK] Volume (default): {volume}")
            
            logger.info(f"   [SUCCESS] SIGNAL PARSED SUCCESSFULLY!")
            
            return {
                'symbol': symbol,
                'direction': direction.lower(),
                'range_start': range_start,
                'range_end': range_end,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'volume': volume,
                'timestamp': datetime.now().isoformat(),
                'original_message': message_text
            }
            
        except Exception as e:
            logger.error(f"Error parsing signal: {e}")
            return None


class MT5TradingClient:
    """Direct MT5 trading via Python library"""
    
    def __init__(self):
        self.connected = False
        
    def connect(self) -> bool:
        """Connect to remote MT5 VPS"""
        if not mt5.initialize():
            logger.error("MT5 initialize() failed")
            return False
        
        # Connect to MT5 VPS using credentials
        if MT5_LOGIN and MT5_PASSWORD and MT5_SERVER:
            if not mt5.login(MT5_LOGIN, password=MT5_PASSWORD, server=MT5_SERVER):
                logger.error(f"MT5 login failed: {mt5.last_error()}")
                return False
            logger.info(f"Connected to MT5 VPS - Server: {MT5_SERVER}, Account: {MT5_LOGIN}")
        else:
            logger.warning("No MT5 VPS credentials provided, using local MT5 connection")
        
        # Get account info
        account_info = mt5.account_info()
        if account_info is None:
            logger.error("Failed to get account info")
            return False
        
        logger.info(f"Account info - Login: {account_info.login}, Balance: {account_info.balance}")
        self.connected = True
        return True
    
    def disconnect(self):
        """Disconnect from MT5"""
        mt5.shutdown()
        self.connected = False
        logger.info("Disconnected from MT5")
    
    def get_current_price(self, symbol: str) -> Optional[Dict[str, float]]:
        """Get current bid/ask prices"""
        if not self.connected:
            return None
            
        tick = mt5.symbol_info_tick(symbol)
        if tick is None:
            return None
            
        return {'bid': tick.bid, 'ask': tick.ask}
    
    def check_order_status(self, order_id: int = None):
        """Check status of orders and positions"""
        logger.info(f"🔍 CHECKING ORDER STATUS:")
        
        # Get all pending orders
        orders = mt5.orders_get()
        if orders:
            logger.info(f"   📋 PENDING ORDERS ({len(orders)}):")
            for order in orders:
                distance = abs(order.price_open - order.price_current) if order.price_current else 0
                # Get order type name
                order_type_names = {
                    0: "BUY", 1: "SELL", 2: "BUY_LIMIT", 3: "SELL_LIMIT", 
                    4: "BUY_STOP", 5: "SELL_STOP", 6: "BUY_STOP_LIMIT", 7: "SELL_STOP_LIMIT"
                }
                type_name = order_type_names.get(order.type, f"TYPE_{order.type}")
                logger.info(f"     Order {order.ticket}: {order.symbol} {type_name}")
                logger.info(f"       Entry: {order.price_open}, Current: {order.price_current}, Distance: {distance:.5f}")
                logger.info(f"       Volume: {order.volume_initial}, SL: {order.sl}, TP: {order.tp}")
        else:
            logger.info(f"   📋 No pending orders")
        
        # Get open positions
        positions = mt5.positions_get()
        if positions:
            logger.info(f"   📍 OPEN POSITIONS ({len(positions)}):")
            for pos in positions:
                # Get position type name
                pos_type_name = "BUY" if pos.type == 0 else "SELL"
                logger.info(f"     Position {pos.ticket}: {pos.symbol} {pos_type_name}")
                logger.info(f"       Open: {pos.price_open}, Current: {pos.price_current}, Profit: ${pos.profit}")
        else:
            logger.info(f"   📍 No open positions")
    
    def calculate_entry_price(self, signal: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate entry price based on strategy - Always returns limit order type"""
        symbol = signal['symbol']
        direction = signal['direction']
        range_start = signal['range_start']
        range_end = signal['range_end']
        
        # Get current price
        prices = self.get_current_price(symbol)
        current_price = prices['ask'] if direction == 'buy' else prices['bid'] if prices else None
        
        # DEBUG: Log market information
        logger.info(f"🔍 DEBUGGING ORDER PLACEMENT:")
        logger.info(f"   Symbol: {symbol}")
        logger.info(f"   Direction: {direction.upper()}")
        logger.info(f"   Signal Range: {range_start} - {range_end}")
        logger.info(f"   Current Market: Bid={prices['bid'] if prices else 'N/A'}, Ask={prices['ask'] if prices else 'N/A'}")
        logger.info(f"   Reference Price ({direction}): {current_price}")
        logger.info(f"   Strategy: {ENTRY_STRATEGY}")
        
        if ENTRY_STRATEGY == 'midpoint':
            entry_price = (range_start + range_end) / 2
            logger.info(f"   📍 MIDPOINT Strategy: Entry = {entry_price}")
            
        elif ENTRY_STRATEGY == 'range_break':
            entry_price = range_end if direction == 'buy' else range_start
            logger.info(f"   📍 RANGE_BREAK Strategy: Entry = {entry_price} ({'range_end' if direction == 'buy' else 'range_start'})")
            
        elif ENTRY_STRATEGY == 'momentum':
            entry_price = range_start if direction == 'buy' else range_end
            logger.info(f"   📍 MOMENTUM Strategy: Entry = {entry_price} ({'range_start' if direction == 'buy' else 'range_end'})")
            
        elif ENTRY_STRATEGY == 'adaptive':
            if current_price is None:
                entry_price = (range_start + range_end) / 2
                logger.info(f"   📍 ADAPTIVE Strategy (no price): Entry = {entry_price} (midpoint)")
            else:
                if direction == 'buy':
                    if current_price > range_end:
                        # Price is above range - set limit at range top for better entry
                        entry_price = range_end
                        logger.info(f"   📍 ADAPTIVE Strategy (BUY): Price {current_price} > range_end {range_end} → Entry = {entry_price}")
                    elif current_price < range_start:
                        # Price is below range - set limit slightly above current for quick fill
                        symbol_info = mt5.symbol_info(symbol)
                        pip_value = 10 ** (-symbol_info.digits) if symbol_info else 0.0001
                        entry_price = current_price + (2 * pip_value)  # 2 pips above current
                        logger.info(f"   📍 ADAPTIVE Strategy (BUY): Price {current_price} < range_start {range_start} → Entry = {entry_price} (+2 pips)")
                    else:
                        # Price is in range - set limit at current price
                        entry_price = current_price
                        logger.info(f"   📍 ADAPTIVE Strategy (BUY): Price {current_price} in range → Entry = {entry_price}")
                else:  # sell
                    if current_price < range_start:
                        # Price is below range - set limit at range bottom for better entry
                        entry_price = range_start
                        logger.info(f"   📍 ADAPTIVE Strategy (SELL): Price {current_price} < range_start {range_start} → Entry = {entry_price}")
                    elif current_price > range_end:
                        # Price is above range - set limit slightly below current for quick fill
                        symbol_info = mt5.symbol_info(symbol)
                        pip_value = 10 ** (-symbol_info.digits) if symbol_info else 0.0001
                        entry_price = current_price - (2 * pip_value)  # 2 pips below current
                        logger.info(f"   📍 ADAPTIVE Strategy (SELL): Price {current_price} > range_end {range_end} → Entry = {entry_price} (-2 pips)")
                    else:
                        # Price is in range - set limit at current price
                        entry_price = current_price
                        logger.info(f"   📍 ADAPTIVE Strategy (SELL): Price {current_price} in range → Entry = {entry_price}")
        else:
            entry_price = (range_start + range_end) / 2
        
        # Get symbol info for normalization
        symbol_info = mt5.symbol_info(symbol)
        if symbol_info:
            digits = symbol_info.digits
            entry_price = round(entry_price, digits)
        
        return {
            'entry_price': entry_price,
            'order_type': 'limit',  # Always limit orders now
            'current_price': current_price,
            'strategy_used': ENTRY_STRATEGY,
            'range_start': range_start,
            'range_end': range_end
        }
    
    def execute_trade(self, signal: Dict[str, Any], entry_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the trading signal - Always use LIMIT orders"""
        try:
            symbol = signal['symbol']
            direction = signal['direction']
            entry_price = entry_data['entry_price']
            
            # Get current market price for comparison
            tick = mt5.symbol_info_tick(symbol)
            if not tick:
                return {
                    'success': False,
                    'error': f"Could not get market price for {symbol}",
                    'entry_price': entry_price,
                    'volume': DEFAULT_VOLUME
                }
            
            current_ask = tick.ask
            current_bid = tick.bid
            
            # DEBUG: Show current market vs entry price
            logger.info(f"🔍 ORDER TYPE DETERMINATION:")
            logger.info(f"   Current Market: Bid={current_bid}, Ask={current_ask}")
            logger.info(f"   Entry Price: {entry_price}")
            logger.info(f"   Direction: {direction.upper()}")
            
            # Use LIMIT orders at the calculated entry price
            if direction == 'buy':
                order_type_mt5 = mt5.ORDER_TYPE_BUY_LIMIT
                logger.info(f"   ✅ BUY LIMIT order at {entry_price}")
            else:  # sell
                order_type_mt5 = mt5.ORDER_TYPE_SELL_LIMIT
                logger.info(f"   ✅ SELL LIMIT order at {entry_price}")

            logger.info(f"   💡 Order will trigger when market reaches {entry_price}")
            logger.info(f"   💡 Take Profit (TP): {signal['take_profit']}, Stop Loss (SL): {signal['stop_loss']}")
            
            # Use volume from signal, fallback to default if not provided
            volume = signal.get('volume', DEFAULT_VOLUME)
            logger.info(f"   Volume: {volume}")
            
            # Prepare limit order request
            request = {
                "action": mt5.TRADE_ACTION_PENDING,
                "symbol": symbol,
                "volume": volume,
                "type": order_type_mt5,
                "price": entry_price,  # Always use the calculated entry price
                "sl": signal['stop_loss'],
                "tp": signal['take_profit'],
                "magic": MAGIC_NUMBER,
                "comment": f"TG Limit {ENTRY_STRATEGY}",
                "type_time": mt5.ORDER_TIME_GTC,  # Good Till Cancelled
                "type_filling": mt5.ORDER_FILLING_RETURN,  # Return execution for limit orders
            }
            
            # Send order (no stoplimit needed for simple LIMIT orders)
            result = mt5.order_send(request)
            
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                return {
                    'success': False,
                    'error': f"Order failed: {result.retcode} - {result.comment}",
                    'entry_price': entry_price,
                    'volume': DEFAULT_VOLUME
                }
            
            # DEBUG: Log order placement result
            logger.info(f"✅ ORDER PLACED SUCCESSFULLY:")
            logger.info(f"   Order ID: {result.order}")
            logger.info(f"   Deal ID: {result.deal}")
            logger.info(f"   Return Code: {result.retcode}")
            logger.info(f"   Comment: {result.comment}")
            
            # Check order status immediately after placement
            self.check_order_status()
            
            return {
                'success': True,
                'order': result.order,
                'deal': result.deal,
                'entry_price': entry_price,
                'volume': DEFAULT_VOLUME,
                'retcode': result.retcode,
                'comment': result.comment
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f"Exception: {str(e)}",
                'entry_price': entry_data.get('entry_price', 0),
                'volume': DEFAULT_VOLUME
            }


class TelegramMonitor:
    def __init__(self):
        self.client = None
        self.target_group = None
        self.running = False
        self.signal_parser = TradingSignalParser()
        self.mt5_client = MT5TradingClient()
        self.telegram_logger = TelegramLogger(N8N_LOG_WEBHOOK)
        self.telegram_feedback = TelegramFeedback(N8N_TELEGRAM_FEEDBACK)
        self.health_server = BotHealthServer(port=8080, bot_instance=self)
    
    def should_ignore_message(self, message_text: str) -> bool:
        """Check if message contains common words/phrases that should be ignored"""
        message_lower = message_text.lower().strip()
        
        # Check if message is too short (likely just an emoji or single word)
        if len(message_lower) <= 3:
            return True
            
        # Check against ignore words list
        for ignore_word in IGNORE_WORDS:
            if ignore_word.lower() in message_lower:
                return True
                
        # Check if message is only emojis/symbols (no alphanumeric characters)
        if not any(c.isalnum() for c in message_text):
            return True
            
        return False
   
    def validate_config(self) -> bool:
        """Validate configuration"""
        required_vars = [
            ('TELEGRAM_API_ID', API_ID),


            ('TELEGRAM_API_HASH', API_HASH),
            ('TELEGRAM_GROUP_ID', GROUP_ID)
        ]
        
        if not BOT_TOKEN and not PHONE_NUMBER:
            logger.error("Missing authentication method: need either BOT_TOKEN or TELEGRAM_PHONE")
            return False
        
        missing_vars = [name for name, value in required_vars if not value]
        
        if missing_vars:
            logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
            return False
        
        return True
    
    async def initialize_client(self, retry_count=0):
        """Initialize Telegram client with bot, StringSession, or phone authentication"""
        try:
            # Log configuration status
            logger.info("🔐 Telegram Authentication Configuration:")
            logger.info(f"   API_ID: {'✅ Set' if API_ID else '❌ Missing'}")
            logger.info(f"   API_HASH: {'✅ Set' if API_HASH else '❌ Missing'}")
            logger.info(f"   BOT_TOKEN: {'✅ Set' if BOT_TOKEN else '❌ Missing'}")
            logger.info(f"   STRING_SESSION: {'✅ Set' if STRING_SESSION else '❌ Missing'}")
            logger.info(f"   PHONE_NUMBER: {'✅ Set' if PHONE_NUMBER else '❌ Missing'}")
            
            # Determine session type - StringSession takes priority
            if STRING_SESSION:
                logger.info("🔑 Using StringSession for authentication...")
                logger.info(f"   StringSession length: {len(STRING_SESSION)} characters")
                self.client = TelegramClient(
                    StringSession(STRING_SESSION),  # Create StringSession object from string
                    API_ID, 
                    API_HASH,
                    timeout=30,
                    retry_delay=5,
                    auto_reconnect=True
                )
            else:
                # Fallback to file-based session
                logger.info("📁 Using file-based session for authentication...")
                self.client = TelegramClient(
                    SESSION_NAME, 
                    API_ID, 
                    API_HASH,
                    timeout=30,
                    retry_delay=5,
                    auto_reconnect=True
                )
            
            if BOT_TOKEN:
                logger.info("Connecting to Telegram as bot...")
                await self.client.start(bot_token=BOT_TOKEN)
                logger.info("✅ Bot authentication successful!")
            elif STRING_SESSION:
                logger.info("Connecting with StringSession...")
                await self.client.start()
                logger.info("✅ StringSession authentication successful!")
            else:
                logger.info("Connecting to Telegram as user with phone...")
                await self.client.start(phone=PHONE_NUMBER)
            
            # Check authorization for non-bot connections
            if not BOT_TOKEN:
                if not await self.client.is_user_authorized():
                    if STRING_SESSION:
                        logger.error("❌ StringSession is invalid or expired")
                        logger.error("Please generate a new StringSession using generate_string_session_macbook.py")
                        return False
                    else:
                        logger.error("Failed to authorize user - session may be invalid")
                        
                        # Try to delete corrupted session file and retry
                        if retry_count < 2:
                            logger.info(f"Attempting session recovery (attempt {retry_count + 1}/3)")
                            try:
                                import os
                                session_file = f"{SESSION_NAME}.session"
                                if os.path.exists(session_file):
                                    os.remove(session_file)
                                    logger.info("Removed corrupted session file")
                            except Exception as e:
                                logger.warning(f"Could not remove session file: {e}")
                            
                            await asyncio.sleep(2)
                            return await self.initialize_client(retry_count + 1)
                        
                        return False 
                     
            
            # Get target group
            try:
                group_id = GROUP_ID
                if isinstance(group_id, str) and group_id.lstrip('-').isdigit():
                    group_id = int(group_id)
                
                self.target_group = await self.client.get_entity(group_id)
                logger.info(f"Connected to group: {self.target_group.title}")
                
            except Exception as e:
                logger.error(f"Could not find group {GROUP_ID}: {e}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize client: {e}")
            return False
    
    def is_break_even_command(self, message_text: str) -> bool:
        """Check if message is a break even command"""
        break_even_keywords = [
            'break even', 'breakeven', 'be', 'move sl to entry', 
            'sl to entry', 'move stop to entry', 'sl be', 'sl to be', 'set slto be', 'set slto be & take partials now', 'sl to be and take partials here'
        ]
        
        message_lower = message_text.lower()
        for keyword in break_even_keywords:
            if keyword.lower() in message_lower:
                return True
        return False
    
    def move_sl_to_break_even(self):
        """Move Stop Loss to break even (entry price) and close BE_PARTIAL_VOLUME for all open positions"""
        logger.info(f"🎯 MOVING STOP LOSS TO BREAK EVEN:")
        logger.info(f"   BE partial volume to close: {BE_PARTIAL_VOLUME}")
        
        # Get all open positions
        positions = mt5.positions_get()
        if not positions:
            logger.info(f"   ❌ No open positions to modify")
            return
        
        success_count = 0
        skipped_count = 0
        partial_close_count = 0
        
        for pos in positions:
            try:
                # Use entry price as break even
                new_sl = pos.price_open
                
                # Check if SL is already at break even (with small tolerance for floating point comparison)
                tolerance = 0.00001  # 1 pip tolerance
                if abs(pos.sl - new_sl) <= tolerance:
                    logger.info(f"   ⏭️  Position {pos.ticket} ALREADY at break even:")
                    logger.info(f"      Symbol: {pos.symbol}")
                    logger.info(f"      Entry Price: {pos.price_open}")
                    logger.info(f"      Current SL: {pos.sl} (already at BE)")
                    logger.info(f"      ✅ Skipping - no change needed")
                    skipped_count += 1
                    continue
                
                # First, close BE_PARTIAL_VOLUME if position is large enough
                if pos.volume > BE_PARTIAL_VOLUME:
                    logger.info(f"   💰 Closing BE partial volume {BE_PARTIAL_VOLUME} on Position {pos.ticket}")
                    
                    partial_request = {
                        "action": mt5.TRADE_ACTION_DEAL,
                        "position": pos.ticket,
                        "symbol": pos.symbol,
                        "volume": BE_PARTIAL_VOLUME,
                        "type": mt5.ORDER_TYPE_SELL if pos.type == 0 else mt5.ORDER_TYPE_BUY,  # Opposite of position
                        "magic": MAGIC_NUMBER,
                        "comment": f"BE partial close {BE_PARTIAL_VOLUME}",
                        "type_filling": mt5.ORDER_FILLING_IOC,  # Immediate or Cancel
                    }
                    
                    partial_result = mt5.order_send(partial_request)
                    
                    if partial_result.retcode == mt5.TRADE_RETCODE_DONE:
                        logger.info(f"      ✅ BE partial close successful! Deal ID: {partial_result.deal}")
                        partial_close_count += 1
                        
                        # Log partial close
                        self.telegram_logger.send_log(
                            'be_partial_close',
                            f"BE partial close {BE_PARTIAL_VOLUME} on Position {pos.ticket}, Deal: {partial_result.deal}"
                        )
                    else:
                        logger.error(f"      ❌ BE partial close failed: {partial_result.retcode} - {partial_result.comment}")
                else:
                    logger.info(f"   ⚠️  Position {pos.ticket} volume ({pos.volume}) too small for BE partial close ({BE_PARTIAL_VOLUME})")
                
                # Create SL modification request
                request = {
                    "action": mt5.TRADE_ACTION_SLTP,
                    "position": pos.ticket,
                    "sl": new_sl,
                    "tp": pos.tp,  # Keep existing TP
                }
                
                logger.info(f"   📝 Modifying Position {pos.ticket}:")
                logger.info(f"      Symbol: {pos.symbol}")
                logger.info(f"      Entry Price: {pos.price_open}")
                logger.info(f"      Current SL: {pos.sl} → New SL: {new_sl}")
                logger.info(f"      Current TP: {pos.tp} (unchanged)")
                
                # Send modification
                result = mt5.order_send(request)
                
                if result.retcode == mt5.TRADE_RETCODE_DONE:
                    logger.info(f"   ✅ Position {pos.ticket} SL moved to break even!")
                    success_count += 1
                    
                    # Log to n8n and send Telegram notification
                    self.telegram_logger.send_log(
                        'sl_break_even',
                        f"Position {pos.ticket} SL moved to break even at {new_sl}"
                    )
                    self.telegram_feedback.notify_sl_break_even(pos.ticket, new_sl)
                    
                else:
                    logger.error(f"   ❌ Failed to modify Position {pos.ticket}: {result.retcode} - {result.comment}")
                    
            except Exception as e:
                logger.error(f"   ❌ Error modifying Position {pos.ticket}: {e}")
        
        # Summary log
        total_positions = len(positions)
        logger.info(f"🎯 BREAK EVEN COMPLETE:")
        logger.info(f"   📊 Total positions: {total_positions}")
        logger.info(f"   ✅ SL Modified: {success_count}")
        logger.info(f"   💰 Partial closed: {partial_close_count}")
        logger.info(f"   ⏭️  Skipped (already BE): {skipped_count}")
        logger.info(f"   ❌ Failed: {total_positions - success_count - skipped_count}")
    
    def has_existing_trades(self) -> bool:
        """Check if there are any existing orders or positions"""
        # Check for pending orders
        orders = mt5.orders_get()
        if orders and len(orders) > 0:
            logger.info(f"   📋 Found {len(orders)} pending orders")
            return True
        
        # Check for open positions
        positions = mt5.positions_get()
        if positions and len(positions) > 0:
            logger.info(f"   📍 Found {len(positions)} open positions")
            return True
        
        logger.info(f"   ✅ No existing trades found")
        return False
    
    def is_position_closed_command(self, message_text: str) -> bool:
        """Check if message is a position closed command"""
        position_closed_keywords = [
            'position closed', 'positions closed', 'close position', 'close positions',
            'close all', 'close remaining', 'exit all', 'exit position', 'exit positions',
            'close trade', 'close trades', 'position close', 'full close', 'close full'
        ]
        
        message_lower = message_text.lower()
        for keyword in position_closed_keywords:
            if keyword.lower() in message_lower:
                return True
        return False
    
    def is_partial_command(self, message_text: str) -> bool:
        """Check if message is a partial profit command"""
        partial_keywords = [
            'tp1', 'tp2', 'tp3', 'tp 1', 'tp 2', 'tp 3', 'tp 4', 'tp4',
            'take profit', 'close half', 
            'close 50%', 'close 25%', 'close 75%', 'profit', 'taking partials here'
        ]
        
        message_lower = message_text.lower()
        
        # Check for specific TP patterns like "TP 1", "27 Pips TP 1", etc.
        import re
        tp_patterns = [
            r'tp\s*[123]',           # "TP 1", "TP1", "TP 2", etc.
            r'\d+\s*pips?\s*tp\s*[123]', # "27 Pips TP 1", "15 pip TP 2", etc.
            r'pips?\s*tp\s*[123]',   # "Pips TP 1"
        ]
        
        for pattern in tp_patterns:
            if re.search(pattern, message_lower):
                logger.info(f"   🎯 TP Pattern detected: '{pattern}' in '{message_text}'")
                return True
        
        # Check for regular keywords
        for keyword in partial_keywords:
            if keyword in message_lower:
                return True
                
        return False
    
    def is_extend_tp_command(self, message_text: str) -> bool:
        """Check if message is an extend TP command"""
        extend_tp_keywords = [
            'extend tp', 'extend take profit', 'move tp', 'move take profit',
            'change tp', 'update tp', 'new tp', 'tp to', 'extend target'
        ]
        
        message_lower = message_text.lower()
        
        # Check for extend TP patterns with numbers
        import re
        extend_tp_patterns = [
            r'extend\s+tp\s+to\s+(\d+(?:\.\d+)?)',      # "EXTEND TP TO 4102"
            r'move\s+tp\s+to\s+(\d+(?:\.\d+)?)',        # "MOVE TP TO 4102"
            r'tp\s+to\s+(\d+(?:\.\d+)?)',               # "TP TO 4102"
            r'extend.*?tp.*?(\d+(?:\.\d+)?)',           # "EXTEND TP 4102"
            r'new\s+tp\s*:?\s*(\d+(?:\.\d+)?)',         # "NEW TP: 4102"
        ]
        
        for pattern in extend_tp_patterns:
            if re.search(pattern, message_lower):
                logger.info(f"   🎯 Extend TP Pattern detected: '{pattern}' in '{message_text}'")
                return True
        
        # Check for regular extend TP keywords
        for keyword in extend_tp_keywords:
            if keyword in message_lower and re.search(r'\d+(?:\.\d+)?', message_text):
                return True
                
        return False
    
    def process_partial_profit(self, message_text: str):
        """Process partial profit taking commands - closes PARTIALS_VOLUME"""
        logger.info(f"💰 PROCESSING PARTIAL PROFIT:")
        logger.info(f"   Message: {message_text}")
        logger.info(f"   Partial volume to close: {PARTIALS_VOLUME}")
        
        # Extract TP level and pips information if available
        import re
        tp_level_match = re.search(r'tp\s*([123])', message_text.lower())
        pips_match = re.search(r'(\d+)\s*pips?', message_text.lower())
        
        tp_level = tp_level_match.group(1) if tp_level_match else "Unknown"
        pips_profit = pips_match.group(1) if pips_match else "Unknown"
        
        logger.info(f"   📈 TP Level: {tp_level}")
        logger.info(f"   📊 Pips Profit: {pips_profit}")
        
        # Get all open positions
        positions = mt5.positions_get()
        if not positions:
            logger.info(f"   ❌ No open positions for partial profit")
            return
        
        success_count = 0
        for pos in positions:
            try:
                # Check if position has enough volume for partial close
                if pos.volume <= PARTIALS_VOLUME:
                    logger.info(f"   ⚠️  Position {pos.ticket} volume ({pos.volume}) <= partial volume ({PARTIALS_VOLUME})")
                    logger.info(f"      Skipping partial close - would close entire position")
                    continue
                
                # Create partial close request
                request = {
                    "action": mt5.TRADE_ACTION_DEAL,
                    "position": pos.ticket,
                    "symbol": pos.symbol,
                    "volume": PARTIALS_VOLUME,
                    "type": mt5.ORDER_TYPE_SELL if pos.type == 0 else mt5.ORDER_TYPE_BUY,  # Opposite of position
                    "magic": MAGIC_NUMBER,
                    "comment": f"Partial close {PARTIALS_VOLUME}",
                    "type_filling": mt5.ORDER_FILLING_IOC,  # Immediate or Cancel
                }
                
                logger.info(f"   � Closing partial on Position {pos.ticket}:")
                logger.info(f"      Symbol: {pos.symbol}")
                logger.info(f"      Original Volume: {pos.volume}")
                logger.info(f"      Closing Volume: {PARTIALS_VOLUME}")
                logger.info(f"      Remaining Volume: {pos.volume - PARTIALS_VOLUME}")
                
                # Send partial close order
                result = mt5.order_send(request)
                
                if result.retcode == mt5.TRADE_RETCODE_DONE:
                    logger.info(f"   ✅ Partial close successful on Position {pos.ticket}!")
                    logger.info(f"      Deal ID: {result.deal}")
                    success_count += 1
                    
                    # Log to n8n and send Telegram notification
                    self.telegram_logger.send_log(
                        'partial_profit',
                        f"TP{tp_level} - {pips_profit} pips: Partial close {PARTIALS_VOLUME} on Position {pos.ticket}, Deal: {result.deal}"
                    )
                    self.telegram_feedback.send_feedback(
                        f"💰 **PARTIAL PROFIT TAKEN (TP{tp_level})**\n\n"
                        f"**Position:** {pos.ticket}\n"
                        f"**TP Level:** TP{tp_level}\n"
                        f"**Pips Profit:** {pips_profit}\n"
                        f"**Volume Closed:** {PARTIALS_VOLUME}\n"
                        f"**Deal ID:** {result.deal}\n"
                        f"**Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                        {'action': 'partial_profit', 'position_id': pos.ticket, 'volume_closed': PARTIALS_VOLUME, 'deal_id': result.deal, 'tp_level': tp_level, 'pips_profit': pips_profit}
                    )
                    
                else:
                    logger.error(f"   ❌ Failed partial close on Position {pos.ticket}: {result.retcode} - {result.comment}")
                    
            except Exception as e:
                logger.error(f"   ❌ Error closing partial on Position {pos.ticket}: {e}")
        
        logger.info(f"💰 PARTIAL PROFIT COMPLETE: {success_count}/{len(positions)} positions partially closed")
    
    def close_remaining_positions(self):
        """Close all remaining open positions completely"""
        logger.info(f"🔴 CLOSING ALL REMAINING POSITIONS:")
        
        # Get all open positions
        positions = mt5.positions_get()
        if not positions:
            logger.info(f"   ❌ No open positions to close")
            return
        
        success_count = 0
        total_positions = len(positions)
        
        for pos in positions:
            try:
                # Create close request for entire position volume
                request = {
                    "action": mt5.TRADE_ACTION_DEAL,
                    "position": pos.ticket,
                    "symbol": pos.symbol,
                    "volume": pos.volume,  # Close entire remaining volume
                    "type": mt5.ORDER_TYPE_SELL if pos.type == 0 else mt5.ORDER_TYPE_BUY,  # Opposite of position
                    "magic": MAGIC_NUMBER,
                    "comment": f"Position closed - full exit",
                    "type_filling": mt5.ORDER_FILLING_IOC,  # Immediate or Cancel
                }
                
                logger.info(f"   🔴 Closing Position {pos.ticket}:")
                logger.info(f"      Symbol: {pos.symbol}")
                logger.info(f"      Volume: {pos.volume} (FULL CLOSE)")
                logger.info(f"      Entry Price: {pos.price_open}")
                logger.info(f"      Current Price: {pos.price_current}")
                logger.info(f"      Current Profit: ${pos.profit}")
                
                # Send close order
                result = mt5.order_send(request)
                
                if result.retcode == mt5.TRADE_RETCODE_DONE:
                    logger.info(f"   ✅ Position {pos.ticket} closed successfully!")
                    logger.info(f"      Deal ID: {result.deal}")
                    success_count += 1
                    
                    # Log to n8n and send Telegram notification
                    self.telegram_logger.send_log(
                        'position_closed',
                        f"Position {pos.ticket} fully closed - Volume: {pos.volume}, Profit: ${pos.profit}, Deal: {result.deal}"
                    )
                    self.telegram_feedback.send_feedback(
                        f"🔴 **POSITION CLOSED**\n\n"
                        f"**Position:** {pos.ticket}\n"
                        f"**Symbol:** {pos.symbol}\n"
                        f"**Volume Closed:** {pos.volume}\n"
                        f"**Entry Price:** {pos.price_open}\n"
                        f"**Exit Price:** {pos.price_current}\n"
                        f"**Profit:** ${pos.profit:.2f}\n"
                        f"**Deal ID:** {result.deal}\n"
                        f"**Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                        {'action': 'position_closed', 'position_id': pos.ticket, 'volume_closed': pos.volume, 'profit': pos.profit, 'deal_id': result.deal}
                    )
                    
                else:
                    logger.error(f"   ❌ Failed to close Position {pos.ticket}: {result.retcode} - {result.comment}")
                    
            except Exception as e:
                logger.error(f"   ❌ Error closing Position {pos.ticket}: {e}")
        
        # Summary log
        logger.info(f"🔴 POSITION CLOSING COMPLETE:")
        logger.info(f"   📊 Total positions: {total_positions}")
        logger.info(f"   ✅ Successfully closed: {success_count}")
        logger.info(f"   ❌ Failed to close: {total_positions - success_count}")
    
    def extend_take_profit(self, message_text: str):
        """Extend take profit levels for all open positions"""
        logger.info(f"🎯 EXTENDING TAKE PROFIT:")
        logger.info(f"   Message: {message_text}")
        
        # Extract new TP price from message
        import re
        tp_price_match = re.search(r'(\d+(?:\.\d+)?)', message_text)
        
        if not tp_price_match:
            logger.error(f"   ❌ No TP price found in message: {message_text}")
            return
        
        new_tp = float(tp_price_match.group(1))
        logger.info(f"   🎯 New TP Level: {new_tp}")
        
        # Get all open positions
        positions = mt5.positions_get()
        if not positions:
            logger.info(f"   ❌ No open positions to modify TP")
            return
        
        success_count = 0
        for pos in positions:
            try:
                # Create TP modification request
                request = {
                    "action": mt5.TRADE_ACTION_SLTP,
                    "position": pos.ticket,
                    "sl": pos.sl,      # Keep existing SL
                    "tp": new_tp,      # Set new TP
                }
                
                logger.info(f"   📝 Extending TP for Position {pos.ticket}:")
                logger.info(f"      Symbol: {pos.symbol}")
                logger.info(f"      Current TP: {pos.tp} → New TP: {new_tp}")
                logger.info(f"      Current SL: {pos.sl} (unchanged)")
                
                # Send modification
                result = mt5.order_send(request)
                
                if result.retcode == mt5.TRADE_RETCODE_DONE:
                    logger.info(f"   ✅ Position {pos.ticket} TP extended successfully!")
                    success_count += 1
                    
                    # Log to n8n and send Telegram notification
                    self.telegram_logger.send_log(
                        'tp_extended',
                        f"Position {pos.ticket} TP extended from {pos.tp} to {new_tp}"
                    )
                    self.telegram_feedback.send_feedback(
                        f"🎯 **TAKE PROFIT EXTENDED**\n\n"
                        f"**Position:** {pos.ticket}\n"
                        f"**Symbol:** {pos.symbol}\n"
                        f"**Previous TP:** {pos.tp}\n"
                        f"**New TP:** {new_tp}\n"
                        f"**SL:** {pos.sl} (unchanged)\n"
                        f"**Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                        {'action': 'tp_extended', 'position_id': pos.ticket, 'old_tp': pos.tp, 'new_tp': new_tp}
                    )
                    
                else:
                    logger.error(f"   ❌ Failed to extend TP for Position {pos.ticket}: {result.retcode} - {result.comment}")
                    
            except Exception as e:
                logger.error(f"   ❌ Error extending TP for Position {pos.ticket}: {e}")
        
        # Summary log
        total_positions = len(positions)
        logger.info(f"🎯 EXTEND TP COMPLETE:")
        logger.info(f"   📊 Total positions: {total_positions}")
        logger.info(f"   ✅ Successfully extended: {success_count}")
        logger.info(f"   ❌ Failed to extend: {total_positions - success_count}")
    
    def process_trading_signal(self, message_text: str): 
        """Process and execute trading signal"""
        try:
            # Early exit: Check ignore words before any processing
            if self.should_ignore_message(message_text):
                logger.debug(f"🔇 Message ignored early (contains ignore words): '{message_text[:30]}...'")
                return
            
            # DEBUG: Log the received message
            logger.info(f"🔍 PROCESSING MESSAGE:")
            logger.info(f"   Raw message: {repr(message_text)}")
            logger.info(f"   Message length: {len(message_text)} characters")
            
            # Check for break even, partial, position closed, and extend TP commands
            has_be_command = self.is_break_even_command(message_text)
            has_partial_command = self.is_partial_command(message_text)
            has_position_closed_command = self.is_position_closed_command(message_text)
            has_extend_tp_command = self.is_extend_tp_command(message_text)
            
            logger.info(f"   🔍 Command Detection: BE={has_be_command}, Partial={has_partial_command}, Close={has_position_closed_command}, ExtendTP={has_extend_tp_command}")
            
            if has_be_command or has_partial_command or has_position_closed_command or has_extend_tp_command:
                if has_be_command:
                    logger.info(f"🎯 BREAK EVEN COMMAND DETECTED!")
                    self.move_sl_to_break_even()
                
                if has_partial_command:
                    logger.info(f"💰 PARTIAL PROFIT COMMAND DETECTED!")
                    self.process_partial_profit(message_text)
                
                if has_position_closed_command:
                    logger.info(f"🔴 POSITION CLOSED COMMAND DETECTED!")
                    self.close_remaining_positions()
                
                if has_extend_tp_command:
                    logger.info(f"🎯 EXTEND TP COMMAND DETECTED!")
                    self.extend_take_profit(message_text)
                
                # If we processed any management commands, don't continue to new signal processing
                return
            
            # Check if we have existing orders or positions - if so, ignore new signals
            if self.has_existing_trades():
                logger.info(f"⚠️  IGNORING NEW SIGNAL - Existing trades detected")
                logger.info(f"   💡 Only BE (break even) and partial commands will be processed")
                logger.info(f"   📋 Use 'BE' to move stop loss to break even")
                logger.info(f"   💰 Use 'TP1', 'TP2', or 'partial' commands for profit taking")
                logger.info(f"📝 MESSAGE IGNORED: '{message_text[:50]}...' - Active trades prevent new signals")
                return
            
            # Parse the signal
            signal = self.signal_parser.parse_signal(message_text)
            if not signal:
                # Only log detailed message if it's not in the ignore list
                if not self.should_ignore_message(message_text):
                    logger.warning(f"❌ NO SIGNAL PARSED - Message did not match trading signal pattern")
                    logger.info(f"   Expected pattern: [SYMBOL] BUY/SELL RANGE: X-Y SL: Z TP: W")
                    logger.info(f"   Received: {message_text}")
                    logger.info(f"📝 MESSAGE IGNORED: '{message_text[:50]}...' - Invalid signal format")
                else:
                    logger.debug(f"🔇 Ignored common message: '{message_text[:30]}...'")
                return
            
            # Log signal received and send Telegram feedback
            self.telegram_logger.log_signal_received(signal)
            self.telegram_feedback.notify_signal_received(signal)
            
            logger.info(f"📊 Parsed signal: {signal['symbol']} {signal['direction']} "
                       f"{signal['range_start']}-{signal['range_end']} "
                       f"SL:{signal['stop_loss']} TP:{signal['take_profit']}")
            
            # Calculate entry
            entry_data = self.mt5_client.calculate_entry_price(signal)
            
            # Log entry calculation
            self.telegram_logger.log_entry_calculation(signal, entry_data['entry_price'], entry_data['order_type'])
            
            logger.info(f"🎯 Limit order calculated: Price={entry_data['entry_price']} Type=LIMIT")
            
            # Execute limit order
            result = self.mt5_client.execute_trade(signal, entry_data)
            
            # Log execution result and send Telegram feedback
            self.telegram_logger.log_trade_execution(signal, result)
            self.telegram_feedback.notify_trade_executed(signal, result)
            
            if result['success']:
                logger.info("✅ Limit order placed successfully - waiting for execution")
            else:
                logger.error(f"❌ Limit order failed: {result['error']}")
                
        except Exception as e:
            error_msg = f"Error processing signal: {e}"
            logger.error(error_msg)
            self.telegram_logger.log_error("signal_processing", str(e))
            self.telegram_feedback.notify_error("signal_processing", str(e), {"message": message_text})
    
    async def setup_event_handlers(self):
        """Set up Telegram event handlers"""
        
        @self.client.on(events.NewMessage(chats=self.target_group))
        async def handle_new_message(event):
            try:
                message = event.message
                logger.info(f"🔍 MESSAGE HANDLER CALLED:")
                logger.info(f"   Message ID: {message.id}")
                logger.info(f"   From user: {message.from_id}")
                logger.info(f"   Chat ID: {message.peer_id}")
                logger.info(f"   Has text: {message.text is not None}")
                logger.info(f"   Message type: {type(message.media) if message.media else 'text'}")
                
                if message.text:
                    logger.info(f"   ✅ Message text found: {message.text[:100]}...")
                    logger.info(f"   🎯 CALLING process_trading_signal()")
                    self.process_trading_signal(message.text)
                else:
                    # Check if it's a video message specifically
                    if message.media and hasattr(message.media, 'document') and message.media.document:
                        mime_type = getattr(message.media.document, 'mime_type', '')
                        if 'video' in mime_type:
                            logger.info(f"   📹 VIDEO MESSAGE IGNORED - No text content to process")
                            logger.info(f"      Video mime type: {mime_type}")
                            logger.info(f"📝 MESSAGE IGNORED: Video message (ID: {message.id}) - No text content")
                        else:
                            logger.warning(f"   ❌ No text content in message")
                            logger.info(f"   Message content: {repr(message)}")
                            logger.info(f"📝 MESSAGE IGNORED: Media message (ID: {message.id}) - No text content")
                    else:
                        logger.warning(f"   ❌ No text content in message")
                        logger.info(f"   Message content: {repr(message)}")
                        logger.info(f"📝 MESSAGE IGNORED: Non-text message (ID: {message.id}) - No text content")
                    
            except Exception as e:
                logger.error(f"Error handling message: {e}")
                
                # Check for specific Telegram protocol errors
                error_str = str(e).lower()
                if any(keyword in error_str for keyword in ['constructor', 'tlobject', 'remaining bytes']):
                    logger.error("🔧 Telegram protocol error in message handler")
                    logger.info("💡 Message processing will continue, but session may need refresh")
                else:
                    import traceback
                    logger.error(f"Traceback: {traceback.format_exc()}")
        
        logger.info("Event handlers set up successfully")
    
    async def run(self):
        """Main run loop"""
        if not self.validate_config():
            return False
        
        logger.info(f"Starting Direct MT5 Telegram Monitor...")
        logger.info(f"Strategy: {ENTRY_STRATEGY}, V: {DEFAULT_VOLUME}")
        
        # Connect to MT5
        if not self.mt5_client.connect():
            error_msg = "Failed to connect to MT5"
            self.telegram_logger.log_error("mt5_connection", error_msg)
            self.telegram_feedback.notify_error("mt5_connection", error_msg)
            return False
        
        # Connect to Telegram
        if not await self.initialize_client():
            error_msg = "Failed to connect to Telegram"
            self.telegram_logger.log_error("telegram_connection", error_msg)
            self.telegram_feedback.notify_error("telegram_connection", error_msg)
            return False
        
        await self.setup_event_handlers()
        
        logger.info("✅ Monitor is running. Watching for trading signals...")
        self.running = True
        
        # Start health check server
        self.health_server.start()
        
        # Send single startup notification to Telegram
        self.telegram_feedback.notify_system_status('started', f"Strategy: {ENTRY_STRATEGY}, V: {DEFAULT_VOLUME}")
        
        try:
            await self.client.run_until_disconnected()
        except KeyboardInterrupt:
            logger.info("Received interrupt signal")
        except Exception as e:
            error_msg = f"Unexpected error: {e}"
            logger.error(error_msg)
            
            # Check if it's a Telegram protocol error
            error_str = str(e).lower()
            if any(keyword in error_str for keyword in ['constructor', 'tlobject', 'remaining bytes', 'protocol']):
                logger.error("🔧 Telegram protocol error detected - session may be corrupted")
                logger.info("💡 Recommendation: Restart the bot to regenerate session")
                
                # Try to clean up corrupted session
                try:
                    import os
                    session_file = f"{SESSION_NAME}.session"
                    if os.path.exists(session_file):
                        os.remove(session_file)
                        logger.info("🗑️ Removed corrupted session file")
                except Exception as cleanup_err:
                    logger.warning(f"Could not cleanup session: {cleanup_err}")
            
            self.telegram_logger.log_error("system_error", str(e))
            self.telegram_feedback.notify_error("system_error", str(e))
        finally:
            self.running = False
            if self.client:
                await self.client.disconnect()
            self.mt5_client.disconnect()
            # Stop health check server
            self.health_server.stop()
            # Send single shutdown notification to Telegram
            self.telegram_feedback.notify_system_status('stopped')
        
        logger.info("Monitor stopped")
        return True


async def start_health_server(): 
    """Simple health check server for Docker healthcheck"""
    from http.server import HTTPServer, BaseHTTPRequestHandler 
    import threading
    
    class HealthHandler(BaseHTTPRequestHandler):  
       

         

        def do_GET(self):
            if self.path == '/health':
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                response = {
                    "status": "healthy",
                    "timestamp": datetime.now().isoformat(),
                    "service": "mt5-trading-bot"
                }
                self.wfile.write(json.dumps(response).encode())
            else:
                self.send_response(404)
                self.end_headers()
        
        def log_message(self, format, *args):
            # Suppress default HTTP logging
            pass
    
    def run_server():
        server = HTTPServer(('0.0.0.0', 8000), HealthHandler)
        server.serve_forever()
    
    health_thread = threading.Thread(target=run_server, daemon=True)
    health_thread.start()
    logger.info("Health check server started on port 8000")


async def main():
    """Main entry point"""
    # Start health check server
    await start_health_server()
    
    # Start main bot
    monitor = TelegramMonitor()
    await monitor.run()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutting down gracefully...")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)