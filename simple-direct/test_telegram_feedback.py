#!/usr/bin/env python3
"""
Test script for Telegram Feedback Webhook
Tests the N8N webhook endpoint for sending feedback messages to Telegram
"""

import os
import sys
import requests
import json
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
N8N_TELEGRAM_FEEDBACK = os.getenv('N8N_TELEGRAM_FEEDBACK', 'https://n8n.srv881084.hstgr.cloud/webhook/91126b9d-bd23-4e92-8891-5bfb217455c7')

def test_webhook_connection():
    """Test basic webhook connectivity"""
    print("🔗 Testing Telegram Feedback Webhook Connection...")
    print(f"URL: {N8N_TELEGRAM_FEEDBACK}")
    
    try:
        # Simple test payload
        test_payload = {
            'message': '🧪 **WEBHOOK CONNECTION TEST**\n\nThis is a test message from the trading bot setup.\nIf you see this, the webhook is working correctly!',
            'timestamp': datetime.now().isoformat(),
            'data': {
                'test': True,
                'source': 'webhook_test_script'
            },
            'source': 'mt5_trading_bot_test'
        }
        
        response = requests.post(
            N8N_TELEGRAM_FEEDBACK,
            json=test_payload,
            timeout=10,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"Response Status: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.text:
            print(f"Response Body: {response.text}")
        
        if response.status_code == 200:
            print("✅ Webhook test successful!")
            return True
        else:
            print(f"❌ Webhook test failed with status {response.status_code}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Webhook test failed: Request timeout")
        return False
    except requests.exceptions.ConnectionError:
        print("❌ Webhook test failed: Connection error")
        return False
    except Exception as e:
        print(f"❌ Webhook test failed: {e}")
        return False

def test_trading_signals():
    """Test trading signal notifications"""
    print("\n📊 Testing Trading Signal Notifications...")
    
    # Test signal received notification
    signal_data = {
        'symbol': 'EURUSD',
        'direction': 'buy',
        'range_start': 1.0850,
        'range_end': 1.0870,
        'stop_loss': 1.0800,
        'take_profit': 1.0950
    }
    
    test_cases = [
        {
            'name': 'Signal Received',
            'message': f"📊 **NEW SIGNAL DETECTED - TEST**\n\n**Symbol:** {signal_data['symbol']}\n**Direction:** {signal_data['direction'].upper()}\n**Range:** {signal_data['range_start']} - {signal_data['range_end']}\n**Stop Loss:** {signal_data['stop_loss']}\n**Take Profit:** {signal_data['take_profit']}\n**Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            'data': signal_data
        },
        {
            'name': 'Trade Executed',
            'message': f"✅ **TRADE EXECUTED SUCCESSFULLY - TEST**\n\n**Symbol:** {signal_data['symbol']}\n**Direction:** {signal_data['direction'].upper()}\n**Entry Price:** 1.0860\n**Volume:** 0.01\n**Stop Loss:** {signal_data['stop_loss']}\n**Take Profit:** {signal_data['take_profit']}\n**Order ID:** 12345\n**Execution Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            'data': {'signal': signal_data, 'result': {'success': True, 'entry_price': 1.0860, 'volume': 0.01, 'order_id': 12345}}
        },
        {
            'name': 'System Started',
            'message': f"🚀 **TRADING BOT STARTED - TEST**\n\n**Status:** Online and monitoring\n**Group ID:** 4867740501\n**MT5 Connection:** ✅ Connected\n**Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            'data': {'status': 'started', 'test': True}
        },
        {
            'name': 'Error Alert', 
            'message': f"🚨 **ERROR ALERT - TEST**\n\n**Error Type:** connection_test\n**Message:** This is a test error message\n**Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            'data': {'error_type': 'connection_test', 'error_message': 'This is a test error message', 'test': True}
        }
    ]
    
    success_count = 0
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. Testing {test_case['name']}...")
        
        payload = {
            'message': test_case['message'],
            'timestamp': datetime.now().isoformat(),
            'data': test_case['data'],
            'source': 'webhook_test_script'
        }
        
        try:
            response = requests.post(
                N8N_TELEGRAM_FEEDBACK,
                json=payload,
                timeout=10,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                print(f"   ✅ {test_case['name']} notification sent successfully")
                success_count += 1
            else:
                print(f"   ❌ {test_case['name']} notification failed: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ {test_case['name']} notification failed: {e}")
        
        # Small delay between tests
        import time
        time.sleep(1)
    
    print(f"\n📈 Test Results: {success_count}/{len(test_cases)} notifications sent successfully")
    return success_count == len(test_cases)

def main():
    """Main test function"""
    print("🧪 TELEGRAM FEEDBACK WEBHOOK TEST")
    print("=" * 50)
    
    if not N8N_TELEGRAM_FEEDBACK:
        print("❌ N8N_TELEGRAM_FEEDBACK webhook URL not configured")
        sys.exit(1)
    
    # Test basic connection
    if not test_webhook_connection():
        print("\n❌ Basic webhook test failed. Check your configuration.")
        sys.exit(1)
    
    # Test trading notifications
    if test_trading_signals():
        print("\n🎉 All tests passed! Telegram feedback is working correctly.")
        print("\nYou should see test messages in your Telegram channel.")
        print("The trading bot is ready to send real notifications!")
    else:
        print("\n⚠️  Some tests failed. Check your N8N workflow configuration.")
        sys.exit(1)

if __name__ == '__main__':
    main()