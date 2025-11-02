#!/usr/bin/env python3
"""
Quick verification script to test StringSession authentication
Run this to verify the StringSession is working before running the main bot
"""

import asyncio
import os
from telethon import TelegramClient
from telethon.sessions import StringSession
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
API_ID = os.getenv('TELEGRAM_API_ID')
API_HASH = os.getenv('TELEGRAM_API_HASH') 
STRING_SESSION = os.getenv('STRING_SESSION')
GROUP_ID = os.getenv('TELEGRAM_GROUP_ID')

async def verify_string_session():
    """Verify StringSession is working properly"""
    
    print("🔐 StringSession Verification")
    print("=" * 40)
    
    # Check configuration
    print(f"API_ID: {'✅ Set' if API_ID else '❌ Missing'}")
    print(f"API_HASH: {'✅ Set' if API_HASH else '❌ Missing'}")
    print(f"STRING_SESSION: {'✅ Set' if STRING_SESSION else '❌ Missing'}")
    print(f"GROUP_ID: {'✅ Set' if GROUP_ID else '❌ Missing'}")
    
    if not all([API_ID, API_HASH, STRING_SESSION]):
        print("\n❌ Missing required configuration!")
        print("Please ensure API_ID, API_HASH, and STRING_SESSION are set in .env file")
        return False
    
    print(f"\nStringSession length: {len(STRING_SESSION)} characters")
    
    # Test connection
    try:
        print("\n🔄 Testing Telegram connection...")
        
        client = TelegramClient(
            StringSession(STRING_SESSION),
            API_ID,
            API_HASH,
            timeout=30
        )
        
        await client.start()
        
        # Check if authorized
        if await client.is_user_authorized():
            print("✅ StringSession authentication successful!")
            
            # Get user info
            me = await client.get_me()
            print(f"   Connected as: {me.first_name} {me.last_name or ''}")
            print(f"   Username: @{me.username}" if me.username else "   Username: Not set")
            print(f"   Phone: {me.phone}" if me.phone else "   Phone: Not available")
            
            # Test group access if GROUP_ID is set
            if GROUP_ID:
                try:
                    print(f"\n🔄 Testing group access...")
                    group_id = GROUP_ID
                    if isinstance(group_id, str) and group_id.lstrip('-').isdigit():
                        group_id = int(group_id)
                    
                    group = await client.get_entity(group_id)
                    print(f"✅ Group access successful!")
                    print(f"   Group: {group.title}")
                    print(f"   Members: {group.participants_count}" if hasattr(group, 'participants_count') else "   Members: Unknown")
                    
                except Exception as e:
                    print(f"❌ Group access failed: {e}")
                    print(f"   Please check GROUP_ID: {GROUP_ID}")
                    return False
            
            await client.disconnect()
            print(f"\n🎉 StringSession verification completed successfully!")
            print(f"   Your bot should now work with this StringSession")
            return True
            
        else:
            print("❌ StringSession is not authorized!")
            print("   The StringSession may be invalid or expired")
            print("   Please generate a new one using generate_string_session_macbook.py")
            return False
            
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print("   The StringSession may be invalid")
        print("   Please generate a new one using generate_string_session_macbook.py")
        return False

if __name__ == "__main__":
    success = asyncio.run(verify_string_session())
    
    if success:
        print(f"\n✅ Ready to run the trading bot!")
        print(f"   Execute: python direct_mt5_monitor.py")
    else:
        print(f"\n❌ StringSession verification failed")
        print(f"   Fix the issues above before running the bot")
        
    input(f"\nPress Enter to exit...")