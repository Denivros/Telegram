"""
MT5 Trading Client Module
Contains MT5TradingClient class for direct MetaTrader5 trading operations.
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional
from config import *

# Try to import MetaTrader5 (available on Windows/Wine only)
try:
    import metatrader5 as mt5
    MT5_AVAILABLE = True
except ImportError:
    MT5_AVAILABLE = False
    mt5 = None

logger = logging.getLogger(__name__)


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
                        
        elif ENTRY_STRATEGY == 'dual_entry':
            # Calculate dual entry points at 1/3 and 2/3 of the range
            range_span = range_end - range_start
            entry_1 = range_start + (range_span / 3)  # 1/3 point
            entry_2 = range_start + (2 * range_span / 3)  # 2/3 point
            
            logger.info(f"   📍 DUAL_ENTRY Strategy:")
            logger.info(f"      Range: {range_start} - {range_end} (span: {range_span})")
            logger.info(f"      Entry 1 (1/3): {entry_1}")
            logger.info(f"      Entry 2 (2/3): {entry_2}")
            logger.info(f"      Volume each: 0.07")
            
            # Return both entry points for dual execution
            entry_price = entry_1  # Primary entry for main logic
            
        elif ENTRY_STRATEGY == 'triple_entry':
            # Calculate triple entry points at begin, mid, and end of the range
            range_span = range_end - range_start
            entry_begin = range_start                         # Begin of range
            entry_mid = range_start + (range_span / 2)       # Mid of range  
            entry_end = range_end                             # End of range
            
            logger.info(f"   📍 TRIPLE_ENTRY Strategy ({direction.upper()}):")
            logger.info(f"      Range: {range_start} - {range_end} (span: {range_span})")
            logger.info(f"      Begin: {entry_begin} - Mid: {entry_mid} - End: {entry_end}")
            
            if direction == 'buy':
                logger.info(f"      BUY Order: Begin(4x) → Mid(2x) → End(2x) LAST")
                logger.info(f"      Entry 1: {entry_begin} - Volume: {2 * DEFAULT_VOLUME_MULTI}")
                logger.info(f"      Entry 2: {entry_mid} - Volume: {4 * DEFAULT_VOLUME_MULTI}")
                logger.info(f"      Entry 3: {entry_end} - Volume: {3 * DEFAULT_VOLUME_MULTI} ← LAST")
                entry_price = entry_begin  # Primary entry for main logic
            else:
                logger.info(f"      SELL Order: End(2x) → Mid(3x) → Begin(4x) LAST")
                logger.info(f"      Entry 1: {entry_end} - Volume: {2 * DEFAULT_VOLUME_MULTI}")
                logger.info(f"      Entry 2: {entry_mid} - Volume: {3 * DEFAULT_VOLUME_MULTI}")
                logger.info(f"      Entry 3: {entry_begin} - Volume: {4 * DEFAULT_VOLUME_MULTI} ← LAST")
                entry_price = entry_end  # Primary entry for main logic
            
            logger.info(f"      Total Volume: {9 * DEFAULT_VOLUME_MULTI}")
            
        elif ENTRY_STRATEGY == 'multi_tp_entry':
            # Multi-TP strategy uses adaptive entry but with multiple TP levels
            if direction == 'buy':
                if current_price < range_start:
                    entry_price = range_start
                    logger.info(f"   📍 MULTI_TP_ENTRY Strategy (BUY): Price {current_price} < range_start {range_start} → Entry = {entry_price}")
                elif current_price > range_end:
                    symbol_info = mt5.symbol_info(symbol)
                    pip_value = 10 ** (-symbol_info.digits) if symbol_info else 0.0001
                    entry_price = current_price + (2 * pip_value)
                    logger.info(f"   📍 MULTI_TP_ENTRY Strategy (BUY): Price {current_price} > range_end {range_end} → Entry = {entry_price} (+2 pips)")
                else:
                    entry_price = current_price
                    logger.info(f"   📍 MULTI_TP_ENTRY Strategy (BUY): Price {current_price} in range → Entry = {entry_price}")
            else:  # sell
                if current_price < range_start:
                    entry_price = range_start
                    logger.info(f"   📍 MULTI_TP_ENTRY Strategy (SELL): Price {current_price} < range_start {range_start} → Entry = {entry_price}")
                elif current_price > range_end:
                    symbol_info = mt5.symbol_info(symbol)
                    pip_value = 10 ** (-symbol_info.digits) if symbol_info else 0.0001
                    entry_price = current_price - (2 * pip_value)
                    logger.info(f"   📍 MULTI_TP_ENTRY Strategy (SELL): Price {current_price} > range_end {range_end} → Entry = {entry_price} (-2 pips)")
                else:
                    entry_price = current_price
                    logger.info(f"   📍 MULTI_TP_ENTRY Strategy (SELL): Price {current_price} in range → Entry = {entry_price}")
            
            logger.info(f"   📊 Will open 5 positions with TP levels: {MULTI_TP_PIPS} pips + Signal TP")
            logger.info(f"   📊 Volumes: {MULTI_TP_VOLUMES}")
            total_volume = sum(MULTI_TP_VOLUMES)
            logger.info(f"   📊 Total Volume: {total_volume}")
            
        elif ENTRY_STRATEGY == 'multi_position_entry':
            # Multi-Position strategy: Fixed entry points at range boundaries
            # 4 positions at range END, 3 at MIDDLE, 2 at START
            entry_price = current_price  # Use current price as reference
            range_middle = range_start + ((range_end - range_start) / 2)
            
            logger.info(f"   📍 MULTI_POSITION_ENTRY Strategy ({direction.upper()}):")
            logger.info(f"   📊 Will open {NUMBER_POSITIONS_MULTI} positions with BOUNDARY-based distribution")
            logger.info(f"   📊 Range: {range_start} (START) - {range_middle} (MIDDLE) - {range_end} (END)")
            logger.info(f"   📊 Logic: 4 positions at boundary closest to price + 3 at MIDDLE + 2 at other boundary")
            logger.info(f"   📊 Standard volume: {POSITION_VOLUME_MULTI}, First position at closest boundary: {2 * POSITION_VOLUME_MULTI} (DOUBLE)")
            logger.info(f"   📊 Total Volume: {(NUMBER_POSITIONS_MULTI - 1) * POSITION_VOLUME_MULTI + (2 * POSITION_VOLUME_MULTI)}")
            logger.info(f"   📊 TP levels: 200, 400, 600, 800 pips per zone from entry")
            
        else:
            entry_price = (range_start + range_end) / 2
        
        # Get symbol info for normalization and prepare dual entry data if needed
        symbol_info = mt5.symbol_info(symbol)
        if symbol_info:
            digits = symbol_info.digits
            entry_price = round(entry_price, digits)
        
        # Prepare multi-entry data for dual_entry and triple_entry strategies
        multi_entries = None
        if ENTRY_STRATEGY == 'dual_entry':
            range_span = range_end - range_start
            entry_1 = round(range_start + (range_span / 3), digits) if symbol_info else range_start + (range_span / 3)
            entry_2 = round(range_start + (2 * range_span / 3), digits) if symbol_info else range_start + (2 * range_span / 3)
            multi_entries = [
                {'price': entry_1, 'volume': 0.07},
                {'price': entry_2, 'volume': 0.07}
            ]
        elif ENTRY_STRATEGY == 'triple_entry':
            range_span = range_end - range_start
            entry_begin = round(range_start, digits) if symbol_info else range_start                    # Begin of range
            entry_mid = round(range_start + (range_span / 2), digits) if symbol_info else range_start + (range_span / 2)  # Mid of range
            entry_end = round(range_end, digits) if symbol_info else range_end                        # End of range
            
            # Order entries based on direction - 2x volume always enters LAST
            if direction == 'buy':
                # BUY: Price moves up, so 2x volume enters at highest level (end) = LAST
                multi_entries = [
                    {'price': entry_begin, 'volume': 3 * DEFAULT_VOLUME_MULTI},  # First: 3x at begin (lowest)
                    {'price': entry_mid, 'volume': 4 * DEFAULT_VOLUME_MULTI},    # Second: 4x at mid
                    {'price': entry_end, 'volume': 2 * DEFAULT_VOLUME_MULTI}     # LAST: 2x at end (highest)
                ]
            else:  # sell
                # SELL: Price moves down, so 2x volume enters at lowest level (begin) = LAST
                multi_entries = [
                    {'price': entry_end, 'volume': 3 * DEFAULT_VOLUME_MULTI},    # First: 3x at end (highest)
                    {'price': entry_mid, 'volume': 4 * DEFAULT_VOLUME_MULTI},    # Second: 4x at mid
                    {'price': entry_begin, 'volume': 2 * DEFAULT_VOLUME_MULTI}   # LAST: 2x at begin (lowest)
                ]
        elif ENTRY_STRATEGY == 'multi_tp_entry':
            # Multi-TP strategy: 5 positions with different TP levels
            # All positions use same entry price but different TPs and volumes
            multi_entries = []
            for i, (tp_pips, volume) in enumerate(zip(MULTI_TP_PIPS + [None], MULTI_TP_VOLUMES), 1):
                multi_entries.append({
                    'price': entry_price,
                    'volume': volume,
                    'tp_pips': tp_pips,  # None for TP5 (uses signal TP)
                    'tp_level': i  # TP1, TP2, TP3, TP4, TP5
                })
        elif ENTRY_STRATEGY == 'multi_position_entry':
            # Multi-Position strategy: Fixed entry points at range boundaries
            # BUY: 4 at END, 3 at MIDDLE, 2 at START | SELL: 2 at END, 3 at MIDDLE, 4 at START
            # Each with TP starting from 200, 400, 600, 800 pips per zone
            range_span = range_end - range_start
            range_middle = range_start + (range_span / 2)
            
            # Create positions at fixed levels (distribution depends on current price position)
            positions = []
            
            # Determine which range boundary (START or END) is closest to current price for 4-position placement
            # MIDDLE is always gets 3 positions, only START vs END compete for the 4 positions
            if current_price is None:
                # Fallback to START if no current price
                closest_to_price = 'start'
                logger.info(f"   ⚠️  No current price available, defaulting 4 positions to START")
            else:
                # Calculate distances to START and END only (skip MIDDLE)
                distance_to_start = abs(current_price - range_start)
                distance_to_end = abs(current_price - range_end)
                
                # Find which boundary (START or END) is closest
                if distance_to_start <= distance_to_end:
                    closest_to_price = 'start'
                else:
                    closest_to_price = 'end'
                
                logger.info(f"   📍 BOUNDARY-BASED DISTRIBUTION LOGIC:")
                logger.info(f"      Current Price: {current_price}")
                logger.info(f"      Range: {range_start} (START) - {range_middle} (MIDDLE) - {range_end} (END)")
                logger.info(f"      Distances: START={distance_to_start:.2f}, END={distance_to_end:.2f}")
                logger.info(f"      ✅ 4 positions will be placed at {closest_to_price.upper()} (closest boundary to current price)")
                logger.info(f"      📝 MIDDLE always gets 3 positions")
            
            # Always place 4 positions at the boundary (START or END) closest to current price
            # MIDDLE always gets 3 positions, remaining boundary gets 2 positions
            
            if closest_to_price == 'start':
                logger.info(f"      📊 Distribution: 4 at START (1 double volume) + 3 at MIDDLE + 2 at END")
                
                # 4 positions at range START (closest boundary to current price)
                # First position gets double volume, others get standard volume
                for i in range(4):
                    volume = (2 * POSITION_VOLUME_MULTI) if i == 0 else POSITION_VOLUME_MULTI
                    positions.append({
                        'price': range_start,
                        'zone': 'start',
                        'volume': volume,
                        'position_number': i + 1
                    })
                
                # 3 positions at range MIDDLE (always gets 3)
                for i in range(3):
                    positions.append({
                        'price': range_middle,
                        'zone': 'middle',
                        'volume': POSITION_VOLUME_MULTI,
                        'position_number': i + 5
                    })
                
                # 2 positions at range END (remaining boundary)
                for i in range(2):
                    positions.append({
                        'price': range_end,
                        'zone': 'end',
                        'volume': POSITION_VOLUME_MULTI,
                        'position_number': i + 8
                    })
                    
            else:  # closest_to_price == 'end'
                logger.info(f"      📊 Distribution: 2 at START + 3 at MIDDLE + 4 at END (1 double volume)")
                
                # 2 positions at range START (remaining boundary)
                for i in range(2):
                    positions.append({
                        'price': range_start,
                        'zone': 'start',
                        'volume': POSITION_VOLUME_MULTI,
                        'position_number': i + 1
                    })
                
                # 3 positions at range MIDDLE (always gets 3)
                for i in range(3):
                    positions.append({
                        'price': range_middle,
                        'zone': 'middle',
                        'volume': POSITION_VOLUME_MULTI,
                        'position_number': i + 3
                    })
                
                # 4 positions at range END (closest boundary to current price)
                # First position gets double volume, others get standard volume
                for i in range(4):
                    volume = (2 * POSITION_VOLUME_MULTI) if i == 0 else POSITION_VOLUME_MULTI
                    positions.append({
                        'price': range_end,
                        'zone': 'end',
                        'volume': volume,
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
                pos_volume = pos['volume']  # Use volume from position (may be double for first position)
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
                    volume_label = "DOUBLE" if pos_volume == (2 * POSITION_VOLUME_MULTI) else "standard"
                    logger.info(f"      Position {i+1}: zone='{pos['zone']}', zone_index={zone_index}, tp_levels={zone_tp_levels}, volume={pos_volume} ({volume_label})")
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
                    volume_label = "DOUBLE" if pos_volume == (2 * POSITION_VOLUME_MULTI) else "standard"
                    logger.info(f"      Position {i+1}: zone='{pos['zone']}', zone_index={zone_index}, tp_levels={zone_tp_levels}, volume={pos_volume} ({volume_label})")
                
                tp_pips = zone_tp_levels[zone_index] if zone_index < len(zone_tp_levels) else zone_tp_levels[-1]
                
                multi_entries.append({
                    'price': pos_price,
                    'volume': pos_volume,  # Use actual position volume (may be double)
                    'tp_pips': tp_pips,  # Grouped TP: range_end(200,400,600,800), range_middle(200,400,600), range_start(200,400)
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
                    logger.info(f"   Placing {NUMBER_POSITIONS_MULTI} orders with DYNAMIC distribution, total volume: {total_vol}")
                    logger.info(f"   Distribution: Closer to current price gets more positions (4/3/2 pattern)")
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
            logger.info(f"   Total Volume: {total_volume}")
            
            for i, entry in enumerate(multi_entries, 1):
                logger.info(f"   Entry {i}/{entry_count}: {entry['price']} - Volume: {entry['volume']}")
            
            results = []
            successful_orders = 0
            
            # Execute all orders
            for i, entry in enumerate(multi_entries, 1):
                entry_price = entry['price']
                volume = entry['volume']
                
                logger.info(f"\n🔄 PLACING ORDER {i}/{entry_count}:")
                logger.info(f"   Entry Price: {entry_price}")
                logger.info(f"   Volume: {volume}")
                
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
            logger.info(f"   Total Volume: {total_volume}")
            
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
                logger.info(f"   Volume: {volume}")
                
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