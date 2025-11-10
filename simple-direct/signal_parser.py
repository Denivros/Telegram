"""
Trading Signal Parser Module
Contains TradingSignalParser class for parsing Telegram trading signals.
"""

import logging
import re
from datetime import datetime
from typing import Dict, Any, Optional
from config import *

logger = logging.getLogger(__name__)


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
                num1 = float(range_match.group(1))
                num2 = float(range_match.group(2))
            else:
                # Fallback: assume first two numbers are the range
                num1 = float(range_numbers[0])
                num2 = float(range_numbers[1])
            
            # Always sort range from high to low (range_start = higher value, range_end = lower value)
            range_start = max(num1, num2)  # Higher value
            range_end = min(num1, num2)    # Lower value
            
            logger.info(f"   [OK] Direction: {direction} (detected from emoji)")
            logger.info(f"   [OK] Range: {range_start} - {range_end} (sorted high to low)")
            
            # Extract SL - find number after "SL"
            sl_match = re.search(r'SL\s*:?\s*(\d+(?:\.\d+)?)', message_text, re.IGNORECASE)
            if sl_match:
                stop_loss = float(sl_match.group(1))
                logger.info(f"   [OK] Stop Loss: {stop_loss}")
            else:
                logger.warning(f"   [X] No SL (Stop Loss) found")
                return None
            
            # Extract TP - find number after "TP" (handles multiple formats)
            # Supports: "TP: 3988", "TP : /3988", "TP 3988", "TP:/3988" etc.
            tp_match = re.search(r'TP\s*:?\s*/?(\d+(?:\.\d+)?)', message_text, re.IGNORECASE)
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