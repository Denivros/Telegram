#!/usr/bin/env python3
"""
Test StringSession authentication on VPS
"""

import asyncio
import os
from telethon import TelegramClient
from telethon.sessions import StringSession
from dotenv import load_dotenv

load_dotenv()

API_ID = os.getenv('TELEGRAM_API_ID')
API_HASH = os.getenv('TELEGRAM_API_HASH')
STRING_SESSION = os.getenv('STRING_SESSION')

async def test_string_session():
    print("🔑 TESTING STRING SESSION ON VPS")
    print("=" * 50)
    
    if not STRING_SESSION or STRING_SESSION.strip() == "":
        print("❌ No STRING_SESSION found in .env file!")
        print("💡 Steps to fix:")
        print("1. Run generate_string_session_macbook.py on your MacBook")
        print("2. Copy the generated string")
        print("3. Add it to .env file: STRING_SESSION=your_string_here")
        return False
    
    print(f"📱 Using StringSession: {STRING_SESSION[:50]}...")
    
    # Create client with StringSession
    client = TelegramClient(StringSession(STRING_SESSION), API_ID, API_HASH)
    
    try:
        print("📡 Connecting to Telegram using StringSession...")
        await client.connect()
        
        if await client.is_user_authorized():
            me = await client.get_me()
            print("✅ StringSession authentication successful!")
            print(f"👤 Logged in as: {me.first_name} ({me.phone})")
            print(f"🆔 User ID: {me.id}")
            
            # Test group access
            group_id = os.getenv('TELEGRAM_GROUP_ID')
            if group_id:
                try:
                    group = await client.get_entity(int(group_id))
                    print(f"📢 Group access: {group.title} ✅")
                except Exception as e:
                    print(f"📢 Group access error: {e}")
            
            return True
        else:
            print("❌ StringSession is not authorized")
            return False
            
    except Exception as e:
        print(f"❌ StringSession test failed: {e}")
        return False
    finally:
        await client.disconnect()

if __name__ == "__main__":
    success = asyncio.run(test_string_session())
    
    if success:
        print("\n🎉 StringSession works! You can now update your bot.")
        print("💡 Next: Modify direct_mt5_monitor.py to use StringSession")
    else:
        print("\n❌ StringSession test failed. Check your setup.")