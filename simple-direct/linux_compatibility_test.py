#!/usr/bin/env python3
"""
Linux Compatibility Test for MT5
Tests if MetaTrader5 library works on Linux and shows deployment options
"""

import os
import sys
import platform
from datetime import datetime

def test_mt5_on_linux():
    """Test MT5 library compatibility on Linux"""
    print(f"🐧 Linux Platform Analysis:")
    print(f"   OS: {platform.system()} {platform.release()}")
    print(f"   Distribution: {platform.platform()}")
    print(f"   Architecture: {platform.machine()}")
    print(f"   Python: {sys.version.split()[0]}")
    
    try:
        import MetaTrader5 as mt5
        print(f"✅ MetaTrader5 library imported successfully on Linux!")
        return mt5
    except ImportError as e:
        print(f"❌ MetaTrader5 library not available on Linux: {e}")
        return None

def show_linux_solutions():
    """Show Linux-specific deployment solutions"""
    print(f"\n🚀 Linux Deployment Solutions:")
    print(f"=" * 50)
    
    print(f"\n1. 🍷 Wine + MetaTrader5 (Most Common)")
    print(f"   • Install Wine on Linux")
    print(f"   • Install Windows MT5 terminal via Wine")
    print(f"   • Install Python Windows version via Wine")
    print(f"   • Install MetaTrader5 library in Wine Python")
    print(f"   • Pro: Full MT5 functionality on Linux")
    print(f"   • Con: Complex setup, potential stability issues")
    
    print(f"\n2. 🖥️  Linux VPS with Wine (Recommended)")
    print(f"   • Rent Linux VPS (Ubuntu/Debian)")
    print(f"   • Much cheaper than Windows VPS (~$5-15/month)")
    print(f"   • Install Wine + MT5 + Python")
    print(f"   • Deploy your trading bot")
    print(f"   • Pro: Cost-effective, always running")
    print(f"   • Con: Wine setup complexity")
    
    print(f"\n3. 🐳 Docker with Wine")
    print(f"   • Use pre-built Docker images with Wine + MT5")
    print(f"   • Run containers on any Linux system")
    print(f"   • Easier deployment and scaling")
    print(f"   • Pro: Portable, reproducible")
    print(f"   • Con: Docker overhead")
    
    print(f"\n4. 🔄 MetaTrader5 WebTerminal + Selenium")
    print(f"   • Use MT5 WebTerminal in browser")
    print(f"   • Control via Selenium WebDriver")
    print(f"   • Works natively on Linux")
    print(f"   • Pro: No Wine needed")
    print(f"   • Con: Limited API, browser dependency")

def wine_setup_guide():
    """Show step-by-step Wine setup for MT5"""
    print(f"\n📖 Wine + MT5 Setup Guide for Linux:")
    print(f"=" * 40)
    
    print(f"\n📦 1. Install Wine:")
    print(f"   Ubuntu/Debian:")
    print(f"   sudo apt update")
    print(f"   sudo apt install wine winetricks")
    print(f"   ")
    print(f"   CentOS/RHEL:")
    print(f"   sudo yum install epel-release")
    print(f"   sudo yum install wine")
    
    print(f"\n🍷 2. Configure Wine:")
    print(f"   winecfg  # Set to Windows 10 mode")
    print(f"   winetricks corefonts vcrun2019")
    
    print(f"\n💾 3. Install MetaTrader5:")
    print(f"   wget https://download.mql5.com/cdn/web/metaquotes.software.corp/mt5/mt5setup.exe")
    print(f"   wine mt5setup.exe")
    
    print(f"\n🐍 4. Install Python in Wine:")
    print(f"   wget https://www.python.org/ftp/python/3.11.0/python-3.11.0-amd64.exe")
    print(f"   wine python-3.11.0-amd64.exe")
    
    print(f"\n📦 5. Install Python packages:")
    print(f"   wine python -m pip install MetaTrader5 telethon requests python-dotenv")

def show_linux_advantages():
    """Show why Linux might be better than Windows for trading"""
    print(f"\n✨ Why Linux for Trading Bots:")
    print(f"=" * 35)
    
    print(f"\n💰 Cost Benefits:")
    print(f"   • Linux VPS: $5-15/month")
    print(f"   • Windows VPS: $15-50/month")
    print(f"   • 50-70% cost savings!")
    
    print(f"\n⚡ Performance Benefits:")
    print(f"   • Lower resource usage")
    print(f"   • Better stability for 24/7 operation")
    print(f"   • No Windows updates disrupting trading")
    
    print(f"\n🔧 Technical Benefits:")
    print(f"   • Better SSH access and management")
    print(f"   • Easier automation and scripting")
    print(f"   • More granular control")

def check_alternatives():
    """Check for Linux-native trading alternatives"""
    print(f"\n🔍 Linux-Native Trading Alternatives:")
    print(f"=" * 45)
    
    print(f"\n1. 📡 FIX Protocol Libraries:")
    print(f"   • quickfix-python")
    print(f"   • Direct broker connection")
    print(f"   • Professional grade")
    
    print(f"\n2. 🌐 Broker WebAPIs:")
    print(f"   • Interactive Brokers API")
    print(f"   • Alpaca API")
    print(f"   • OANDA API")
    print(f"   • Check if PUPrime offers REST API")
    
    print(f"\n3. 🔌 cTrader (if broker supports):")
    print(f"   • cTrader has Linux-compatible APIs")
    print(f"   • Alternative to MetaTrader")
    
    print(f"\n4. 📈 TradingView Pine Script:")
    print(f"   • Web-based, platform independent")
    print(f"   • Can send webhooks to your bot")

def main():
    """Main test function"""
    print(f"🐧 Linux MT5 Compatibility Test")
    print(f"=" * 40)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test MT5 import (will likely fail on Linux without Wine)
    mt5 = test_mt5_on_linux()
    
    if not mt5:
        show_linux_solutions()
        wine_setup_guide()
        show_linux_advantages()
        check_alternatives()
        
        print(f"\n🎯 Recommended Linux Approach:")
        print(f"=" * 35)
        print(f"1. 💡 Try Wine + MT5 setup first")
        print(f"2. 🐳 Use Docker if Wine is complex")  
        print(f"3. ☁️  Deploy to cheap Linux VPS")
        print(f"4. 🔍 Check PUPrime WebAPI as backup")
        
    else:
        print(f"\n🎉 Excellent! MT5 works natively on this Linux system")

if __name__ == "__main__":
    main()