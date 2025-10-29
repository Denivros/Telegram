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

import requests
from telethon import TelegramClient, events
from telethon.errors import SessionPasswordNeededError, FloodWaitError
from dotenv import load_dotenv

# Try to import MetaTrader5 (available on Windows/Wine only)
try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
except ImportError:
    print("MetaTrader5 library not available - using remote MT5 connection mode")
    MT5_AVAILABLE = False
    mt5 = None

# Load environment variables
load_dotenv()

# Configuration
API_ID = os.getenv('TELEGRAM_API_ID')
API_HASH = os.getenv('TELEGRAM_API_HASH')
PHONE_NUMBER = os.getenv('TELEGRAM_PHONE')
GROUP_ID = os.getenv('TELEGRAM_GROUP_ID')
SESSION_NAME = os.getenv('SESSION_NAME', 'telegram_monitor')

# MT5 VPS Connection Configuration
MT5_LOGIN = int(os.getenv('MT5_LOGIN', '0'))
MT5_PASSWORD = os.getenv('MT5_PASSWORD', '')
MT5_SERVER = os.getenv('MT5_SERVER', '')

# Trading Configuration
DEFAULT_VOLUME = float(os.getenv('DEFAULT_VOLUME', '0.01'))
ENTRY_STRATEGY = os.getenv('ENTRY_STRATEGY', 'adaptive')  # adaptive, midpoint, range_break, momentum
MAGIC_NUMBER = int(os.getenv('MAGIC_NUMBER', '123456'))

