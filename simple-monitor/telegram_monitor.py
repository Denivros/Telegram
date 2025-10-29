#!/usr/bin/env python3
"""
Simple Telegram Signal Monitor for Hostinger VPS
Monitors Telegram groups for trading signals and logs them
"""

import asyncio
import json
import logging
import os
import re
from datetime import datetime
from typing import Dict, Any, Optional

import requests
from telethon import TelegramClient, events
from telethon.errors import SessionPasswordNeededError, FloodWaitError
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
API_ID = os.getenv('TELEGRAM_API_ID')
API_HASH = os.getenv('TELEGRAM_API_HASH')
PHONE_NUMBER = os.getenv('TELEGRAM_PHONE')
GROUP_ID = os.getenv('TELEGRAM_GROUP_ID')
SESSION_NAME = os.getenv('SESSION_NAME', 'telegram_monitor')

# N8N Logging Configuration
N8N_LOG_WEBHOOK = os.getenv('N8N_LOG_WEBHOOK', 'https://n8n.srv881084.hstgr.cloud/webhook/trading-logs')

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('telegram_monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SignalParser:
    """Parse trading signals from Telegram messages"""
    
    # Common signal patterns
    PATTERNS = {
        'buy': r'(?i)\b(buy|long|call)\s+(\w+)',
        'sell': r'(?i)\b(sell|short|put)\s+(\w+)',
        'entry': r'(?i)(?:entry|enter|ep)[\s:]*(\d+\.?\d*)',
        'tp': r'(?i)(?:tp|target|take\s?profit)[\s:]*(\d+\.?\d*)',
        'sl': r'(?i)(?:sl|stop\s?loss|stoploss)[\s:]*(\d+\.?\d*)',
        'pair': r'([A-Z]{3}/?[A-Z]{3})',
    }
    
    @classmethod
    def parse_message(cls, message_text: str) -> Optional[Dict[str, Any]]:
        """Parse a message for trading signals"""
        if not message_text:
            return None
            
        message_text = message_text.strip()
        
        # Check for buy/sell signals
        buy_match = re.search(cls.PATTERNS['buy'], message_text)
        sell_match = re.search(cls.PATTERNS['sell'], message_text)
        
        if not (buy_match or sell_match):
            return None
            
        signal = {
            'timestamp': datetime.now().isoformat(),
            'raw_message': message_text,
            'signal_type': 'buy' if buy_match else 'sell',
            'symbol': None,
            'entry_price': None,
            'take_profit': None,
            'stop_loss': None,
        }
        
        # Extract symbol
        pair_match = re.search(cls.PATTERNS['pair'], message_text)
        if pair_match:
            signal['symbol'] = pair_match.group(1).replace('/', '').upper()
        elif buy_match:
            signal['symbol'] = buy_match.group(2).upper()
        elif sell_match:
            signal['symbol'] = sell_match.group(2).upper()
            
        # Extract entry price
        entry_match = re.search(cls.PATTERNS['entry'], message_text)
        if entry_match:
            signal['entry_price'] = float(entry_match.group(1))
            
        # Extract take profit
        tp_match = re.search(cls.PATTERNS['tp'], message_text)
        if tp_match:
            signal['take_profit'] = float(tp_match.group(1))
            
        # Extract stop loss
        sl_match = re.search(cls.PATTERNS['sl'], message_text)
        if sl_match:
            signal['stop_loss'] = float(sl_match.group(1))
            
        return signal

class LogManager:
    """Handle logging to various destinations"""
    
    @staticmethod
    def log_to_n8n(data: Dict[str, Any]) -> bool:
        """Send log data to n8n webhook"""
        try:
            if not N8N_LOG_WEBHOOK:
                logger.warning("N8N webhook URL not configured")
                return False
                
            headers = {'Content-Type': 'application/json'}
            response = requests.post(
                N8N_LOG_WEBHOOK,
                json=data,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info("Successfully sent log to n8n")
                return True
            else:
                logger.error(f"N8N webhook failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to send log to n8n: {e}")
            return False

class TelegramMonitor:
    """Main Telegram monitoring class"""
    
    def __init__(self):
        self.client = None
        self.running = False
        
    async def initialize(self):
        """Initialize Telegram client"""
        if not all([API_ID, API_HASH, PHONE_NUMBER]):
            raise ValueError("Missing Telegram API credentials")
            
        # Check if session file exists
        session_file = f"{SESSION_NAME}.session"
        if not os.path.exists(session_file):
            logger.error(f"Session file {session_file} not found!")
            logger.error("Please run setup_session.py first to create the session file")
            raise ValueError("Session file not found - run setup_session.py first")
            
        self.client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
        
        try:
            await self.client.start()
            
            if not await self.client.is_user_authorized():
                logger.error("Session is not authorized - please recreate session")
                raise ValueError("Session not authorized")
                
        except Exception as e:
            logger.error(f"Failed to initialize Telegram client: {e}")
            raise
                
        logger.info("Successfully initialized Telegram client")
        
    async def start_monitoring(self):
        """Start monitoring Telegram groups"""
        if not self.client:
            await self.initialize()
            
        # Register event handler for new messages
        @self.client.on(events.NewMessage)
        async def handle_new_message(event):
            await self.process_message(event)
            
        self.running = True
        logger.info("Started monitoring Telegram groups")
        
        # Keep the client running
        try:
            await self.client.run_until_disconnected()
        except KeyboardInterrupt:
            logger.info("Monitoring stopped by user")
        except Exception as e:
            logger.error(f"Monitoring error: {e}")
        finally:
            self.running = False
            
    async def process_message(self, event):
        """Process incoming Telegram message"""
        try:
            message = event.message
            
            # Skip if no text
            if not message.text:
                return
                
            # Get chat info
            chat = await event.get_chat()
            chat_title = getattr(chat, 'title', 'Unknown')
            
            # Log all messages for debugging
            logger.info(f"Message from {chat_title}: {message.text[:100]}...")
            
            # Parse for trading signals
            signal = SignalParser.parse_message(message.text)
            
            if signal:
                # Add metadata
                signal.update({
                    'chat_id': event.chat_id,
                    'chat_title': chat_title,
                    'message_id': message.id,
                    'sender_id': message.sender_id,
                })
                
                logger.info(f"📊 Signal detected: {signal['signal_type'].upper()} {signal['symbol']}")
                
                # Log to file
                self.log_signal_to_file(signal)
                
                # Send to n8n
                LogManager.log_to_n8n(signal)
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            
    def log_signal_to_file(self, signal: Dict[str, Any]):
        """Log signal to JSON file"""
        try:
            filename = f"signals_{datetime.now().strftime('%Y%m%d')}.json"
            
            # Read existing data
            signals = []
            if os.path.exists(filename):
                with open(filename, 'r') as f:
                    signals = json.load(f)
                    
            # Add new signal
            signals.append(signal)
            
            # Write back to file
            with open(filename, 'w') as f:
                json.dump(signals, f, indent=2, default=str)
                
            logger.info(f"Signal logged to {filename}")
            
        except Exception as e:
            logger.error(f"Failed to log signal to file: {e}")

async def main():
    """Main function"""
    logger.info("Starting Telegram Signal Monitor")
    
    try:
        monitor = TelegramMonitor()
        await monitor.start_monitoring()
        
    except KeyboardInterrupt:
        logger.info("Application stopped by user")
    except Exception as e:
        logger.error(f"Application error: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())