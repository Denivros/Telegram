#!/usr/bin/env python3
"""
Simple MT5 Platform Test
Tests MT5 library availability and shows deployment options for macOS
"""

import os
import sys
from datetime import datetime

def test_mt5_import():
    """Test if MT5 library can be imported"""
    try:
        import MetaTrader5 as mt5
        print("✅ MetaTrader5 library imported successfully")
        print(f"   Library version: {mt5.__version__}")
        return mt5
    except ImportError as e:
        print(f"❌ MetaTrader5 library not available: {e}")
        print(f"\n🔍 Platform Analysis:")
        print(f"   Operating System: {sys.platform}")
        print(f"   Python Version: {sys.version.split()[0]}")
        
        if sys.platform == "darwin":  # macOS
            print(f"\n📱 Current Platform: macOS")
            print(f"   The MetaTrader5 Python library only works on Windows")
            print(f"   Your MT5 VPS runs Windows, but we're on macOS")
        
        return None

def show_deployment_solutions():
    """Show practical deployment solutions for macOS users"""
    print(f"\n🚀 Deployment Solutions for macOS:")
    print(f"=" * 50)
    
    print(f"\n1. 🖥️  Windows VM on Mac (Recommended for Development)")
    print(f"   • Install Parallels Desktop or VMware Fusion")
    print(f"   • Create Windows 10/11 VM")
    print(f"   • Install Python + MetaTrader5 library in VM")
    print(f"   • Run your trading bot from Windows VM")
    print(f"   • Pro: Full control, can test locally")
    print(f"   • Con: Uses Mac resources")
    
    print(f"\n2. ☁️  Cloud Windows VPS (Recommended for Production)")
    print(f"   • Rent Windows VPS (AWS EC2, Azure, DigitalOcean)")
    print(f"   • Install Python + dependencies on VPS")
    print(f"   • Deploy your script to cloud VPS")
    print(f"   • Run 24/7 without Mac being on")
    print(f"   • Pro: Always running, professional setup")
    print(f"   • Con: Monthly cost (~$10-30)")
    
    print(f"\n3. 🔄 WebAPI Alternative (If Available)")
    print(f"   • Check if PUPrime offers REST API")
    print(f"   • Use HTTP requests instead of MT5 library")
    print(f"   • Works natively on macOS")
    print(f"   • Pro: No Windows needed")
    print(f"   • Con: Limited broker support")
    
    print(f"\n4. 🐳 Docker + Wine (Advanced)")
    print(f"   • Use Wine to run Windows MT5 in container")
    print(f"   • Complex setup, may have stability issues")
    print(f"   • Not recommended for production")

def check_env_file():
    """Check if .env file exists and has MT5 credentials"""
    if os.path.exists('.env'):
        print(f"\n📋 Environment File Check:")
        with open('.env', 'r') as f:
            content = f.read()
            
        if 'MT5_LOGIN=' in content and 'PUPrime-Demo' in content:
            print(f"   ✅ .env file found with MT5 credentials")
            print(f"   ✅ Broker: PUPrime-Demo")
            print(f"   ✅ Configuration ready for Windows deployment")
        else:
            print(f"   ❌ Missing MT5 credentials in .env")
    else:
        print(f"\n📋 Environment File: ❌ .env not found")

def show_next_steps():
    """Show immediate next steps"""
    print(f"\n🎯 Immediate Next Steps:")
    print(f"=" * 30)
    print(f"\nFor Quick Testing:")
    print(f"   1. Set up Windows VM (Parallels/VMware)")
    print(f"   2. Copy this project folder to Windows VM")
    print(f"   3. Install Python + pip install MetaTrader5")
    print(f"   4. Test connection with your demo account")
    
    print(f"\nFor Production Deployment:")
    print(f"   1. Rent Windows VPS from AWS/Azure")
    print(f"   2. Install Python + MetaTrader5 library")
    print(f"   3. Upload your project files")
    print(f"   4. Run trading bot 24/7 on cloud")
    
    print(f"\nWould you like help with:")
    print(f"   • Setting up Windows VM?")
    print(f"   • Choosing cloud VPS provider?")
    print(f"   • Checking if PUPrime has WebAPI?")

def main():
    """Main test function"""
    print(f"🧪 MT5 Platform Compatibility Test")
    print(f"=" * 40)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test MT5 import
    mt5 = test_mt5_import()
    
    # Check environment setup
    check_env_file()
    
    # Show solutions if MT5 not available
    if not mt5:
        show_deployment_solutions()
        show_next_steps()
    else:
        print(f"\n🎉 Great! MT5 library is available on this system")
        print(f"You can proceed with testing the VPS connection")

if __name__ == "__main__":
    main()