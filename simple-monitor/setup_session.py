#!/usr/bin/env python3
"""
Interactive setup script for Telegram authentication
Run this once to create the session file, then use the regular monitor
"""

import asyncio
import os
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

API_ID = os.getenv('TELEGRAM_API_ID')
API_HASH = os.getenv('TELEGRAM_API_HASH')
PHONE_NUMBER = os.getenv('TELEGRAM_PHONE')
SESSION_NAME = os.getenv('SESSION_NAME', 'telegram_monitor')

async def setup_session():
    """Interactive session setup"""
    print("🔐 Setting up Telegram session...")
    
    if not all([API_ID, API_HASH, PHONE_NUMBER]):
        print("❌ Missing Telegram API credentials in .env file")
        return False
        
    print(f"📱 Using phone number: {PHONE_NUMBER}")
    
    client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
    
    try:
        await client.start(phone=PHONE_NUMBER)
        
        if await client.is_user_authorized():
            print("✅ Session created successfully!")
            print(f"📁 Session file: {SESSION_NAME}.session")
            return True
        else:
            print("❌ Authorization failed")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    finally:
        await client.disconnect()

if __name__ == "__main__":
    asyncio.run(setup_session())