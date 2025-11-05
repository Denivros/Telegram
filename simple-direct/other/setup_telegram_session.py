#!/usr/bin/env python3
"""
Telegram Session Setup Script
Creates a Telegram session for use with direct_mt5_monitor.py
"""

import asyncio
import os
import sys
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration from .env file
API_ID = os.getenv('TELEGRAM_API_ID')
API_HASH = os.getenv('TELEGRAM_API_HASH')
PHONE_NUMBER = os.getenv('TELEGRAM_PHONE')
SESSION_NAME = os.getenv('SESSION_NAME', 'telegram_monitor')

def validate_config():
    """Validate that all required config is present"""
    if not API_ID:
        print("❌ Error: TELEGRAM_API_ID not found in .env file")
        return False
    if not API_HASH:
        print("❌ Error: TELEGRAM_API_HASH not found in .env file")  
        return False
    if not PHONE_NUMBER:
        print("❌ Error: TELEGRAM_PHONE not found in .env file")
        return False
    
    return True

async def create_session():
    """Create Telegram session"""
    print("🔧 Setting up Telegram session...")
    print(f"📱 Phone: {PHONE_NUMBER}")
    print(f"📝 Session name: {SESSION_NAME}")
    print()
    
    # Create client
    client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
    
    try:
        # Connect to Telegram
        await client.connect()
        
        if not await client.is_user_authorized():
            print("📲 Sending authentication code...")
            await client.send_code_request(PHONE_NUMBER)
            
            # Get verification code from user
            code = input("🔑 Enter the verification code you received: ")
            
            try:
                await client.sign_in(PHONE_NUMBER, code)
            except SessionPasswordNeededError:
                # Two-factor authentication enabled
                password = input("🔒 Two-factor authentication detected. Enter your password: ")
                await client.sign_in(password=password)
        
        # Get user info
        me = await client.get_me()
        print(f"✅ Successfully authenticated as: {me.first_name} {me.last_name or ''}")
        print(f"📱 Phone: {me.phone}")
        print(f"👤 Username: @{me.username}" if me.username else "👤 No username set")
        print()
        
        # Test getting groups
        print("📋 Testing access to your groups...")
        dialogs = await client.get_dialogs(limit=10)
        group_count = sum(1 for d in dialogs if d.is_group or d.is_channel)
        print(f"✅ Found {group_count} groups/channels accessible")
        
        # Check if target group is accessible
        target_group_id = os.getenv('TELEGRAM_GROUP_ID')
        if target_group_id:
            try:
                target_group_id = int(target_group_id)
                entity = await client.get_entity(target_group_id)
                print(f"✅ Target group accessible: {entity.title}")
            except Exception as e:
                print(f"⚠️ Warning: Cannot access target group {target_group_id}: {e}")
        
        print()
        print("🎉 Session setup completed successfully!")
        print(f"📄 Session file created: {SESSION_NAME}.session")
        print("✅ You can now use this session with direct_mt5_monitor.py")
        
    except Exception as e:
        print(f"❌ Error during session setup: {e}")
        return False
    finally:
        await client.disconnect()
    
    return True

async def test_existing_session():
    """Test if existing session still works"""
    print("🧪 Testing existing session...")
    
    client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
    
    try:
        await client.connect()
        
        if await client.is_user_authorized():
            me = await client.get_me()
            print(f"✅ Existing session is valid for: {me.first_name} {me.last_name or ''}")
            return True
        else:
            print("❌ Existing session is not authorized")
            return False
            
    except Exception as e:
        print(f"❌ Error testing session: {e}")
        return False
    finally:
        await client.disconnect()

def main():
    """Main function"""
    print("=" * 60)
    print("🚀 TELEGRAM SESSION SETUP SCRIPT")
    print("=" * 60)
    print()
    
    # Validate configuration
    if not validate_config():
        print("\n❌ Configuration validation failed!")
        print("Please check your .env file and ensure all Telegram settings are correct.")
        sys.exit(1)
    
    # Check if session already exists
    session_file = f"{SESSION_NAME}.session"
    
    if os.path.exists(session_file):
        print(f"📄 Found existing session file: {session_file}")
        
        # Ask user what to do
        choice = input("Choose an option:\n1. Test existing session\n2. Create new session (overwrites existing)\n3. Exit\nEnter choice (1-3): ")
        
        if choice == "1":
            if asyncio.run(test_existing_session()):
                print("\n✅ Existing session is working perfectly!")
                print("You can use direct_mt5_monitor.py with this session.")
                return
            else:
                print("\n❌ Existing session is not working. Creating new session...")
        elif choice == "2":
            print("\n🔄 Creating new session (will overwrite existing)...")
        elif choice == "3":
            print("👋 Exiting...")
            return
        else:
            print("❌ Invalid choice. Exiting...")
            return
    
    # Create new session
    if asyncio.run(create_session()):
        print("\n" + "=" * 60)
        print("🎯 NEXT STEPS:")
        print("=" * 60)
        print("1. ✅ Your Telegram session is ready!")
        print("2. 🚀 Run your trading bot:")
        print("   python direct_mt5_monitor.py")
        print()
        print("3. 📱 The bot will now be able to:")
        print("   - Monitor your Telegram groups")
        print("   - Parse trading signals")
        print("   - Send notifications via N8N webhook")
        print()
        print("4. 🔍 Monitor the logs:")
        print("   tail -f direct_mt5_monitor.log")
        print("=" * 60)
    else:
        print("\n❌ Session setup failed!")
        sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Setup cancelled by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)