#!/usr/bin/env python3
"""
Helper script to list all groups you're a member of
This will help you find the correct group ID
"""

import asyncio
import os
from telethon import TelegramClient
from telethon.tl.types import Chat, Channel
from dotenv import load_dotenv

load_dotenv()

API_ID = os.getenv('TELEGRAM_API_ID')
API_HASH = os.getenv('TELEGRAM_API_HASH')
PHONE_NUMBER = os.getenv('TELEGRAM_PHONE')
SESSION_NAME = os.getenv('SESSION_NAME', 'telegram_monitor')

async def list_groups():
    """List all groups the user is a member of."""
    client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
    
    try:
        await client.start(phone=PHONE_NUMBER)
        
        print("📋 Groups you're a member of:\n")
        print("=" * 80)
        
        async for dialog in client.iter_dialogs():
            entity = dialog.entity
            
            # Check if it's a group or channel
            if isinstance(entity, (Chat, Channel)):
                group_type = "Channel" if isinstance(entity, Channel) else "Group"
                
                print(f"🔹 {group_type}: {entity.title}")
                print(f"   ID: {entity.id}")
                if hasattr(entity, 'username') and entity.username:
                    print(f"   Username: @{entity.username}")
                else:
                    print("   Username: (none)")
                
                # For channels, show if it's a supergroup
                if isinstance(entity, Channel):
                    if entity.megagroup:
                        print("   Type: Supergroup")
                    elif entity.broadcast:
                        print("   Type: Broadcast Channel")
                    else:
                        print("   Type: Channel")
                
                print(f"   Members: {getattr(entity, 'participants_count', 'Unknown')}")
                print("-" * 40)
        
        print("\n✅ Copy the ID of your target group and update TELEGRAM_GROUP_ID in .env")
        print("💡 Tip: Use the exact ID number shown above (including the minus sign if present)")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        await client.disconnect()

if __name__ == '__main__':
    asyncio.run(list_groups())