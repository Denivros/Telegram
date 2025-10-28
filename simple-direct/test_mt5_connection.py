#!/usr/bin/env python3
"""
Test MT5 VPS Connection
This script tests if we can connect to your MT5 VPS
"""

import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_mt5_import():
    """Test if MT5 library can be imported"""
    try:
        import MetaTrader5 as mt5
        print("✅ MetaTrader5 library imported successfully")
        return mt5
    except ImportError as e:
        print(f"❌ MetaTrader5 library not available: {e}")
        print("\n🔍 Platform Analysis:")
        print(f"   - Operating System: {sys.platform}")
        print(f"   - Python Version: {sys.version}")
        
        if sys.platform == "darwin":  # macOS
            print("\n💡 Solution Options for macOS:")
            print("   1. Use Windows VM with MT5 + Python")
            print("   2. Use MT5 WebAPI (if broker supports)")
            print("   3. Run Python script on Windows VPS")
            print("   4. Use alternative trading libraries (e.g., cTrader, TradingView)")
        
        return None

def test_mt5_connection(mt5):
    """Test connection to MT5 VPS"""
    if not mt5:
        return False
        
    try:
        # Get credentials from environment
        login = int(os.getenv('MT5_LOGIN', '0'))
        password = os.getenv('MT5_PASSWORD', '')
        server = os.getenv('MT5_SERVER', '')
        
        if not all([login, password, server]):
            print("❌ Missing MT5 credentials in .env file")
            print("   Required: MT5_LOGIN, MT5_PASSWORD, MT5_SERVER")
            return False
        
        print(f"\n🔌 Attempting connection to MT5 VPS...")
        print(f"   Server: {server}")
        print(f"   Login: {login}")
        
        # Initialize MT5
        if not mt5.initialize():
            print(f"❌ MT5 initialization failed: {mt5.last_error()}")
            return False
        
        # Login to VPS
        if not mt5.login(login, password=password, server=server):
            error = mt5.last_error()
            print(f"❌ MT5 VPS login failed: {error}")
            print("\n🔧 Troubleshooting:")
            print("   1. Check if login credentials are correct")
            print("   2. Verify server name with your broker")
            print("   3. Ensure MT5 account is active")
            print("   4. Check if VPS allows remote connections")
            return False
        
        # Get account info
        account_info = mt5.account_info()
        if account_info is None:
            print("❌ Failed to get account information")
            return False
        
        print("✅ Successfully connected to MT5 VPS!")
        print(f"   Account: {account_info.login}")
        print(f"   Balance: {account_info.balance} {account_info.currency}")
        print(f"   Broker: {account_info.company}")
        print(f"   Server: {account_info.server}")
        
        # Test basic market data
        symbols = mt5.symbols_get()
        if symbols:
            print(f"   Available symbols: {len(symbols)} pairs")
        
        return True
        
    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        return False
    finally:
        if mt5:
            mt5.shutdown()

def show_platform_specific_guidance():
    """Show guidance based on current platform"""
    if sys.platform == "darwin":  # macOS
        print("\n🍎 macOS Deployment Options:")
        print("\n1. 🖥️  Windows VM Solution:")
        print("   - Install Parallels/VMware with Windows")
        print("   - Install MT5 + Python in Windows VM")
        print("   - Run the trading script from VM")
        
        print("\n2. ☁️  Cloud Windows VPS:")
        print("   - Rent Windows VPS (AWS/Azure/DigitalOcean)")
        print("   - Install MT5 + Python on cloud VPS")
        print("   - Run script 24/7 on cloud")
        
        print("\n3. 🔗 WebAPI Alternative:")
        print("   - Check if your broker offers WebAPI")
        print("   - Use REST API instead of MT5 library")
        print("   - Works natively on macOS")
        
        print("\n4. 🐳 Docker Solution:")
        print("   - Use Windows container with MT5")
        print("   - Run via Docker Desktop on macOS")

def main():
    """Main test function"""
    print("🧪 MT5 VPS Connection Test")
    print("=" * 50)
    
    # Test 1: Import MT5 library
    mt5 = test_mt5_import()
    
    # Test 2: Check environment variables
    print(f"\n📋 Environment Check:")
    required_vars = ['MT5_LOGIN', 'MT5_PASSWORD', 'MT5_SERVER']
    all_set = True
    
    for var in required_vars:
        value = os.getenv(var)
        if value:
            if var == 'MT5_PASSWORD':
                print(f"   {var}: {'*' * len(value)}")  # Hide password
            else:
                print(f"   {var}: {value}")
        else:
            print(f"   {var}: ❌ Not set")
            all_set = False
    
    if not all_set:
        print("\n📝 Please update your .env file with MT5 credentials")
        return
    
    # Test 3: Attempt connection (if MT5 available)
    if mt5:
        success = test_mt5_connection(mt5)
        if success:
            print("\n🎉 Connection test completed successfully!")
            print("Your setup is ready for automated trading.")
        else:
            print("\n❌ Connection test failed.")
    else:
        show_platform_specific_guidance()

if __name__ == "__main__":
    main()