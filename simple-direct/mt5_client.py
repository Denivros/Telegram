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
                    # Determine correct order type based on price relationship
                    if direction == 'buy':
                        if entry_price < current_ask:
                            # Buy below market = BUY LIMIT
                            order_type_mt5 = mt5.ORDER_TYPE_BUY_LIMIT
                            logger.info(f"   ✅ BUY LIMIT order {i} at {entry_price} (below market {current_ask})")
                        else:
                            # Buy above market = BUY STOP
                            order_type_mt5 = mt5.ORDER_TYPE_BUY_STOP
                            logger.info(f"   ✅ BUY STOP order {i} at {entry_price} (above market {current_ask})")
                    else:  # sell
                        if entry_price > current_bid:
                            # Sell above market = SELL LIMIT
                            order_type_mt5 = mt5.ORDER_TYPE_SELL_LIMIT
                            logger.info(f"   ✅ SELL LIMIT order {i} at {entry_price} (above market {current_bid})")
                        else:
                            # Sell below market = SELL STOP
                            order_type_mt5 = mt5.ORDER_TYPE_SELL_STOP
                            logger.info(f"   ✅ SELL STOP order {i} at {entry_price} (below market {current_bid})")
                    
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
                
                # Debug: Log the complete request before sending
                logger.info(f"   🔍 DEBUG - Order request details:")
                logger.info(f"      Symbol: {symbol}")
                logger.info(f"      Type: {order_type_mt5} ({'MARKET' if request['action'] == mt5.TRADE_ACTION_DEAL else 'LIMIT'})")
                logger.info(f"      Entry Price: {entry_price}")
                logger.info(f"      TP Price: {signal['take_profit']}")
                logger.info(f"      SL Price: {signal['stop_loss']}")
                logger.info(f"      Volume: {volume}")
                logger.info(f"      Current Bid: {current_bid}, Ask: {current_ask}")
                
                # Send order
                result = mt5.order_send(request)
                logger.info(f"   📤 Order send result: {result}")
                    
                if result is None:
                    logger.error(f"   ❌ Order {i} failed: mt5.order_send() returned None (connection issue?)")
                    results.append({
                        'entry_price': entry_price,
                        'volume': volume,
                        'error': "MT5 connection failed - order_send returned None",
                        'success': False
                    })
                elif result.retcode == mt5.TRADE_RETCODE_DONE:
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
                    # result is not None but failed - safe to access retcode/comment
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
                    'entry_type': 'dual',
                    'orders_placed': successful_orders,
                    'total_volume': total_volume,
                    'volume': total_volume,  # For backward compatibility
                    'entry_prices': entry_prices,
                    'results': results
                }
            elif successful_orders > 0:
                logger.warning(f"⚠️ PARTIAL SUCCESS: {successful_orders}/{entry_count} orders placed")
                return {
                    'success': True,
                    'multi_entry': True,
                    'entry_type': 'dual',
                    'entry_price': entry_prices[0] if entry_prices else 0,
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
                    'entry_type': 'dual',
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
                    
                    # RECALCULATE TP based on MARKET PRICE instead of range entry price
                    if tp_pips is not None:
                        if direction == 'buy':
                            market_tp_price = market_price + (tp_pips * pip_value)
                        else:  # sell
                            market_tp_price = market_price - (tp_pips * pip_value)
                        market_tp_price = round(market_tp_price, symbol_info.digits)
                        logger.info(f"   🎯 TP RECALCULATED for MARKET order:")
                        logger.info(f"      Original TP (from range): {tp_price} (based on {entry_price})")
                        logger.info(f"      New TP (from market): {market_tp_price} (based on {market_price})")
                        tp_price = market_tp_price
                    
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
                        "tp": tp_price,  # Now uses market-based TP calculation
                        "magic": MAGIC_NUMBER,
                        "comment": f"TG Market {tp_level}/5 {tp_pips if tp_pips else 'Signal'}p",
                        "type_filling": mt5.ORDER_FILLING_IOC,
                    }
                    logger.info(f"   ✅ {direction.upper()} MARKET order {i} (was limit at {entry_price})")
                else:
                    # Determine correct order type based on price relationship
                    if direction == 'buy':
                        if entry_price < current_ask:
                            # Buy below market = BUY LIMIT
                            order_type_mt5 = mt5.ORDER_TYPE_BUY_LIMIT
                            logger.info(f"   ✅ BUY LIMIT order {i} at {entry_price} (below market {current_ask})")
                        else:
                            # Buy above market = BUY STOP
                            order_type_mt5 = mt5.ORDER_TYPE_BUY_STOP
                            logger.info(f"   ✅ BUY STOP order {i} at {entry_price} (above market {current_ask})")
                    else:  # sell
                        if entry_price > current_bid:
                            # Sell above market = SELL LIMIT
                            order_type_mt5 = mt5.ORDER_TYPE_SELL_LIMIT
                            logger.info(f"   ✅ SELL LIMIT order {i} at {entry_price} (above market {current_bid})")
                        else:
                            # Sell below market = SELL STOP
                            order_type_mt5 = mt5.ORDER_TYPE_SELL_STOP
                            logger.info(f"   ✅ SELL STOP order {i} at {entry_price} (below market {current_bid})")
                    
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
                
                if result is None:
                    logger.error(f"   ❌ {tp_label} order failed: mt5.order_send() returned None (connection issue?)")
                    results.append({
                        'entry_price': entry_price,
                        'tp_price': tp_price,
                        'tp_pips': tp_pips,
                        'tp_level': tp_level,
                        'volume': volume,
                        'error': "MT5 connection failed - order_send returned None",
                        'success': False
                    })
                elif result.retcode == mt5.TRADE_RETCODE_DONE:
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
                    # result is not None but failed - safe to access retcode/comment
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
                    'volume': total_volume,  # For backward compatibility
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
                    'entry_price': entry_prices[0] if entry_prices else 0,
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