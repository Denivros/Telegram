#!/usr/bin/env python3
"""
StringSession Generator for MacBook
Run this on your MacBook where Telegram authentication works
"""

import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession

# Your API credentials (same as VPS)
API_ID = 22159421
API_HASH = '0a383c450ac02bbc327fd975f32387c4'
PHONE_NUMBER = '+32474071892'

async def generate_string_session():
    print("🔑 TELEGRAM STRING SESSION GENERATOR")
    print("=" * 50)
    print("This will create a session string you can use on your VPS")
    print()
    
    # Use empty StringSession to force fresh authentication
    client = TelegramClient(StringSession(), API_ID, API_HASH)
    
    try:
        print("📡 Connecting to Telegram...")
        await client.start(phone=PHONE_NUMBER)
        
        print("✅ Authentication successful!")
        
        # Get user info to confirm
        me = await client.get_me()
        print(f"👤 Logged in as: {me.first_name} ({me.phone})")
        print()
        
        # Generate the string session
        string_session = client.session.save()
        
        print("🔐 STRING SESSION GENERATED:")
        print("=" * 50)
        print(string_session)
        print("=" * 50)
        print()
        
        print("📋 NEXT STEPS:")
        print("1. Copy the string above")
        print("2. Go to your VPS")
        print("3. Add this to your .env file as:")
        print(f"   STRING_SESSION={string_session}")
        print("4. Update your bot to use StringSession")
        print()
        print("⚠️  SECURITY WARNING:")
        print("   Keep this string PRIVATE! It's like your login password.")
        print("   Anyone with this string can access your Telegram account.")
        
        return string_session
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return None
    finally:
        await client.disconnect()

if __name__ == "__main__":
    print("🚀 Starting StringSession generation...")
    print("📱 You may need to enter your phone verification code.")
    print()
    
    session_string = asyncio.run(generate_string_session())
    
    if session_string:
        print("\n🎉 StringSession created successfully!")
        print("Now transfer this to your VPS and update the bot code.")
    else:
        print("\n❌ Failed to create StringSession")