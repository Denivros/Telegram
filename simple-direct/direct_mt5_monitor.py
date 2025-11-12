#!/usr/bin/env python3
"""
Direct MT5 Telegram Monitor
Connects directly to MT5 via Python library
Sends logs to n8n for Telegram notifications
"""

import asyncio
import logging
import os
import re
import requests
import sys
from datetime import datetime
from typing import Dict, Any

# Fix Unicode encoding for Windows console
if sys.platform.startswith('win'):
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

from telethon import TelegramClient, events
from telethon.sessions import StringSession
from config import *

# Import modular components
from telegram_logger import TelegramLogger, TelegramFeedback
from mt5_client import MT5TradingClient
from signal_parser import TradingSignalParser
from health_server import BotHealthServer

# Try to import MetaTrader5 (available on Windows/Wine only)
try:
    import metatrader5 as mt5
    MT5_AVAILABLE = True
    print(f"✅ MetaTrader5 library loaded successfully - Version: {mt5.version()}")
except ImportError:
    print("❌ MetaTrader5 library not available - using remote MT5 connection mode")
    MT5_AVAILABLE = False
    mt5 = None

# Configuration loaded from config.py

# Custom logging handler to detect system clock errors and trigger restart
class SystemClockErrorHandler(logging.Handler):
    """Custom logging handler that triggers VPS restart on system clock errors"""
    
    def __init__(self):
        super().__init__()
        self.restart_triggered = False
        
    def emit(self, record):
        """Check log record for system clock errors and trigger restart if needed"""
        try:
            # Check if this is a system clock error from Telethon
            if (hasattr(record, 'name') and 
                'telethon' in record.name.lower() and 
                hasattr(record, 'getMessage')):
                
                message = record.getMessage().lower()
                
                # Check for system clock error patterns
                clock_error_patterns = [
                    'system clock is wrong',
                    'set time offset',
                    'clock error',
                    'time synchronization'
                ]
                
                if any(pattern in message for pattern in clock_error_patterns):
                    if not self.restart_triggered:
                        self.restart_triggered = True
                        logger = logging.getLogger(__name__)
                        logger.warning("🕐 SYSTEM CLOCK ERROR DETECTED!")
                        logger.warning(f"   Error message: {record.getMessage()}")
                        logger.warning("🔄 Triggering automatic VPS restart...")
                        
                        # Trigger restart in a separate thread to avoid blocking
                        import threading
                        threading.Thread(
                            target=self._trigger_restart, 
                            daemon=True
                        ).start()
                        
        except Exception as e:
            # Don't let logging errors crash the handler
            pass
    
    def _trigger_restart(self):
        """Trigger VPS restart via the same mechanism as /restart endpoint"""
        try:
            logger = logging.getLogger(__name__)
            
            # Use the health server's restart endpoint
            restart_url = "http://localhost:8080/restart"
            
            logger.info(f"🔄 Sending restart request to {restart_url}")
            
            response = requests.post(restart_url, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                logger.info("✅ VPS restart initiated successfully!")
                logger.info(f"   Response: {result.get('message', 'No message')}")
            else:
                logger.error(f"❌ Restart request failed: {response.status_code}")
                logger.error(f"   Response: {response.text}")
                
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"❌ Failed to trigger automatic restart: {e}")

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

# Add the system clock error handler to the root logger
clock_handler = SystemClockErrorHandler()
clock_handler.setLevel(logging.INFO)
logging.getLogger().addHandler(clock_handler)


