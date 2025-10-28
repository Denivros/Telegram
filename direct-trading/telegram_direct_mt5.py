#!/usr/bin/env python3
"""
Enhanced Telegram Monitor with Direct MT5 Integration
Single Entry Strategy for Range-based Signals
"""

import asyncio
import json
import logging
import os
import sys
import re
from datetime import datetime
from typing import Dict, Any, Optional

import requests
from telethon import TelegramClient, events
from telethon.errors import SessionPasswordNeededError, FloodWaitError
from telethon.tl.types import (
    MessageMediaPhoto, MessageMediaDocument, 
    MessageMediaContact, MessageMediaGeo,
    MessageMediaWebPage, User, Chat, Channel
)
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
API_ID = os.getenv('TELEGRAM_API_ID')
API_HASH = os.getenv('TELEGRAM_API_HASH')
PHONE_NUMBER = os.getenv('TELEGRAM_PHONE')
GROUP_ID = os.getenv('TELEGRAM_GROUP_ID')
SESSION_NAME = os.getenv('SESSION_NAME', 'telegram_monitor')

# MT5 API Configuration
MT5_API_URL = os.getenv('MT5_API_URL', 'http://your-mt5-vps:8080/trade')

# N8N Logging Configuration  
N8N_LOG_WEBHOOK = os.getenv('N8N_LOG_WEBHOOK', 'https://n8n.srv881084.hstgr.cloud/webhook/trading-logs')

