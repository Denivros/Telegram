#!/usr/bin/env python3
"""
Test script to find available gold symbols on MT5
"""

import MetaTrader5 as mt5

# Initialize connection to MT5
if not mt5.initialize():
    print("Failed to initialize MT5")
    exit(1)

print("Connected to MT5")
print(f"Account: {mt5.account_info().login}")

# Get all symbols
symbols = mt5.symbols_get()
if symbols:
    print(f"\nTotal symbols available: {len(symbols)}")
    
    # Find gold-related symbols
    gold_symbols = []
    for symbol in symbols:
        if any(keyword in symbol.name.upper() for keyword in ['XAU', 'GOLD']):
            gold_symbols.append(symbol.name)
    
    if gold_symbols:
        print(f"\nFound {len(gold_symbols)} gold-related symbols:")
        for symbol_name in gold_symbols:
            # Try to get market info
            symbol_info = mt5.symbol_info(symbol_name)
            tick = mt5.symbol_info_tick(symbol_name)
            
            if symbol_info and tick:
                print(f"✅ {symbol_name}: Bid={tick.bid}, Ask={tick.ask}")
            else:
                print(f"❌ {symbol_name}: No price data")
    else:
        print("\n❌ No gold symbols found!")
        
    # Also check some common forex pairs to make sure MT5 is working
    print("\nTesting common forex pairs:")
    test_pairs = ['EURUSD', 'GBPUSD', 'USDJPY']
    for pair in test_pairs:
        tick = mt5.symbol_info_tick(pair)
        if tick:
            print(f"✅ {pair}: Bid={tick.bid}, Ask={tick.ask}")
        else:
            print(f"❌ {pair}: No price data")

else:
    print("No symbols retrieved")

# Cleanup
mt5.shutdown()