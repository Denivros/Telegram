#!/usr/bin/env python3
"""
Quick Telegram Session Creator
Simple script to authenticate and create session file
"""

import asyncio
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError

# Your Telegram API credentials (from .env or hardcoded)
API_ID = 22159421
API_HASH = "0a383c450ac02bbc327fd975f32387c4"
PHONE_NUMBER = "+32474071892"
SESSION_NAME = "telegram_monitor"

async def quick_setup():
    """Quick session setup"""
    print(f"📱 Creating session for {PHONE_NUMBER}...")
    
    client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
    
    try:
        await client.start(phone=PHONE_NUMBER)
        
        # Get user info
        me = await client.get_me()
        print(f"✅ Authenticated as: {me.first_name}")
        print(f"📄 Session saved as: {SESSION_NAME}.session")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    finally:
        await client.disconnect()

if __name__ == "__main__":
    if asyncio.run(quick_setup()):
        print("🎉 Session ready! You can now run direct_mt5_monitor.py")
    else:
        print("❌ Session setup failed")