# Trading Strategy Configuration
ENTRY_STRATEGY = os.getenv('ENTRY_STRATEGY', 'adaptive')  # adaptive, midpoint, range_break, momentum
VOLUME = float(os.getenv('DEFAULT_VOLUME', '0.01'))

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('telegram_monitor.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class TelegramLogger:
    """Send trading logs and notifications via n8n to Telegram"""
    
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
    
    def send_log(self, log_type: str, message: str, data: Dict[str, Any] = None, level: str = "INFO"):
        """Send log message to n8n webhook for Telegram notification"""
        try:
            payload = {
                'timestamp': datetime.now().isoformat(),
                'log_type': log_type,
                'level': level,
                'message': message,
                'data': data or {},
                'source': 'telegram_mt5_monitor'
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
        """Log when a new trading signal is received"""
        message = f"📊 NEW SIGNAL: {signal['symbol']} {signal['direction'].upper()}\n"
        message += f"Range: {signal['range_start']}-{signal['range_end']}\n"
        message += f"SL: {signal['stop_loss']} | TP: {signal['take_profit']}"
        
        self.send_log("signal_received", message, signal, "INFO")
    
    def log_entry_calculation(self, signal: Dict[str, Any], entry_data: Dict[str, Any]):
        """Log entry price calculation details"""
        message = f"🎯 ENTRY CALCULATED: {signal['symbol']}\n"
        message += f"Strategy: {entry_data['strategy_used']}\n"
        message += f"Entry Price: {entry_data['entry_price']}\n"
        message += f"Order Type: {entry_data['order_type']}\n"
        
        if entry_data['current_price']:
            message += f"Current Price: {entry_data['current_price']}\n"
        
        range_info = entry_data['range_analysis']
        message += f"Range Size: {range_info['range_size']}\n"
        message += f"Midpoint: {range_info['range_midpoint']}"
        
        self.send_log("entry_calculated", message, {
            'signal': signal,
            'entry_data': entry_data
        }, "INFO")
    
    def log_trade_execution(self, signal: Dict[str, Any], entry_data: Dict[str, Any], result: Dict[str, Any]):
        """Log trade execution result"""
        if result.get('success'):
            message = f"✅ TRADE EXECUTED: {signal['symbol']}\n"
            message += f"Side: {signal['direction'].upper()}\n"
            message += f"Entry: {entry_data['entry_price']}\n"
            message += f"Volume: {VOLUME}\n"
            message += f"SL: {signal['stop_loss']} | TP: {signal['take_profit']}\n"
            
            if 'order_id' in result:
                message += f"Order ID: {result['order_id']}\n"
            if 'deal_id' in result:
                message += f"Deal ID: {result['deal_id']}"
                
            level = "SUCCESS"
        else:
            message = f"❌ TRADE FAILED: {signal['symbol']}\n"
            message += f"Error: {result.get('error', 'Unknown error')}\n"
            message += f"Strategy: {entry_data['strategy_used']}\n"
            message += f"Attempted Entry: {entry_data['entry_price']}"
            
            level = "ERROR"
        
        self.send_log("trade_execution", message, {
            'signal': signal,
            'entry_data': entry_data,
            'result': result
        }, level)
    
    def log_system_status(self, status: str, details: str = ""):
        """Log system status changes"""
        emoji_map = {
            'starting': '🚀',
            'connected': '✅',
            'error': '❌', 
            'disconnected': '⚠️',
            'stopped': '🛑'
        }
        
        emoji = emoji_map.get(status, '📝')
        message = f"{emoji} SYSTEM {status.upper()}"
        
        if details:
            message += f"\n{details}"
        
        self.send_log("system_status", message, {'status': status}, "INFO")
    
    def log_market_analysis(self, symbol: str, current_price: float, signal_range: tuple, analysis: str):
        """Log market condition analysis"""
        message = f"📈 MARKET ANALYSIS: {symbol}\n"
        message += f"Current Price: {current_price}\n"
        message += f"Signal Range: {signal_range[0]}-{signal_range[1]}\n"
        message += f"Analysis: {analysis}"
        
        self.send_log("market_analysis", message, {
            'symbol': symbol,
            'current_price': current_price,
            'signal_range': signal_range,
            'analysis': analysis
        }, "INFO")
    
    def log_error(self, error_type: str, error_message: str, context: Dict[str, Any] = None):
        """Log errors and exceptions"""
        message = f"🚨 ERROR: {error_type}\n{error_message}"
        
        self.send_log("error", message, context or {}, "ERROR")


class TradingSignalParser:
    """Parse trading signals from Telegram messages"""
    
    @staticmethod
    def parse_signal(message_text: str) -> Optional[Dict[str, Any]]:
        """Parse trading signal from message text"""
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
                'original_message': message_text
            }
            
        except Exception as e:
            logger.error(f"Error parsing signal: {e}")
            return None


class EntryStrategyCalculator:
    """Calculate entry price based on different strategies"""
    
    @staticmethod
    def get_current_price(symbol: str) -> Optional[float]:
        """Get current market price (you'd implement this with MT5 or broker API)"""
        # Placeholder - implement with actual price feed
        # For now, return None to simulate price fetch
        return None
    
    @staticmethod
    def calculate_entry_price(signal: Dict[str, Any], strategy: str = 'adaptive') -> Dict[str, Any]:
        """Calculate entry price based on strategy"""
        
        symbol = signal['symbol']
        direction = signal['direction']
        range_start = signal['range_start']
        range_end = signal['range_end']
        
        # Get current market price
        current_price = EntryStrategyCalculator.get_current_price(symbol)
        
        if strategy == 'midpoint':
            # Simple midpoint of range
            entry_price = (range_start + range_end) / 2
            order_type = 'limit'
            
        elif strategy == 'range_break':
            # Enter when price breaks into range
            if direction == 'buy':
                entry_price = range_end  # Enter at top of buy range
            else:
                entry_price = range_start  # Enter at bottom of sell range
            order_type = 'limit'
            
        elif strategy == 'momentum':
            # Use range start as more aggressive entry
            entry_price = range_start if direction == 'buy' else range_end
            order_type = 'limit'
            
        elif strategy == 'adaptive':
            # Adaptive based on current price vs range
            if current_price is None:
                # No current price, use midpoint
                entry_price = (range_start + range_end) / 2
                order_type = 'limit'
            else:
                if direction == 'buy':
                    if current_price > range_end:
                        # Price above range, wait for pullback to range top
                        entry_price = range_end
                        order_type = 'limit'
                    elif current_price < range_start:
                        # Price below range, enter at market
                        entry_price = current_price
                        order_type = 'market'
                    else:
                        # Price in range, enter at current price
                        entry_price = current_price
                        order_type = 'market'
                else:  # SELL
                    if current_price < range_start:
                        # Price below range, wait for bounce to range bottom
                        entry_price = range_start
                        order_type = 'limit'
                    elif current_price > range_end:
                        # Price above range, enter at market
                        entry_price = current_price
                        order_type = 'market'
                    else:
                        # Price in range, enter at current price
                        entry_price = current_price
                        order_type = 'market'
        
        else:
            # Default to midpoint
            entry_price = (range_start + range_end) / 2
            order_type = 'limit'
        
        # Round to reasonable decimal places
        entry_price = round(entry_price, 2)
        
        return {
            'entry_price': entry_price,
            'order_type': order_type,
            'strategy_used': strategy,
            'current_price': current_price,
            'range_analysis': {
                'range_size': abs(range_end - range_start),
                'range_midpoint': (range_start + range_end) / 2,
                'aggressive_entry': range_start if direction == 'buy' else range_end,
                'conservative_entry': range_end if direction == 'buy' else range_start
            }
        }


class MT5TradingClient:
    """Handle communication with MT5 API"""
    
    def __init__(self, api_url: str):
        self.api_url = api_url
    
    def send_trade_signal(self, signal: Dict[str, Any], entry_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send trading signal to MT5 API"""
        try:
            trade_data = {
                'symbol': signal['symbol'],
                'side': signal['direction'],
                'type': entry_data['order_type'],
                'price': entry_data['entry_price'],
                'volume': VOLUME,
                'stopLoss': signal['stop_loss'],
                'takeProfit': signal['take_profit'],
                'comment': f"TG Signal - {entry_data['strategy_used']} strategy",
                'metadata': {
                    'strategy': entry_data['strategy_used'],
                    'range_start': signal['range_start'],
                    'range_end': signal['range_end'],
                    'entry_analysis': entry_data['range_analysis'],
                    'timestamp': datetime.now().isoformat()
                }
            }
            
            logger.info(f"Sending trade signal: {trade_data}")
            
            response = requests.post(
                self.api_url,
                json=trade_data,
                timeout=30,
                headers={'Content-Type': 'application/json'}
            )
            
            response.raise_for_status()
            result = response.json()
            
            if result.get('success'):
                logger.info(f"Trade executed successfully: {result}")
                return result
            else:
                logger.error(f"Trade failed: {result}")
                return result
            
        except requests.exceptions.RequestException as e:
            error_result = {
                'success': False,
                'error': f"Request error: {str(e)}",
                'error_type': 'connection_error'
            }
            logger.error(f"Error sending trade signal: {e}")
            return error_result
            
        except Exception as e:
            error_result = {
                'success': False,
                'error': f"Unexpected error: {str(e)}",
                'error_type': 'unknown_error'
            }
            logger.error(f"Error sending trade signal: {e}")
            return error_result


class TelegramMonitor:
    def __init__(self):
        self.client = None
        self.target_group = None
        self.running = False
        self.signal_parser = TradingSignalParser()
        self.mt5_client = MT5TradingClient(MT5_API_URL)
        self.telegram_logger = TelegramLogger(N8N_LOG_WEBHOOK)
        
    def validate_config(self) -> bool:
        """Validate configuration"""
        required_vars = [
            ('TELEGRAM_API_ID', API_ID),
            ('TELEGRAM_API_HASH', API_HASH),
            ('TELEGRAM_PHONE', PHONE_NUMBER),
            ('TELEGRAM_GROUP_ID', GROUP_ID),
            ('MT5_API_URL', MT5_API_URL),
            ('N8N_LOG_WEBHOOK', N8N_LOG_WEBHOOK)
        ]
        
        missing_vars = []
        for var_name, var_value in required_vars:
            if not var_value:
                missing_vars.append(var_name)
        
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
                
                # Send connection success log to Telegram
                self.telegram_logger.log_system_status(
                    'connected', 
                    f"Connected to group: {self.target_group.title}\nStrategy: {ENTRY_STRATEGY}\nVolume: {VOLUME}"
                )
                
            except Exception as e:
                logger.error(f"Could not find group {GROUP_ID}: {e}")
                self.telegram_logger.log_error("connection_failed", f"Could not find group {GROUP_ID}: {e}")
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
                logger.info("Message does not contain a valid trading signal")
                return
            
            # Log signal received to Telegram
            self.telegram_logger.log_signal_received(signal)
            
            logger.info(f"Parsed trading signal: {signal['symbol']} {signal['direction']} "
                       f"{signal['range_start']}-{signal['range_end']} "
                       f"SL:{signal['stop_loss']} TP:{signal['take_profit']}")
            
            # Calculate entry based on strategy
            entry_data = EntryStrategyCalculator.calculate_entry_price(signal, ENTRY_STRATEGY)
            
            # Log entry calculation to Telegram
            self.telegram_logger.log_entry_calculation(signal, entry_data)
            
            logger.info(f"Entry strategy '{ENTRY_STRATEGY}' calculated: "
                       f"Price: {entry_data['entry_price']} "
                       f"Type: {entry_data['order_type']}")
            
            # Send market analysis if current price is available
            if entry_data['current_price']:
                analysis = self._get_market_analysis(signal, entry_data)
                self.telegram_logger.log_market_analysis(
                    signal['symbol'],
                    entry_data['current_price'],
                    (signal['range_start'], signal['range_end']),
                    analysis
                )
            
            # Send to MT5
            result = self.mt5_client.send_trade_signal(signal, entry_data)
            
            # Log execution result to Telegram
            self.telegram_logger.log_trade_execution(signal, entry_data, result)
            
            if result.get('success'):
                logger.info("✅ Trading signal executed successfully")
            else:
                logger.error("❌ Failed to execute trading signal")
                
        except Exception as e:
            logger.error(f"Error processing trading signal: {e}")
            self.telegram_logger.log_error("signal_processing", str(e), {
                'message_text': message_text[:200] + '...' if len(message_text) > 200 else message_text
            })
    
    def _get_market_analysis(self, signal: Dict[str, Any], entry_data: Dict[str, Any]) -> str:
        """Generate market analysis string"""
        current_price = entry_data['current_price']
        range_start = signal['range_start']
        range_end = signal['range_end']
        direction = signal['direction']
        
        if direction == 'buy':
            if current_price > range_end:
                return f"Price above range (+{current_price - range_end:.1f} pips). Waiting for pullback."
            elif current_price < range_start:
                return f"Price below range (-{range_start - current_price:.1f} pips). Immediate entry opportunity."
            else:
                return f"Price in range. {((current_price - range_start) / (range_end - range_start) * 100):.1f}% through range."
        else:  # sell
            if current_price < range_start:
                return f"Price below range (-{range_start - current_price:.1f} pips). Waiting for bounce."
            elif current_price > range_end:
                return f"Price above range (+{current_price - range_end:.1f} pips). Immediate entry opportunity."
            else:
                return f"Price in range. {((range_end - current_price) / (range_end - range_start) * 100):.1f}% through range."
    
    async def setup_event_handlers(self):
        """Set up Telegram event handlers"""
        
        @self.client.on(events.NewMessage(chats=self.target_group))
        async def handle_new_message(event):
            """Handle new messages"""
            try:
                message = event.message
                if message.text:
                    logger.info(f"New message: {message.text[:100]}...")
                    
                    # Process as potential trading signal
                    self.process_trading_signal(message.text)
                
            except Exception as e:
                logger.error(f"Error handling message: {e}")
                self.telegram_logger.log_error("message_handling", str(e))
        
        logger.info("Event handlers set up successfully")
    
    async def run(self):
        """Main run loop"""
        if not self.validate_config():
            return False
        
        # Send startup notification to Telegram
        self.telegram_logger.log_system_status(
            'starting', 
            f"Entry Strategy: {ENTRY_STRATEGY}\nDefault Volume: {VOLUME}\nMT5 API: {MT5_API_URL}"
        )
        
        logger.info(f"Starting Telegram Monitor with {ENTRY_STRATEGY} entry strategy...")
        logger.info(f"Default volume: {VOLUME}")
        logger.info(f"MT5 API URL: {MT5_API_URL}")
        
        if not await self.initialize_client():
            return False
        
        await self.setup_event_handlers()
        
        logger.info("Monitor is running. Watching for trading signals...")
        self.running = True
        
        try:
            await self.client.run_until_disconnected()
        except KeyboardInterrupt:
            logger.info("Received interrupt signal")
            self.telegram_logger.log_system_status('stopped', 'Monitor stopped by user (Ctrl+C)')
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            self.telegram_logger.log_error("system_error", str(e))
        finally:
            self.running = False
            if self.client:
                await self.client.disconnect()
        
        logger.info("Monitor stopped")
        return True


async def main():
    """Main entry point"""
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