# Health server classes moved to health_server.py
# Telegram logger classes moved to telegram_logger.py
# TradingSignalParser class moved to signal_parser.py
# MT5TradingClient class moved to mt5_client.py


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
                logger.info(f"       V: {order.volume_initial}, SL: {order.sl}, TP: {order.tp}")
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
    
    def get_current_price(self, symbol: str):
        """Get current bid/ask prices using MT5TradingClient"""
        return self.mt5_client.get_current_price(symbol)
    
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
        logger.info(f"   Direction: {direction.upper()}")
        logger.info(f"   Signal Range: {range_start} - {range_end}")
        logger.info(f"   Current Market: Bid={prices['bid'] if prices else 'N/A'}, Ask={prices['ask'] if prices else 'N/A'}")
        logger.info(f"   Reference Price ({direction}): {current_price}")
        logger.info(f"   Strategy: {ENTRY_STRATEGY}")
        
        if ENTRY_STRATEGY == 'midpoint':
            entry_price = (range_start + range_end) / 2
            logger.info(f"   📍 MIDPOINT Strategy: Entry = {entry_price}")
            
        elif ENTRY_STRATEGY == 'dual_entry':
            # Calculate dual entry points at 1/3 and 2/3 of the range
            range_span = range_end - range_start
            entry_1 = range_start + (range_span / 3)  # 1/3 point
            entry_2 = range_start + (2 * range_span / 3)  # 2/3 point
            
            logger.info(f"   📍 DUAL_ENTRY Strategy:")
            logger.info(f"      Range: {range_start} - {range_end} (span: {range_span})")
            logger.info(f"      Entry 1 (1/3): {entry_1}")
            logger.info(f"      Entry 2 (2/3): {entry_2}")
            logger.info(f"      V each: 0.07")
            
            # Return both entry points for dual execution
            entry_price = entry_1  # Primary entry for main logic
            
        elif ENTRY_STRATEGY == 'multi_position_entry':
            # Multi-Position strategy: Fixed entry points at range boundaries
            # 4 positions at range END, 3 at MIDDLE, 2 at START
            entry_price = current_price  # Use current price as reference
            range_middle = range_start + ((range_end - range_start) / 2)
            
            logger.info(f"   📍 MULTI_POSITION_ENTRY Strategy ({direction.upper()}):")
            logger.info(f"   📊 Will open {NUMBER_POSITIONS_MULTI} positions at fixed range points")
            logger.info(f"   📊 Range: {range_start} (START) - {range_middle} (MIDDLE) - {range_end} (END)")
            logger.info(f"   📊 Distribution: 4 at END ({range_end}) + 3 at MIDDLE ({range_middle}) + 2 at START ({range_start})")
            logger.info(f"   📊 V per pos: {POSITION_VOLUME_MULTI}")
            logger.info(f"   📊 Total V: {NUMBER_POSITIONS_MULTI * POSITION_VOLUME_MULTI}")
            logger.info(f"   📊 TP levels: 200, 400, 600, 800 pips per zone from entry")
            
        else:
            entry_price = (range_start + range_end) / 2
        
        # Get symbol info for normalization and prepare dual entry data if needed
        symbol_info = mt5.symbol_info(symbol)
        if symbol_info:
            digits = symbol_info.digits
            entry_price = round(entry_price, digits)
        
        # Prepare multi-entry data for dual_entry
        multi_entries = None
        if ENTRY_STRATEGY == 'dual_entry':
            range_span = range_end - range_start
            entry_1 = round(range_start + (range_span / 3), digits) if symbol_info else range_start + (range_span / 3)
            entry_2 = round(range_start + (2 * range_span / 3), digits) if symbol_info else range_start + (2 * range_span / 3)
            multi_entries = [
                {'price': entry_1, 'volume': 0.07},
                {'price': entry_2, 'volume': 0.07}
            ]
        elif ENTRY_STRATEGY == 'multi_position_entry':
            # Multi-Position strategy: Fixed entry points at range boundaries
            # BUY: 4 at END, 3 at MIDDLE, 2 at START | SELL: 2 at END, 3 at MIDDLE, 4 at START
            # Each with TP starting from 200, 400, 600, 800 pips per zone
            range_span = range_end - range_start
            range_middle = range_start + (range_span / 2)
            
            # Create positions at fixed levels (distribution depends on direction)
            positions = []
            
            if direction == 'buy':
                # BUY: More positions at higher price (range_end) - 4,3,2 distribution
                # 4 positions at range END
                for i in range(4):
                    positions.append({
                        'price': range_end,
                        'zone': 'end',
                        'position_number': i + 1
                    })
                
                # 3 positions at range MIDDLE  
                for i in range(3):
                    positions.append({
                        'price': range_middle,
                        'zone': 'middle', 
                        'position_number': i + 5
                    })
                
                # 2 positions at range START
                for i in range(2):
                    positions.append({
                        'price': range_start,
                        'zone': 'start',
                        'position_number': i + 8
                    })
            else:  # direction == 'sell'
                # SELL: More positions at lower price (range_start) - 2,3,4 distribution
                # 2 positions at range END
                for i in range(2):
                    positions.append({
                        'price': range_end,
                        'zone': 'end',
                        'position_number': i + 1
                    })
                
                # 3 positions at range MIDDLE  
                for i in range(3):
                    positions.append({
                        'price': range_middle,
                        'zone': 'middle', 
                        'position_number': i + 3
                    })
                
                # 4 positions at range START
                for i in range(4):
                    positions.append({
                        'price': range_start,
                        'zone': 'start',
                        'position_number': i + 6
                    })
            
            # Set entry_price as range middle for multi-position strategy (representative value)
            entry_price = range_middle
            
            # DEBUG: Log position distribution before processing
            logger.info(f"   🔍 DEBUG Position Distribution:")
            logger.info(f"      Total positions created: {len(positions)}")
            logger.info(f"      NUMBER_POSITIONS_MULTI: {NUMBER_POSITIONS_MULTI}")
            zone_counts = {}
            for p in positions:
                zone_counts[p['zone']] = zone_counts.get(p['zone'], 0) + 1
            logger.info(f"      Zone distribution: {zone_counts}")
            
            # Create multi_entries with grouped TPs (200, 400, 600, 800 pips per zone)
            multi_entries = []
            for i, pos in enumerate(positions[:NUMBER_POSITIONS_MULTI]):
                pos_price = pos['price']
                if symbol_info:
                    pos_price = round(pos_price, symbol_info.digits)
               
                # Calculate grouped TP progression based on position zone and direction
                if direction == 'buy':
                    # BUY: 2 at END, 3 at MIDDLE, 4 at START
                    if pos['zone'] == 'end':  # 2 positions: TP 200, 400 pips
                        zone_tp_levels = [200, 400]
                        zone_index = sum(1 for p in positions[:i] if p['zone'] == 'end')
                    elif pos['zone'] == 'middle':  # 3 positions: TP 200, 400, 600 pips
                        zone_tp_levels = [200, 400, 600]
                        zone_index = sum(1 for p in positions[:i] if p['zone'] == 'middle')
                    else:  # start - 4 positions: TP 200, 400, 600, 800 pips
                        zone_tp_levels = [200, 400, 600, 800]
                        zone_index = sum(1 for p in positions[:i] if p['zone'] == 'start')
                    
                    # DEBUG: Log TP assignment
                    logger.info(f"      Position {i+1}: zone='{pos['zone']}', zone_index={zone_index}, tp_levels={zone_tp_levels}")
                else:  # direction == 'sell'
                    # SELL: 2 at END, 3 at MIDDLE, 4 at START
                    if pos['zone'] == 'end':  # 2 positions: TP 200, 400 pips
                        zone_tp_levels = [200, 400]
                        zone_index = sum(1 for p in positions[:i] if p['zone'] == 'end')
                    elif pos['zone'] == 'middle':  # 3 positions: TP 200, 400, 600 pips
                        zone_tp_levels = [200, 400, 600]
                        zone_index = sum(1 for p in positions[:i] if p['zone'] == 'middle')
                    else:  # start - 4 positions: TP 200, 400, 600, 800 pips
                        zone_tp_levels = [200, 400, 600, 800]
                        zone_index = sum(1 for p in positions[:i] if p['zone'] == 'start')
                    
                    # DEBUG: Log TP assignment
                    logger.info(f"      Position {i+1}: zone='{pos['zone']}', zone_index={zone_index}, tp_levels={zone_tp_levels}")
                
                tp_pips = zone_tp_levels[zone_index] if zone_index < len(zone_tp_levels) else zone_tp_levels[-1]
                
                multi_entries.append({
                    'price': pos_price,
                    'volume': POSITION_VOLUME_MULTI,
                    'tp_pips': tp_pips,  # Grouped TP: range_end(200,400), range_middle(200,400,600), range_start(200,400,600,800)
                    'tp_level': zone_index + 1,
                    'position_zone': pos['zone']
                })
        
        return {
            'entry_price': entry_price,
            'order_type': 'limit',  # Always limit orders now
            'current_price': current_price,
            'strategy_used': ENTRY_STRATEGY,
            'range_start': range_start,
            'range_end': range_end,
            'multi_entries': multi_entries  # None for single, [{'price': x, 'volume': y}, ...] for multi-entry
        }
    
    def execute_trade(self, signal: Dict[str, Any], entry_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the trading signal - Handle both single and dual entry strategies"""
        try:
            symbol = signal['symbol']
            direction = signal['direction']
            entry_price = entry_data['entry_price']
            
            # Check if this is a multi-entry strategy (dual, triple, or multi-tp)
            multi_entries = entry_data.get('multi_entries')
            if multi_entries:
                if len(multi_entries) == 2:
                    logger.info(f"🎯 DUAL ENTRY STRATEGY DETECTED!")
                    logger.info(f"   Placing TWO orders with 0.07 volume each")
                    return self._execute_multi_trades(signal, multi_entries)
                elif len(multi_entries) == 3:
                    logger.info(f"🎯 TRIPLE ENTRY STRATEGY DETECTED!")
                    total_vol = sum(entry['volume'] for entry in multi_entries)
                    logger.info(f"   Placing THREE orders with total volume: {total_vol}")
                    return self._execute_multi_trades(signal, multi_entries)
                elif len(multi_entries) == 5 and multi_entries[0].get('tp_pips') is not None and not multi_entries[0].get('position_zone'):
                    logger.info(f"🎯 MULTI-TP ENTRY STRATEGY DETECTED!")
                    total_vol = sum(entry['volume'] for entry in multi_entries)
                    logger.info(f"   Placing FIVE orders with different TP levels, total volume: {total_vol}")
                    return self._execute_multi_tp_trades(signal, multi_entries)
                elif len(multi_entries) == NUMBER_POSITIONS_MULTI and multi_entries[0].get('position_zone'):
                    logger.info(f"🎯 MULTI-POSITION ENTRY STRATEGY DETECTED!")
                    total_vol = sum(entry['volume'] for entry in multi_entries)
                    logger.info(f"   Placing {NUMBER_POSITIONS_MULTI} orders distributed across range, total volume: {total_vol}")
                    logger.info(f"   Position distribution: 4 close + 3 middle + 2 outer")
                    return self._execute_multi_tp_trades(signal, multi_entries)  # Reuse multi-TP handler
                else:
                    # Fallback for other multi-entry strategies
                    return self._execute_multi_trades(signal, multi_entries)
            
            # Single entry logic
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
            logger.info(f"   V: {volume}")
            
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
    
    def _execute_multi_trades(self, signal: Dict[str, Any], multi_entries: list) -> Dict[str, Any]:
        """Execute multi-entry trades (dual or triple) with flexible volumes"""
        try:
            symbol = signal['symbol']
            direction = signal['direction']
            entry_count = len(multi_entries)
            
            # Get current market price for order type determination
            tick = mt5.symbol_info_tick(symbol)
            if not tick:
                return {
                    'success': False,
                    'error': f"Could not get market price for {symbol}",
                    'entry_price': multi_entries[0]['price'] if multi_entries else 0,
                    'volume': multi_entries[0]['volume'] if multi_entries else 0
                }
            
            current_ask = tick.ask
            current_bid = tick.bid
            
            # Calculate total volume
            total_volume = sum([entry['volume'] for entry in multi_entries])
            
            logger.info(f"🎯 EXECUTING {entry_count} ENTRY ORDERS:")
            logger.info(f"   Direction: {direction.upper()}")
            logger.info(f"   Current Market: Bid={current_bid}, Ask={current_ask}")
            logger.info(f"   Total V: {total_volume}")
            
            for i, entry in enumerate(multi_entries, 1):
                logger.info(f"   Entry {i}/{entry_count}: {entry['price']} - V: {entry['volume']}")
            
            results = []
            successful_orders = 0
            
            # Execute all orders
            for i, entry in enumerate(multi_entries, 1):
                entry_price = entry['price']
                volume = entry['volume']
                
                logger.info(f"\n🔄 PLACING ORDER {i}/{entry_count}:")
                logger.info(f"   Entry Price: {entry_price}")
                logger.info(f"   V: {volume}")
                
                # Get symbol info for pip calculation
                symbol_info = mt5.symbol_info(symbol)
                if symbol_info:
                    pip_value = 10 ** (-symbol_info.digits + (1 if symbol_info.digits == 5 or symbol_info.digits == 3 else 0))
                else:
                    pip_value = 0.0001  # Default for most pairs
                
                # Check if entry price is too close to market price (within ±$1)
                market_price = current_ask if direction == 'buy' else current_bid
                price_distance = abs(entry_price - market_price)
                min_distance = 1.0  # $1 minimum distance
                
                if price_distance <= min_distance:
                    # Market price too close - use market order instead
                    logger.warning(f"   ⚠️  Entry price {entry_price} too close to market {market_price} (distance: {price_distance:.5f})")
                    logger.info(f"   🔄 Converting to MARKET order for immediate execution")
                    
                    if direction == 'buy':
                        order_type_mt5 = mt5.ORDER_TYPE_BUY
                    else:  # sell
                        order_type_mt5 = mt5.ORDER_TYPE_SELL
                    
                    # Market order - no price needed
                    request = {
                        "action": mt5.TRADE_ACTION_DEAL,
                        "symbol": symbol,
                        "volume": volume,
                        "type": order_type_mt5,
                        "sl": signal['stop_loss'],
                        "tp": signal['take_profit'],
                        "magic": MAGIC_NUMBER,
                        "comment": f"TG Market {i}/{entry_count} {ENTRY_STRATEGY}",
                        "type_filling": mt5.ORDER_FILLING_IOC,
                    }
                    logger.info(f"   ✅ {direction.upper()} MARKET order {i} (was limit at {entry_price})")
                else:
                    # Normal limit order
                    if direction == 'buy':
                        order_type_mt5 = mt5.ORDER_TYPE_BUY_LIMIT
                        logger.info(f"   ✅ BUY LIMIT order {i} at {entry_price}")
                    else:  # sell
                        order_type_mt5 = mt5.ORDER_TYPE_SELL_LIMIT
                        logger.info(f"   ✅ SELL LIMIT order {i} at {entry_price}")
                    
                    # Limit order request
                    request = {
                        "action": mt5.TRADE_ACTION_PENDING,
                        "symbol": symbol,
                        "volume": volume,
                        "type": order_type_mt5,
                        "price": entry_price,
                        "sl": signal['stop_loss'],
                        "tp": signal['take_profit'],
                        "magic": MAGIC_NUMBER,
                        "comment": f"TG Multi {i}/{entry_count} {ENTRY_STRATEGY}",
                        "type_time": mt5.ORDER_TIME_GTC,
                        "type_filling": mt5.ORDER_FILLING_RETURN,
                    }
                
                # Send order
                result = mt5.order_send(request)
                
                if result.retcode == mt5.TRADE_RETCODE_DONE:
                    logger.info(f"   ✅ Order {i} placed successfully!")
                    logger.info(f"      Order ID: {result.order}")
                    logger.info(f"      Deal ID: {result.deal}")
                    successful_orders += 1
                    results.append({
                        'order_id': result.order,
                        'deal_id': result.deal,
                        'entry_price': entry_price,
                        'volume': volume,
                        'success': True
                    })
                else:
                    logger.error(f"   ❌ Order {i} failed: {result.retcode} - {result.comment}")
                    results.append({
                        'entry_price': entry_price,
                        'volume': volume,
                        'error': f"{result.retcode} - {result.comment}",
                        'success': False
                    })
            
            # Check order status
            self.check_order_status()
            
            # Extract entry prices for return data
            entry_prices = [entry['price'] for entry in multi_entries]
            
            # Return summary result
            if successful_orders == entry_count:
                logger.info(f"🎉 MULTI-ENTRY SUCCESS: All {entry_count} orders placed!")
                return {
                    'success': True,
                    'multi_entry': True,
                    'entry_type': 'triple' if entry_count == 3 else 'dual',
                    'orders_placed': successful_orders,
                    'total_volume': total_volume,
                    'entry_prices': entry_prices,
                    'results': results
                }
            elif successful_orders > 0:
                logger.warning(f"⚠️ PARTIAL SUCCESS: {successful_orders}/{entry_count} orders placed")
                return {
                    'success': True,
                    'multi_entry': True,
                    'entry_type': 'triple' if entry_count == 3 else 'dual',
                    'orders_placed': successful_orders,
                    'total_volume': sum([r['volume'] for r in results if r.get('success', False)]),
                    'entry_prices': entry_prices,
                    'results': results,
                    'warning': f'Only {successful_orders}/{entry_count} orders placed successfully'
                }
            else:
                logger.error(f"❌ MULTI-ENTRY FAILED: No orders placed successfully")
                return {
                    'success': False,
                    'multi_entry': True,
                    'entry_type': 'triple' if entry_count == 3 else 'dual',
                    'orders_placed': 0,
                    'total_volume': 0,
                    'entry_prices': entry_prices,
                    'results': results,
                    'error': f'All {entry_count} multi-entry orders failed'
                }
                
        except Exception as e:
            logger.error(f"Exception in multi-entry execution: {e}")
            return {
                'success': False,
                'multi_entry': True,
                'error': f"Exception: {str(e)}",
                'entry_prices': [entry.get('price', 0) for entry in multi_entries] if multi_entries else [],
                'volume': multi_entries[0].get('volume', 0) if multi_entries else 0
            }

    def _execute_multi_tp_trades(self, signal: Dict[str, Any], multi_tp_entries: list) -> Dict[str, Any]:
        """Execute multi-TP or multi-position trades with different entry prices and TP levels"""
        try:
            symbol = signal['symbol']
            direction = signal['direction']
            entry_count = len(multi_tp_entries)
            
            # Get current market price and symbol info
            tick = mt5.symbol_info_tick(symbol)
            symbol_info = mt5.symbol_info(symbol)
            if not tick or not symbol_info:
                return {
                    'success': False,
                    'error': f"Could not get market data for {symbol}",
                    'entry_price': multi_tp_entries[0]['price'] if multi_tp_entries else 0,
                    'volume': sum([e['volume'] for e in multi_tp_entries])
                }
            
            current_ask = tick.ask
            current_bid = tick.bid
            
            # Calculate pip value for TP calculations
            pip_value = 10 ** (-symbol_info.digits + (1 if symbol_info.digits == 5 or symbol_info.digits == 3 else 0))
            
            # Calculate total volume
            total_volume = sum([entry['volume'] for entry in multi_tp_entries])
            
            # Check if all positions use same entry (original multi_tp) or different entries (multi_position)
            unique_entries = list(set([entry['price'] for entry in multi_tp_entries]))
            is_multi_position = len(unique_entries) > 1
            
            logger.info(f"🎯 EXECUTING MULTI-{'POSITION' if is_multi_position else 'TP'} ORDERS:")
            logger.info(f"   Direction: {direction.upper()}")
            if is_multi_position:
                logger.info(f"   Entry Prices: {unique_entries}")
            else:
                logger.info(f"   Entry Price: {unique_entries[0]}")
            logger.info(f"   Current Market: Bid={current_bid}, Ask={current_ask}")
            logger.info(f"   Pip Value: {pip_value}")
            logger.info(f"   Total V: {total_volume}")
            
            results = []
            successful_orders = 0
            
            # Execute all TP orders
            for i, entry in enumerate(multi_tp_entries, 1):
                tp_pips = entry['tp_pips']
                volume = entry['volume']
                tp_level = entry['tp_level']
                entry_price = entry['price']  # Use individual entry price for each position
                position_zone = entry.get('position_zone', 'standard')
                
                # Calculate TP price
                if tp_pips is not None:
                    # Use pip-based calculation for each position's entry price
                    if direction == 'buy':
                        tp_price = entry_price + (tp_pips * pip_value)
                    else:  # sell
                        tp_price = entry_price - (tp_pips * pip_value)
                    tp_price = round(tp_price, symbol_info.digits)
                    tp_label = f"TP{tp_level} ({tp_pips} pips)"
                else:
                    # Use signal's original TP
                    tp_price = signal['take_profit']
                    tp_label = f"TP{tp_level} (Signal TP)"
                
                logger.info(f"\n🔄 PLACING ORDER {i}/{entry_count}:")
                logger.info(f"   Entry: {entry_price} ({position_zone})")
                logger.info(f"   {tp_label}: {tp_price}")
                logger.info(f"   V: {volume}")
                
                # Check if entry price is too close to market price (within ±$1)
                market_price = current_ask if direction == 'buy' else current_bid
                price_distance = abs(entry_price - market_price)
                min_distance = 1.0  # $1 minimum distance
                
                if price_distance <= min_distance:
                    # Market price too close - use market order instead
                    logger.warning(f"   ⚠️  Entry price {entry_price} too close to market {market_price} (distance: {price_distance:.5f})")
                    logger.info(f"   🔄 Converting to MARKET order for immediate execution")
                    
                    if direction == 'buy':
                        order_type_mt5 = mt5.ORDER_TYPE_BUY
                    else:  # sell
                        order_type_mt5 = mt5.ORDER_TYPE_SELL
                    
                    # Market order - no price needed
                    request = {
                        "action": mt5.TRADE_ACTION_DEAL,
                        "symbol": symbol,
                        "volume": volume,
                        "type": order_type_mt5,
                        "sl": signal['stop_loss'],
                        "tp": tp_price,
                        "magic": MAGIC_NUMBER,
                        "comment": f"TG Market {tp_level}/5 {tp_pips if tp_pips else 'Signal'}p",
                        "type_filling": mt5.ORDER_FILLING_IOC,
                    }
                    logger.info(f"   ✅ {direction.upper()} MARKET order {i} (was limit at {entry_price})")
                else:
                    # Normal limit order
                    if direction == 'buy':
                        order_type_mt5 = mt5.ORDER_TYPE_BUY_LIMIT
                        logger.info(f"   ✅ BUY LIMIT order {i} at {entry_price}")
                    else:  # sell
                        order_type_mt5 = mt5.ORDER_TYPE_SELL_LIMIT
                        logger.info(f"   ✅ SELL LIMIT order {i} at {entry_price}")
                    
                    # Limit order request
                    request = {
                        "action": mt5.TRADE_ACTION_PENDING,
                        "symbol": symbol,
                        "volume": volume,
                        "type": order_type_mt5,
                        "price": entry_price,
                        "sl": signal['stop_loss'],
                        "tp": tp_price,
                        "magic": MAGIC_NUMBER,
                        "comment": f"TG MultiTP {tp_level}/5 {tp_pips if tp_pips else 'Signal'}p",
                        "type_time": mt5.ORDER_TIME_GTC,
                        "type_filling": mt5.ORDER_FILLING_RETURN,
                    }
                
                # Send order
                result = mt5.order_send(request)
                
                if result.retcode == mt5.TRADE_RETCODE_DONE:
                    logger.info(f"   ✅ {tp_label} order placed successfully!")
                    logger.info(f"      Order ID: {result.order}")
                    logger.info(f"      Deal ID: {result.deal}")
                    successful_orders += 1
                    results.append({
                        'order_id': result.order,
                        'deal_id': result.deal,
                        'entry_price': entry_price,
                        'tp_price': tp_price,
                        'tp_pips': tp_pips,
                        'tp_level': tp_level,
                        'volume': volume,
                        'success': True
                    })
                else:
                    logger.error(f"   ❌ {tp_label} order failed: {result.retcode} - {result.comment}")
                    results.append({
                        'entry_price': entry_price,
                        'tp_price': tp_price,
                        'tp_pips': tp_pips,
                        'tp_level': tp_level,
                        'volume': volume,
                        'error': f"{result.retcode} - {result.comment}",
                        'success': False
                    })
            
            # Check order status
            self.check_order_status()
            
            # Return summary result  
            entry_prices = [r['entry_price'] for r in results if r.get('success', False)]
            
            if successful_orders == entry_count:
                logger.info(f"🎉 MULTI-{'POSITION' if is_multi_position else 'TP'} SUCCESS: All {entry_count} orders placed!")
                return {
                    'success': True,
                    'multi_tp': True,
                    'multi_position': is_multi_position,
                    'orders_placed': successful_orders,
                    'total_volume': total_volume,
                    'entry_prices': unique_entries,
                    'tp_levels': [f"TP{r['tp_level']}" for r in results if r.get('success', False)],
                    'results': results
                }
            elif successful_orders > 0:
                logger.warning(f"⚠️ PARTIAL SUCCESS: {successful_orders}/{entry_count} orders placed")
                return {
                    'success': True,
                    'multi_tp': True,
                    'multi_position': is_multi_position,
                    'orders_placed': successful_orders,
                    'total_volume': sum([r['volume'] for r in results if r.get('success', False)]),
                    'entry_prices': entry_prices,
                    'tp_levels': [f"TP{r['tp_level']}" for r in results if r.get('success', False)],
                    'results': results,
                    'warning': f'Only {successful_orders}/{entry_count} orders placed successfully'
                }
            else:
                logger.error(f"❌ MULTI-{'POSITION' if is_multi_position else 'TP'} FAILED: No orders placed successfully")
                return {
                    'success': False,
                    'multi_tp': True,
                    'multi_position': is_multi_position,
                    'orders_placed': 0,
                    'total_volume': 0,
                    'entry_prices': unique_entries,
                    'results': results,
                    'error': f'All {entry_count} multi-position orders failed'
                }
                
        except Exception as e:
            logger.error(f"Exception in multi-position execution: {e}")
            return {
                'success': False,
                'multi_tp': True,
                'error': f"Exception: {str(e)}",
                'entry_prices': [e.get('price', 0) for e in multi_tp_entries] if multi_tp_entries else [],
                'volume': sum([e.get('volume', 0) for e in multi_tp_entries]) if multi_tp_entries else 0
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
        
        if not PHONE_NUMBER:
            logger.error("Missing authentication method, need TELEGRAM_PHONE")
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
            
            if STRING_SESSION:
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
            'break even', 'breakeven', 'move sl to entry', 
            'sl to entry', 'move stop to entry', 'sl be', 'sl to be', 
            'set slto be', 'set slto be & take partials now',
            'sl to be and take partials here', 'sl to be& take partials'
            'take partials set sl to be now'
        ]
        
        message_lower = message_text.lower()
        for keyword in break_even_keywords:
            if keyword.lower() in message_lower:
                return True
        return False
    
    def move_sl_to_break_even(self):
        """Move Stop Loss to break even (entry price) and close strategy-aware BE partial volume for all open positions"""
        be_partial_vol = get_be_partial_volume()
        logger.info(f"🎯 MOVING STOP LOSS TO BREAK EVEN:")
        logger.info(f"   Strategy: {ENTRY_STRATEGY}")
        logger.info(f"   BE partial volume to close: {be_partial_vol}")
        
        # Cancel all pending orders when moving to break even
        logger.info(f"🚫 Cancelling pending orders (SL to BE triggered)")
        cancel_result = self.cancel_all_pending_orders()
        if cancel_result['cancelled_count'] > 0:
            logger.info(f"   ✅ Cancelled {cancel_result['cancelled_count']} pending orders")
        else:
            logger.info(f"   📋 No pending orders to cancel")
        
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
                    logger.info(f"   ⏭️  Position {pos.ticket} ALREADY at BE:")
                    logger.info(f"      Entry Price: {pos.price_open}")
                    logger.info(f"      Current SL: {pos.sl} (already at BE)")
                    logger.info(f"      ✅ Skipping - no change needed")
                    skipped_count += 1
                    continue
                
                # Create SL modification request
                request = {
                    "action": mt5.TRADE_ACTION_SLTP,
                    "position": pos.ticket,
                    "sl": new_sl,
                    "tp": pos.tp,  # Keep existing TP
                }
                
                logger.info(f"   📝 Modifying Position {pos.ticket}:")
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
        """Check if message is a position closed command - Enhanced with emoji recognition"""
        message_lower = message_text.lower()
        
        # 🔴 EMOJI-BASED DETECTION (High Priority) 🔴
        # Red circles around text = Strong command signal
        if '🔴' in message_text and 'position closed' in message_lower:
            logger.info(f"   🔴 RED EMOJI + 'POSITION CLOSED' detected - STRONG COMMAND signal")
            return True
        
        # Red circles with close-related terms
        if '🔴' in message_text and any(term in message_lower for term in ['close', 'exit', 'closed']):
            logger.info(f"   🔴 RED EMOJI + close terms detected - Command signal")
            return True
        
        # 🟢 GREEN EMOJI EXCLUSION 🟢
        # Green circles typically indicate status/commentary, not commands
        if '🟢' in message_text and 'position closed' in message_lower:
            logger.info(f"   🟢 GREEN EMOJI detected with 'position closed' - COMMENTARY, not command")
            return False
        
        # DESCRIPTIVE PHRASES (Should NOT trigger close)
        descriptive_phrases = [
            'partials taken', 'profits taken', '% of the position closed',
            'over 80%', 'over 90%', 'majority closed', 'let the remaining',
            'let remaining', 'remaining run', 'let it run', 'already closed'
        ]
        
        for phrase in descriptive_phrases:
            if phrase in message_lower:
                logger.info(f"   📝 DESCRIPTIVE phrase detected: '{phrase}' - NOT a command")
                return False
        
        # COMMAND KEYWORDS (Should trigger close)
        position_closed_keywords = [
            'close position', 'close positions', 'close all', 'close remaining',
            'exit all', 'exit position', 'exit positions', 'close trade', 
            'close trades', 'position close', 'full close', 'close full',
            'close everything', 'exit everything'
        ]
        
        for keyword in position_closed_keywords:
            if keyword in message_lower:
                logger.info(f"   💼 COMMAND keyword detected: '{keyword}'")
                return True
        
        # SPECIAL CASE: "position closed" without context
        if 'position closed' in message_lower:
            # Check for ALL CAPS emphasis (indicates command)
            if 'POSITION CLOSED' in message_text:
                logger.info(f"   📢 ALL CAPS 'POSITION CLOSED' detected - Command emphasis")
                return True
            else:
                logger.info(f"   📝 Lowercase 'position closed' without strong signals - Likely commentary")
                return False
        
        return False
    
    def is_partial_command(self, message_text: str) -> bool:
        """Check if message is a partial profit command"""
        partial_keywords = [
            'tp1', 'tp2', 'tp3', 'tp 1', 'tp 2', 'tp 3', 'tp 4', 'tp4',
            'take profit', 'close half', 
            'close 50%', 'close 25%', 'close 75%', 'taking partials here'
        ]
        
        message_lower = message_text.lower()
        
        # Check for specific TP patterns like "TP 1", "27 Pips TP 1", etc.
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
    
    def is_move_sl_command(self, message_text: str) -> bool:
        """Check if message is a move SL command"""
        message_lower = message_text.lower()
        
        # Check for SL movement patterns with numbers
        move_sl_patterns = [
            r'sl\s+at\s+(\d+(?:\.\d+)?)',               # "SL at 4122"
            r'move\s+sl\s+to\s+(\d+(?:\.\d+)?)',        # "MOVE SL TO 4122"
            r'set\s+sl\s+to\s+(\d+(?:\.\d+)?)',         # "SET SL TO 4122"
            r'sl\s+to\s+(\d+(?:\.\d+)?)',               # "SL TO 4122"
            r'stop\s+loss\s+at\s+(\d+(?:\.\d+)?)',      # "STOP LOSS AT 4122"
            r'move\s+stop\s+to\s+(\d+(?:\.\d+)?)',      # "MOVE STOP TO 4122"
            r'new\s+sl\s*:?\s*(\d+(?:\.\d+)?)',         # "NEW SL: 4122"
        ]
        
        for pattern in move_sl_patterns:
            if re.search(pattern, message_lower):
                return True
                
        return False
    
    def is_tp_hit_command(self, message_text: str) -> bool:
        """Check if message indicates TP has been hit and all orders should be cancelled"""
        tp_hit_keywords = [
            'tp hit', 'tp reached', 'take profit hit', 'target reached',
            'tp1 hit', 'tp2 hit', 'tp3 hit', 'tp4 hit', 'tp5 hit',
            'first tp hit', 'tp achieved', 'profit taken',
            'close all orders', 'cancel all orders', 'cancel remaining orders',
            'target hit', 'tp complete', 'full tp', 'tp done'
        ]
        
        message_lower = message_text.lower()
        for keyword in tp_hit_keywords:
            if keyword in message_lower:
                logger.info(f"   🎯 TP Hit detected: '{keyword}' in '{message_text}'")
                return True
        return False
    
    def cancel_all_pending_orders(self):
        """Cancel all pending orders when TP is hit"""
        logger.info(f"🚫 CANCELLING ALL PENDING ORDERS:")
        
        # Get all pending orders
        orders = mt5.orders_get()
        if not orders:
            logger.info(f"   ✅ No pending orders to cancel")
            return {'success': True, 'cancelled_count': 0, 'message': 'No pending orders'}
        
        cancelled_count = 0
        failed_count = 0
        
        logger.info(f"   📋 Found {len(orders)} pending orders to cancel")
        
        for order in orders:
            # Cancel order request
            cancel_request = {
                "action": mt5.TRADE_ACTION_REMOVE,
                "order": order.ticket,
            }
            
            result = mt5.order_send(cancel_request)
            
            if result.retcode == mt5.TRADE_RETCODE_DONE:
                logger.info(f"   ✅ Order {order.ticket} cancelled successfully")
                logger.info(f"      Type: {order.type}, Price: {order.price_open}, V: {order.volume_initial}")
                cancelled_count += 1
            else:
                logger.error(f"   ❌ Failed to cancel order {order.ticket}: {result.retcode} - {result.comment}")
                failed_count += 1
        
        # Send Telegram notification
        if cancelled_count > 0:
            message = f"🚫 **ALL PENDING ORDERS CANCELLED**\n\n"
            message += f"**Orders Cancelled:** {cancelled_count}\n"
            if failed_count > 0:
                message += f"**Failed to Cancel:** {failed_count}\n"
            message += f"**Reason:** TP Hit - Target Achieved\n"
            message += f"**Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            self.telegram_feedback.send_feedback(message, {
                'action': 'cancel_all_orders',
                'cancelled_count': cancelled_count,
                'failed_count': failed_count,
                'reason': 'tp_hit'
            })
        
        logger.info(f"🚫 ORDER CANCELLATION COMPLETE:")
        logger.info(f"   ✅ Cancelled: {cancelled_count}")
        logger.info(f"   ❌ Failed: {failed_count}")
        
        return {
            'success': cancelled_count > 0,
            'cancelled_count': cancelled_count,
            'failed_count': failed_count,
            'message': f'Cancelled {cancelled_count} orders, {failed_count} failed'
        }
    
    def process_partial_profit(self, message_text: str):
        """Process partial profit taking commands - closes strategy-aware partial volume"""
        partials_vol = get_partials_volume()
        logger.info(f"💰 PROCESSING PARTIAL PROFIT:")
        logger.info(f"   Message: {message_text}")
        logger.info(f"   Strategy: {ENTRY_STRATEGY}")
        logger.info(f"   Partial volume to close: {partials_vol}")
        
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
                if pos.volume <= partials_vol:
                    logger.info(f"   ⚠️  Position {pos.ticket} volume ({pos.volume}) <= partial volume ({partials_vol})")
                    logger.info(f"      Skipping partial close - would close entire position")
                    continue
                
                # Create partial close request
                request = {
                    "action": mt5.TRADE_ACTION_DEAL,
                    "position": pos.ticket,
                    "symbol": pos.symbol,
                    "volume": partials_vol,
                    "type": mt5.ORDER_TYPE_SELL if pos.type == 0 else mt5.ORDER_TYPE_BUY,  # Opposite of position
                    "magic": MAGIC_NUMBER,
                    "comment": f"Partial close {partials_vol}",
                    "type_filling": mt5.ORDER_FILLING_IOC,  # Immediate or Cancel
                }
                
                logger.info(f"   � Closing partial on Position {pos.ticket}:")
                logger.info(f"      Original V: {pos.volume}")
                logger.info(f"      Closing V: {partials_vol}")
                logger.info(f"      Remaining V: {pos.volume - partials_vol}")
                
                # Send partial close order
                result = mt5.order_send(request)
                
                if result.retcode == mt5.TRADE_RETCODE_DONE:
                    logger.info(f"   ✅ Partial close successful on Position {pos.ticket}!")
                    logger.info(f"      Deal ID: {result.deal}")
                    success_count += 1
                    
                    # Log to n8n and send Telegram notification
                    self.telegram_logger.send_log(
                        'partial_profit',
                        f"TP{tp_level} - {pips_profit} pips: Partial close {partials_vol} on Position {pos.ticket}, Deal: {result.deal}"
                    )
                    self.telegram_feedback.send_feedback(
                        f"💰 **PARTIAL PROFIT TAKEN (TP{tp_level})**\n\n"
                        f"**Pos:** {pos.ticket}\n"
                        f"**TP Level:** TP{tp_level}\n"
                        f"**Pips Profit:** {pips_profit}\n"
                        f"**V Closed:** {partials_vol}\n"
                        f"**Deal ID:** {result.deal}\n"
                        f"**Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                        {'action': 'partial_profit', 'position_id': pos.ticket, 'volume_closed': partials_vol, 'deal_id': result.deal, 'tp_level': tp_level, 'pips_profit': pips_profit}
                    )
                    
                else:
                    logger.error(f"   ❌ Failed partial close on Position {pos.ticket}: {result.retcode} - {result.comment}")
                    
            except Exception as e:
                logger.error(f"   ❌ Error closing partial on Position {pos.ticket}: {e}")
        
        logger.info(f"💰 PARTIAL PROFIT COMPLETE: {success_count}/{len(positions)} positions partially closed")
        
        # Auto-move to Break Even on TP1 (if not already at BE)
        if tp_level == "1" and success_count > 0:
            logger.info(f"🎯 TP1 DETECTED - AUTO-MOVING REMAINING POSITIONS TO BREAK EVEN:")
            self._auto_move_to_break_even_after_tp1()
    
    def _auto_move_to_break_even_after_tp1(self):
        """Automatically move SL to break even after TP1 (without closing BE_PARTIAL_VOLUME)"""
        logger.info(f"🎯 AUTO BREAK EVEN AFTER TP1:")
        
        # Get all remaining open positions
        positions = mt5.positions_get()
        if not positions:
            logger.info(f"   ❌ No remaining positions to modify")
            return
        
        be_success_count = 0
        be_skipped_count = 0
        
        for pos in positions:
            try:
                # Use entry price as break even
                new_sl = pos.price_open
                
                # Check if SL is already at break even (with tolerance)
                tolerance = 0.00001  # 1 pip tolerance
                if abs(pos.sl - new_sl) <= tolerance:
                    logger.info(f"   ⏭️  Position {pos.ticket} ALREADY at break even:")
                    logger.info(f"      Current SL: {pos.sl} ≈ Entry: {pos.price_open}")
                    logger.info(f"      ✅ Skipping - already protected")
                    be_skipped_count += 1
                    continue
                
                # Create SL modification request (NO partial close - already done in TP1)
                request = {
                    "action": mt5.TRADE_ACTION_SLTP,
                    "position": pos.ticket,
                    "sl": new_sl,
                    "tp": pos.tp,  # Keep existing TP
                }
                
                logger.info(f"   📝 Moving Pos {pos.ticket} to BE:")
                logger.info(f"      Entry Price: {pos.price_open}")
                logger.info(f"      Current SL: {pos.sl} → New SL: {new_sl} (Break Even)")
                logger.info(f"      Current TP: {pos.tp} (unchanged)")
                logger.info(f"      💡 No additional partial close - already done in TP1")
                
                # Send modification
                result = mt5.order_send(request)
                
                if result.retcode == mt5.TRADE_RETCODE_DONE:
                    logger.info(f"   ✅ Position {pos.ticket} SL moved to break even!")
                    be_success_count += 1
                    
                    # Log to n8n and send Telegram notification
                    self.telegram_logger.send_log(
                        'auto_sl_break_even',
                        f"Auto BE after TP1: Position {pos.ticket} SL moved to break even at {new_sl}"
                    )
                    self.telegram_feedback.send_feedback(
                        f"🎯 **AUTO BREAK EVEN (After TP1)**\n\n"
                        f"**Position:** {pos.ticket}\n"
                        f"**New SL Price:** {new_sl}\n"
                        f"**Status:** Protected at entry level\n"
                        f"**Trigger:** Automatic after TP1\n"
                        f"**Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                        {'action': 'auto_sl_break_even', 'position_id': pos.ticket, 'break_even_price': new_sl, 'trigger': 'tp1'}
                    )
                    
                else:
                    logger.error(f"   ❌ Failed to move Position {pos.ticket} to BE: {result.retcode} - {result.comment}")
                    
            except Exception as e:
                logger.error(f"   ❌ Error moving Position {pos.ticket} to BE: {e}")
        
        # Summary log
        total_positions = len(positions)
        logger.info(f"🎯 AUTO BREAK EVEN COMPLETE:")
        logger.info(f"   📊 Remaining positions: {total_positions}")
        logger.info(f"   ✅ Moved to BE: {be_success_count}")
        logger.info(f"   ⏭️  Already at BE: {be_skipped_count}")
        logger.info(f"   ❌ Failed: {total_positions - be_success_count - be_skipped_count}")
    
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
                
                logger.info(f"   🔴 Closing P {pos.ticket}:")
                logger.info(f"      V: {pos.volume} (FULL CLOSE)")
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
                        f"Pos {pos.ticket} fully closed - V: {pos.volume}, Profit: ${pos.profit}, Deal: {result.deal}"
                    )
                    self.telegram_feedback.send_feedback(
                        f"🔴 **POSITION CLOSED**\n\n"
                        f"**Pos:** {pos.ticket}\n"
                        f"**V Closed:** {pos.volume}\n"
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
    
    def move_sl_to_price(self, message_text: str):
        """Move Stop Loss to specified price for all open positions"""
        logger.info(f"🎯 MOVING STOP LOSS TO SPECIFIED PRICE:")
        logger.info(f"   Message: {message_text}")
        
        # Extract SL price from message
        message_lower = message_text.lower()
        sl_price_match = re.search(r'sl\s+at\s+(\d+(?:\.\d+)?)', message_lower)
        
        if not sl_price_match:
            # Try other patterns if "SL at" doesn't match
            other_patterns = [
                r'move\s+sl\s+to\s+(\d+(?:\.\d+)?)',
                r'set\s+sl\s+to\s+(\d+(?:\.\d+)?)',
                r'sl\s+to\s+(\d+(?:\.\d+)?)',
                r'stop\s+loss\s+at\s+(\d+(?:\.\d+)?)',
                r'move\s+stop\s+to\s+(\d+(?:\.\d+)?)',
                r'new\s+sl\s*:?\s*(\d+(?:\.\d+)?)',
            ]
            
            for pattern in other_patterns:
                sl_price_match = re.search(pattern, message_lower)
                if sl_price_match:
                    break
        
        if not sl_price_match:
            logger.error(f"   ❌ Could not extract SL price from message: {message_text}")
            return
        
        new_sl = float(sl_price_match.group(1))
        logger.info(f"   🎯 New SL Price: {new_sl}")
        
        # Get all open positions
        positions = mt5.positions_get()
        if not positions:
            logger.info(f"   ❌ No open positions to modify")
            return
        
        success_count = 0
        for pos in positions:
            try:
                # Check if SL is already at the target price (with small tolerance)
                tolerance = 0.00001  # 1 pip tolerance
                if abs(pos.sl - new_sl) <= tolerance:
                    logger.info(f"   ⏭️  Position {pos.ticket} ALREADY at target SL:")
                    logger.info(f"      Current SL: {pos.sl}, Target SL: {new_sl}")
                    logger.info(f"      ✅ Skipping - no change needed")
                    continue
                
                # Create SL modification request
                request = {
                    "action": mt5.TRADE_ACTION_SLTP,
                    "position": pos.ticket,
                    "sl": new_sl,
                    "tp": pos.tp,  # Keep existing TP
                }
                
                logger.info(f"   📝 Modifying Position {pos.ticket}:")
                logger.info(f"      Current SL: {pos.sl} → New SL: {new_sl}")
                logger.info(f"      Current TP: {pos.tp} (unchanged)")
                
                # Send modification
                result = mt5.order_send(request)
                
                if result.retcode == mt5.TRADE_RETCODE_DONE:
                    logger.info(f"   ✅ Position {pos.ticket} SL moved to {new_sl}!")
                    success_count += 1
                    
                    # Log to n8n and send Telegram notification
                    self.telegram_logger.send_log(
                        'sl_moved',
                        f"Position {pos.ticket} SL moved to {new_sl}"
                    )
                    self.telegram_feedback.notify_sl_moved(pos.ticket, new_sl)
                    
                else:
                    logger.error(f"   ❌ Failed to modify Position {pos.ticket}: {result.retcode} - {result.comment}")
                    
            except Exception as e:
                logger.error(f"   ❌ Error modifying Position {pos.ticket}: {e}")
        
        # Summary log
        total_positions = len(positions)
        logger.info(f"🎯 MOVE SL COMPLETE:")
        logger.info(f"   📊 Total positions: {total_positions}")
        logger.info(f"   ✅ Successfully moved: {success_count}")
        logger.info(f"   ❌ Failed to move: {total_positions - success_count}")
    
    def process_trading_signal(self, message_text: str): 
        """Process and execute trading signal"""
        try:
            # Early exit: Check ignore words before any processing
            if self.should_ignore_message(message_text):
                logger.info(f"🔇 Message ignored early (contains ignore words): '{message_text[:30]}...'")
                return
            
            # DEBUG: Log the received message
            logger.info(f"🔍 PROCESSING MESSAGE:")
            logger.info(f"   Raw message: {repr(message_text)}")
            logger.info(f"   Message length: {len(message_text)} characters")
            
            # Check for break even, partial, position closed, TP hit, extend TP, and move SL commands
            has_be_command = self.is_break_even_command(message_text)
            has_partial_command = self.is_partial_command(message_text)
            has_position_closed_command = self.is_position_closed_command(message_text)
            has_tp_hit_command = self.is_tp_hit_command(message_text)
            has_extend_tp_command = self.is_extend_tp_command(message_text)
            has_move_sl_command = self.is_move_sl_command(message_text)
            
            logger.info(f"   🔍 Command Detection: BE={has_be_command}, Partial={has_partial_command}, Close={has_position_closed_command}, TPHit={has_tp_hit_command}, ExtendTP={has_extend_tp_command}, MoveSL={has_move_sl_command}")
            
            if has_be_command or has_partial_command or has_position_closed_command or has_tp_hit_command or has_extend_tp_command or has_move_sl_command:
                if has_be_command:
                    logger.info(f"🎯 BREAK EVEN COMMAND DETECTED!")
                    self.move_sl_to_break_even()
                
                if has_partial_command:
                    logger.info(f"💰 PARTIAL PROFIT COMMAND DETECTED!")
                    # self.process_partial_profit(message_text)
                
                if has_position_closed_command:
                    logger.info(f"🔴 POSITION CLOSED COMMAND DETECTED!")
                    self.close_remaining_positions()  # Now cancels orders by default
                    self.cancel_all_pending_orders()
                
                if has_tp_hit_command:
                    logger.info(f"🎯 TP HIT COMMAND DETECTED!")
                    # self.cancel_all_pending_orders()
                
                if has_extend_tp_command:
                    logger.info(f"🎯 EXTEND TP COMMAND DETECTED!")
                    self.extend_take_profit(message_text)
                
                if has_move_sl_command:
                    logger.info(f"🎯 MOVE SL COMMAND DETECTED!")
                    self.move_sl_to_price(message_text)
                
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
                    logger.info(f"🔇 Ignored common message: '{message_text[:30]}...'")
                return
            
            # Log signal received and send Telegram feedback
            self.telegram_logger.log_signal_received(signal)
            self.telegram_feedback.notify_signal_received(signal)
            
            logger.info(f"📊 Parsed signal: {signal['symbol']} {signal['direction']} "
                       f"{signal['range_start']}-{signal['range_end']} "
                       f"SL:{signal['stop_loss']} TP:{signal['take_profit']}")
            
            # Calculate entry
            entry_data = self.calculate_entry_price(signal)
            
            # Log entry calculation
            entry_price_to_log = entry_data.get('entry_price', 'Multi-Position')
            self.telegram_logger.log_entry_calculation(signal, entry_price_to_log, entry_data.get('order_type', 'LIMIT'))
            
            if 'entry_price' in entry_data:
                logger.info(f"🎯 Limit order calculated: Price={entry_data['entry_price']} Type=LIMIT")
            else:
                logger.info(f"🎯 Multi-position strategy: Multiple entry points calculated")
            
            # Execute limit order
            result = self.execute_trade(signal, entry_data)
            
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
        
        # Log automatic restart configuration
        logger.info("🔄 Automatic restart system active:")
        logger.info("   - System clock errors will trigger VPS restart")
        logger.info("   - Uses OVH API via health server /restart endpoint")
        
        # Send single startup notification to Telegram
        self.telegram_feedback.notify_system_status('started', f"Strategy: {ENTRY_STRATEGY}, V: {DEFAULT_VOLUME}")
        
        try:
            await self.client.run_until_disconnected()
        except KeyboardInterrupt:
            logger.info("Received interrupt signal")
        except Exception as e:
            error_msg = f"Unexpected error: {e}"
            logger.error(error_msg)
            
            # Check if it's a system clock error
            error_str = str(e).lower()
            if any(keyword in error_str for keyword in ['system clock', 'time offset', 'clock error', 'time synchronization']):
                logger.error("🕐 SYSTEM CLOCK ERROR in main loop - triggering restart")
                self.telegram_feedback.notify_error("system_clock_error", f"System clock error detected: {error_msg}. Restarting VPS automatically...")
                
                # Trigger restart
                try:
                    import threading
                    threading.Thread(
                        target=self._trigger_emergency_restart, 
                        daemon=True
                    ).start()
                except Exception as restart_err:
                    logger.error(f"Failed to trigger emergency restart: {restart_err}")
                    
            # Check if it's a Telegram protocol error
            elif any(keyword in error_str for keyword in ['constructor', 'tlobject', 'remaining bytes', 'protocol']):
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
    
    def _trigger_emergency_restart(self):
        """Emergency restart method for system clock errors"""
        try:
            logger.info("🚨 EMERGENCY RESTART - System clock error detected")
            
            # Use the health server's restart endpoint
            restart_url = "http://localhost:8080/restart"
            
            logger.info(f"🔄 Sending emergency restart request to {restart_url}")
            
            response = requests.post(restart_url, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                logger.info("✅ Emergency VPS restart initiated successfully!")
                logger.info(f"   Response: {result.get('message', 'No message')}")
            else:
                logger.error(f"❌ Emergency restart request failed: {response.status_code}")
                logger.error(f"   Response: {response.text}")
                
        except Exception as e:
            logger.error(f"❌ Failed to trigger emergency restart: {e}")


async def main():
    """Main entry point"""
    # Start main bot (health server starts automatically in TelegramMonitor.__init__)
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