#!/usr/bin/env python3
"""
List Telegram groups using StringSession
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

async def list_groups():
    """List all groups the user is a member of"""
    
    if not STRING_SESSION:
        print("❌ STRING_SESSION not found in .env file")
        return
    
    client = TelegramClient(StringSession(STRING_SESSION), API_ID, API_HASH)
    
    try:
        await client.start()
        
        print("📋 TELEGRAM GROUPS & CHANNELS")
        print("=" * 60)
        
        dialogs = []
        async for dialog in client.iter_dialogs():
            dialogs.append(dialog)
        
        groups = [d for d in dialogs if d.is_group or d.is_channel]
        users = [d for d in dialogs if d.is_user]
        
        print(f"\n🔍 Found {len(groups)} groups/channels and {len(users)} users\n")
        
        if groups:
            print("📢 GROUPS & CHANNELS:")
            print("-" * 60)
            for dialog in groups:
                entity = dialog.entity
                group_type = "Channel" if dialog.is_channel else "Group"
                print(f"📋 {group_type}: {entity.title}")
                print(f"   ID: {entity.id} (use this for TELEGRAM_GROUP_ID)")
                print(f"   Username: @{entity.username}" if hasattr(entity, 'username') and entity.username else "   Username: None")
                print()
        
        if users:
            print("👤 RECENT USERS/BOTS:")
            print("-" * 60)
            for dialog in users[:5]:  # Show only first 5 users
                entity = dialog.entity
                name = f"{entity.first_name or ''} {entity.last_name or ''}".strip()
                print(f"👤 User: {name}")
                print(f"   ID: {entity.id}")
                print(f"   Username: @{entity.username}" if hasattr(entity, 'username') and entity.username else "   Username: None")
                print()
        
        print("💡 USAGE:")
        print("Copy the GROUP ID (negative number) to your .env file:")
        print("TELEGRAM_GROUP_ID=-1234567890")
        
    except Exception as e:
        print(f"❌ Error listing groups: {e}")
    finally:
        await client.disconnect()

if __name__ == "__main__":
    asyncio.run(list_groups())