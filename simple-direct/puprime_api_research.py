#!/usr/bin/env python3
"""
PUPrime API Research Tool
Checks if PUPrime offers WebAPI or REST API for trading
"""

import requests
import json
from urllib.parse import urljoin

def check_puprime_api():
    """Research PUPrime API availability"""
    print("🔍 Researching PUPrime API Options...")
    print("=" * 50)
    
    # Common API endpoint patterns to test
    base_urls = [
        "https://api.puprime.com/",
        "https://webapi.puprime.com/", 
        "https://rest.puprime.com/",
        "https://trading.puprime.com/api/",
        "https://puprime.com/api/",
        "https://mt5api.puprime.com/"
    ]
    
    api_endpoints = [
        "v1/",
        "api/v1/",
        "trading/",
        "quotes/",
        "symbols/",
        "account/",
        "orders/"
    ]
    
    print("📡 Testing common API endpoints...")
    
    found_apis = []
    
    for base_url in base_urls:
        try:
            # Test base URL
            response = requests.get(base_url, timeout=5)
            if response.status_code == 200:
                print(f"✅ Found endpoint: {base_url} (Status: {response.status_code})")
                found_apis.append(base_url)
                
                # Test for API documentation
                if any(keyword in response.text.lower() for keyword in ['api', 'documentation', 'swagger', 'openapi']):
                    print(f"   📚 Possible API documentation found!")
                    
        except requests.exceptions.RequestException:
            continue
    
    if not found_apis:
        print("❌ No obvious API endpoints found")
    
    return found_apis

def check_puprime_website():
    """Check PUPrime website for API documentation"""
    print("\n🌐 Checking PUPrime website for API info...")
    
    try:
        response = requests.get("https://www.puprime.com", timeout=10)
        if response.status_code == 200:
            content = response.text.lower()
            
            # Look for API-related keywords
            api_keywords = ['api', 'rest api', 'webapi', 'trading api', 'developer', 'integration']
            found_keywords = [kw for kw in api_keywords if kw in content]
            
            if found_keywords:
                print(f"✅ Found API-related content: {', '.join(found_keywords)}")
            else:
                print("❌ No API-related content found on main website")
                
        else:
            print(f"❌ Website not accessible (Status: {response.status_code})")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error accessing website: {e}")

def show_api_alternatives():
    """Show what to do if no API is found"""
    print("\n🔄 If PUPrime has no WebAPI:")
    print("=" * 35)
    
    print("1. 🍷 Use Wine + MT5 approach on Linux")
    print("   • Most reliable for MT5-only brokers")
    print("   • Costs $5-15/month on Linux VPS")
    
    print("\n2. 🔌 Switch to API-friendly broker:")
    print("   • Interactive Brokers (robust API)")
    print("   • Alpaca (modern REST API)")  
    print("   • OANDA (excellent API)")
    print("   • IG Markets (comprehensive API)")
    
    print("\n3. 📈 Use TradingView + Webhooks:")
    print("   • Create signals in TradingView")
    print("   • Send webhooks to your bot")
    print("   • Bot executes via MT5 Wine setup")

def generate_contact_script():
    """Generate script to contact PUPrime about API"""
    print("\n📧 Contact PUPrime About API:")
    print("=" * 35)
    
    contact_message = """
Subject: Trading API / REST API Availability

Dear PUPrime Support,

I am developing an automated trading system and would like to know:

1. Does PUPrime offer a REST API or WebAPI for trading?
2. Are there any developer documentation or API endpoints available?
3. Can I execute trades programmatically without MetaTrader 5 terminal?
4. What are the requirements for API access?

I am currently using MetaTrader 5 but would prefer a direct API connection 
for better integration with my trading algorithms.

Thank you for your assistance.

Best regards,
[Your Name]
    """
    
    print("📝 Email template:")
    print(contact_message)
    
    print("\n📞 Contact methods:")
    print("• Email: Check PUPrime website for support email")
    print("• Live chat: Visit https://www.puprime.com")
    print("• Phone: Check their contact page")

def main():
    """Main research function"""
    print("🔬 PUPrime API Research")
    print("Date: 2025-10-28")
    print("=" * 30)
    
    # Test for API endpoints
    found_apis = check_puprime_api()
    
    # Check website for API info
    check_puprime_website()
    
    # Show alternatives
    show_api_alternatives()
    
    # Provide contact template
    generate_contact_script()
    
    print(f"\n💡 Next Steps:")
    print(f"1. Contact PUPrime about API availability")
    print(f"2. If no API: Set up Linux VPS with Wine + MT5")
    print(f"3. If API exists: We'll build native Linux integration!")

if __name__ == "__main__":
    main()