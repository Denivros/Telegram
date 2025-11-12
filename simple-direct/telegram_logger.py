"""
Telegram Logger Module
Contains TelegramLogger and TelegramFeedback classes for sending notifications
via n8n webhooks to Telegram.
"""

import logging
import requests
from datetime import datetime
from typing import Dict, Any
from config import *

# Try to import MetaTrader5 for status checks
try:
    import metatrader5 as mt5
    MT5_AVAILABLE = True
except ImportError:
    MT5_AVAILABLE = False
    mt5 = None

logger = logging.getLogger(__name__)


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
    
    def log_entry_calculation(self, signal: Dict[str, Any], entry_price, order_type: str):
        message = f"🎯 LIMIT ORDER CALCULATED: {signal['symbol']}\n"
        message += f"Strategy: {ENTRY_STRATEGY}\n"
        
        if isinstance(entry_price, str):
            message += f"Entry Type: {entry_price}\n"
        else:
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
            
            # Handle both single and multi-position results
            if 'entry_price' in result:
                message += f"Limit Price: {result['entry_price']}\n"
                message += f"Volume: {result['volume']}\n"
            elif 'entry_prices' in result:
                message += f"Multi-Position: {len(result['entry_prices'])} orders at {result['entry_prices']}\n"
                message += f"Total Volume: {result['total_volume']}\n"
            else:
                message += f"Volume: {result.get('volume', 'N/A')}\n"
            
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
        message += f"**Direction:** {signal['direction'].upper()}\n"
        message += f"**Range:** {signal['range_start']} - {signal['range_end']}\n"
        message += f"**SL:** {signal['stop_loss']}\n"
        message += f"**TP:** {signal['take_profit']}\n"
        message += f"**Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        self.send_feedback(message, signal)
    
    def notify_trade_executed(self, signal: Dict[str, Any], result: Dict[str, Any]):
        """Send notification when limit order is placed"""
        if result.get('success'):
            message = f"✅ **LIMIT ORDER PLACED SUCCESSFULLY**\n\n"
            message += f"**Direction:** {signal['direction'].upper()}\n"
            message += f"**Limit Price:** {result['entry_price']}\n"
            message += f"**Volume:** {result['volume']}\n"
            message += f"**SL:** {signal['stop_loss']}\n"
            message += f"**TP:** {signal['take_profit']}\n"
            message += f"**Order Type:** LIMIT (Pending)\n"
            
            if 'order_id' in result:
                message += f"**Order ID:** {result['order_id']}\n"
            elif 'order' in result:
                message += f"**Order:** {result['order']}\n"
                
            message += f"**Placement Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            message += f"💡 *Order will execute when market reaches limit price*"
        else:
            message = f"❌ **LIMIT ORDER PLACEMENT FAILED**\n\n"
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
    
    def notify_sl_moved(self, position_id: int, new_sl_price: float):
        """Send SL moved notification"""
        message = f"🎯 **STOP LOSS MOVED**\n\n"
        message += f"**Position:** {position_id}\n"
        message += f"**New SL Price:** {new_sl_price}\n"
        message += f"**Status:** Stop loss updated\n"
        message += f"**Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        self.send_feedback(message, {'action': 'sl_moved', 'position_id': position_id, 'new_sl_price': new_sl_price})