# N8N Webhooks Configuration
N8N_LOG_WEBHOOK = os.getenv('N8N_LOG_WEBHOOK', 'https://n8n.srv881084.hstgr.cloud/webhook/trading-logs')
N8N_TELEGRAM_FEEDBACK = os.getenv('N8N_TELEGRAM_FEEDBACK', 'https://n8n.srv881084.hstgr.cloud/webhook/91126b9d-bd23-4e92-8891-5bfb217455c7')

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('direct_mt5_monitor.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class TelegramLogger:
    """Send trading logs to n8n for Telegram notifications"""
    
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
    
    def send_log(self, log_type: str, message: str, level: str = "INFO", data: Dict[str, Any] = None):
        """Send log message to n8n webhook"""
        try:
            payload = {
                'timestamp': datetime.now().isoformat(),
                'log_type': log_type,
                'level': level,
                'message': message,
                'data': data or {},
                'source': 'direct_mt5_python'
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
        message = f"🎯 ENTRY CALCULATED: {signal['symbol']}\n"
        message += f"Strategy: {ENTRY_STRATEGY}\n"
        message += f"Entry Price: {entry_price}\n"
        message += f"Order Type: {order_type}"
        
        data = {
            'signal': signal,
            'entry_price': entry_price,
            'order_type': order_type,
            'strategy': ENTRY_STRATEGY
        }
        self.send_log("entry_calculated", message, "INFO", data)
    
    def log_trade_execution(self, signal: Dict[str, Any], result: Dict[str, Any]):
        if result.get('success'):
            message = f"✅ TRADE EXECUTED: {signal['symbol']}\n"
            message += f"Side: {signal['direction'].upper()}\n"
            message += f"Entry: {result['entry_price']}\n"
            message += f"Volume: {result['volume']}\n"
            message += f"SL: {signal['stop_loss']} | TP: {signal['take_profit']}"
            
            if 'order' in result:
                message += f"\nOrder: {result['order']}"
            if 'deal' in result:
                message += f"\nDeal: {result['deal']}"
                
            self.send_log("trade_execution", message, "SUCCESS", result)
        else:
            message = f"❌ TRADE FAILED: {signal['symbol']}\n"
            message += f"Error: {result.get('error', 'Unknown error')}\n"
            message += f"Attempted Entry: {result.get('entry_price', 'N/A')}"
            
            self.send_log("trade_execution", message, "ERROR", result)
    
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
        self.send_log("error", message, "ERROR", context or {})


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
        """Send notification when trade is executed"""
        if result.get('success'):
            message = f"✅ **TRADE EXECUTED SUCCESSFULLY**\n\n"
            message += f"**Symbol:** {signal['symbol']}\n"
            message += f"**Direction:** {signal['direction'].upper()}\n"
            message += f"**Entry Price:** {result['entry_price']}\n"
            message += f"**Volume:** {result['volume']}\n"
            message += f"**Stop Loss:** {signal['stop_loss']}\n"
            message += f"**Take Profit:** {signal['take_profit']}\n"
            
            if 'order_id' in result:
                message += f"**Order ID:** {result['order_id']}\n"
            if 'deal_id' in result:
                message += f"**Deal ID:** {result['deal_id']}\n"
                
            message += f"**Execution Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        else:
            message = f"❌ **TRADE EXECUTION FAILED**\n\n"
            message += f"**Symbol:** {signal['symbol']}\n"
            message += f"**Direction:** {signal['direction'].upper()}\n"
            message += f"**Attempted Entry:** {result.get('entry_price', 'N/A')}\n"
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


class TradingSignalParser:
    """Parse trading signals from Telegram messages"""
    
    @staticmethod
    def parse_signal(message_text: str) -> Optional[Dict[str, Any]]:
        try:
            # Extract currency pair
            pair_match = re.search(r'([A-Z]{6,})', message_text)
            if not pair_match:
                return None
            
            symbol = pair_match.group(1)
            
            # Extract direction and range
            range_match = re.search(r'(BUY|SELL)\s+RANGE\s*:?\s*(\d+(?:\.\d+)?)\s*[-–~]\s*(\d+(?:\.\d+)?)', 
                                   message_text, re.IGNORECASE)
            if not range_match:
                return None
            
            direction = range_match.group(1).upper()
            range_start = float(range_match.group(2))
            range_end = float(range_match.group(3))
            
            # Extract SL
            sl_match = re.search(r'SL\s*:?\s*(\d+(?:\.\d+)?)', message_text, re.IGNORECASE)
            if not sl_match:
                return None
            
            stop_loss = float(sl_match.group(1))
            
            # Extract TP
            tp_match = re.search(r'TP\s*:?\s*(\d+(?:\.\d+)?)', message_text, re.IGNORECASE)
            if not tp_match:
                return None
            
            take_profit = float(tp_match.group(1))
            
            return {
                'symbol': symbol,
                'direction': direction.lower(),
                'range_start': range_start,
                'range_end': range_end,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
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
    
    def calculate_entry_price(self, signal: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate entry price based on strategy"""
        symbol = signal['symbol']
        direction = signal['direction']
        range_start = signal['range_start']
        range_end = signal['range_end']
        
        # Get current price
        prices = self.get_current_price(symbol)
        current_price = prices['ask'] if direction == 'buy' else prices['bid'] if prices else None
        
        if ENTRY_STRATEGY == 'midpoint':
            entry_price = (range_start + range_end) / 2
            order_type = 'pending'
            
        elif ENTRY_STRATEGY == 'range_break':
            entry_price = range_end if direction == 'buy' else range_start
            order_type = 'pending'
            
        elif ENTRY_STRATEGY == 'momentum':
            entry_price = range_start if direction == 'buy' else range_end
            order_type = 'pending'
            
        elif ENTRY_STRATEGY == 'adaptive':
            if current_price is None:
                entry_price = (range_start + range_end) / 2
                order_type = 'pending'
            else:
                if direction == 'buy':
                    if current_price > range_end:
                        entry_price = range_end
                        order_type = 'pending'
                    elif current_price < range_start:
                        entry_price = current_price
                        order_type = 'market'
                    else:
                        entry_price = current_price
                        order_type = 'market'
                else:  # sell
                    if current_price < range_start:
                        entry_price = range_start
                        order_type = 'pending'
                    elif current_price > range_end:
                        entry_price = current_price
                        order_type = 'market'
                    else:
                        entry_price = current_price
                        order_type = 'market'
        else:
            entry_price = (range_start + range_end) / 2
            order_type = 'pending'
        
        # Get symbol info for normalization
        symbol_info = mt5.symbol_info(symbol)
        if symbol_info:
            digits = symbol_info.digits
            entry_price = round(entry_price, digits)
        
        return {
            'entry_price': entry_price,
            'order_type': order_type,
            'current_price': current_price,
            'strategy_used': ENTRY_STRATEGY
        }
    
    def execute_trade(self, signal: Dict[str, Any], entry_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the trading signal"""
        try:
            symbol = signal['symbol']
            direction = signal['direction']
            entry_price = entry_data['entry_price']
            order_type = entry_data['order_type']
            
            # Prepare order request
            if order_type == 'market':
                # Market order
                if direction == 'buy':
                    order_type_mt5 = mt5.ORDER_TYPE_BUY
                    price = mt5.symbol_info_tick(symbol).ask
                else:
                    order_type_mt5 = mt5.ORDER_TYPE_SELL  
                    price = mt5.symbol_info_tick(symbol).bid
            else:
                # Pending order
                if direction == 'buy':
                    current_ask = mt5.symbol_info_tick(symbol).ask
                    if entry_price > current_ask:
                        order_type_mt5 = mt5.ORDER_TYPE_BUY_STOP
                    else:
                        order_type_mt5 = mt5.ORDER_TYPE_BUY_LIMIT
                else:
                    current_bid = mt5.symbol_info_tick(symbol).bid
                    if entry_price < current_bid:
                        order_type_mt5 = mt5.ORDER_TYPE_SELL_STOP
                    else:
                        order_type_mt5 = mt5.ORDER_TYPE_SELL_LIMIT
                price = entry_price
            
            request = {
                "action": mt5.TRADE_ACTION_DEAL if order_type == 'market' else mt5.TRADE_ACTION_PENDING,
                "symbol": symbol,
                "volume": DEFAULT_VOLUME,
                "type": order_type_mt5,
                "price": price,
                "sl": signal['stop_loss'],
                "tp": signal['take_profit'],
                "deviation": 20,
                "magic": MAGIC_NUMBER,
                "comment": f"TG Signal {ENTRY_STRATEGY}",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            # Send order
            result = mt5.order_send(request)
            
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                return {
                    'success': False,
                    'error': f"Order failed: {result.retcode} - {result.comment}",
                    'entry_price': entry_price,
                    'volume': DEFAULT_VOLUME
                }
            
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
        
    def validate_config(self) -> bool:
        """Validate configuration"""
        required_vars = [
            ('TELEGRAM_API_ID', API_ID),
            ('TELEGRAM_API_HASH', API_HASH),
            ('TELEGRAM_PHONE', PHONE_NUMBER),
            ('TELEGRAM_GROUP_ID', GROUP_ID)
        ]
        
        missing_vars = [name for name, value in required_vars if not value]
        
        if missing_vars:
            logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
            return False
        
        return True
    
    async def initialize_client(self):
        """Initialize Telegram client"""
        try:
            self.client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
            await self.client.start(phone=PHONE_NUMBER)
            
            if not await self.client.is_user_authorized():
                logger.error("Failed to authorize user")
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
    
    def process_trading_signal(self, message_text: str):
        """Process and execute trading signal"""
        try:
            # Parse the signal
            signal = self.signal_parser.parse_signal(message_text)
            if not signal:
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
            
            logger.info(f"🎯 Entry calculated: Price={entry_data['entry_price']} Type={entry_data['order_type']}")
            
            # Execute trade
            result = self.mt5_client.execute_trade(signal, entry_data)
            
            # Log execution result and send Telegram feedback
            self.telegram_logger.log_trade_execution(signal, result)
            self.telegram_feedback.notify_trade_executed(signal, result)
            
            if result['success']:
                logger.info("✅ Trade executed successfully")
            else:
                logger.error(f"❌ Trade failed: {result['error']}")
                
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
                if message.text:
                    logger.info(f"New message: {message.text[:100]}...")
                    self.process_trading_signal(message.text)
            except Exception as e:
                logger.error(f"Error handling message: {e}")
        
        logger.info("Event handlers set up successfully")
    
    async def run(self):
        """Main run loop"""
        if not self.validate_config():
            return False
        
        # Send startup log
        self.telegram_logger.log_system_status('starting', f"Strategy: {ENTRY_STRATEGY}\\nVolume: {DEFAULT_VOLUME}")
        
        logger.info(f"Starting Direct MT5 Telegram Monitor...")
        logger.info(f"Strategy: {ENTRY_STRATEGY}, Volume: {DEFAULT_VOLUME}")
        
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
        
        # Send connected status and Telegram feedback
        self.telegram_logger.log_system_status('connected', f"Group: {self.target_group.title}\\nMT5 Account: Connected")
        
        await self.setup_event_handlers()
        
        logger.info("✅ Monitor is running. Watching for trading signals...")
        self.running = True
        
        # Send startup notification to Telegram
        self.telegram_feedback.notify_system_status('started', f"Strategy: {ENTRY_STRATEGY}, Volume: {DEFAULT_VOLUME}")
        
        try:
            await self.client.run_until_disconnected()
        except KeyboardInterrupt:
            logger.info("Received interrupt signal")
        except Exception as e:
            error_msg = f"Unexpected error: {e}"
            logger.error(error_msg)
            self.telegram_logger.log_error("system_error", str(e))
            self.telegram_feedback.notify_error("system_error", str(e))
        finally:
            self.running = False
            if self.client:
                await self.client.disconnect()
            self.mt5_client.disconnect()
            self.telegram_logger.log_system_status('stopped', 'Monitor stopped')
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