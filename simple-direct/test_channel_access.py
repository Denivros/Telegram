#!/usr/bin/env python3
"""
Test specific channel access with different ID formats
"""

import asyncio
import os
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.errors import ChannelInvalidError, ChannelPrivateError
from dotenv import load_dotenv

load_dotenv()

API_ID = os.getenv('TELEGRAM_API_ID')
API_HASH = os.getenv('TELEGRAM_API_HASH')
STRING_SESSION = os.getenv('STRING_SESSION')

async def test_channel_access():
    """Test different ways to access the CallistoFx Premium Channel"""
    
    client = TelegramClient(StringSession(STRING_SESSION), API_ID, API_HASH)
    
    try:
        await client.start()
        
        print("🔍 TESTING CHANNEL ACCESS METHODS")
        print("=" * 50)
        
        # Test different ID formats for CallistoFx Premium Channel
        channel_ids = [
            1623437581,    # Original positive ID
            -1623437581,   # Negative format
            -1001623437581  # Full channel ID format
        ]
        
        for channel_id in channel_ids:
            print(f"\n🔄 Testing channel ID: {channel_id}")
            try:
                entity = await client.get_entity(channel_id)
                print(f"✅ SUCCESS! Channel: {entity.title}")
                print(f"   Type: {'Channel' if hasattr(entity, 'broadcast') else 'Group'}")
                print(f"   ID: {entity.id}")
                print(f"   Access hash: {getattr(entity, 'access_hash', 'N/A')}")
                
                # Test message access
                try:
                    messages = await client.get_messages(entity, limit=1)
                    print(f"✅ Can read messages: {len(messages)} messages accessible")
                except Exception as e:
                    print(f"❌ Cannot read messages: {e}")
                    
                break  # If successful, use this ID
                
            except ChannelInvalidError:
                print("❌ Channel not found or invalid")
            except ChannelPrivateError:
                print("❌ Channel is private or access denied")
            except Exception as e:
                print(f"❌ Error: {e}")
        
        # Also try to find by name/title
        print(f"\n🔍 Searching for CallistoFx channels by name...")
        async for dialog in client.iter_dialogs():
            if 'callisto' in dialog.title.lower() and 'premium' in dialog.title.lower():
                entity = dialog.entity
                print(f"\n✅ FOUND: {entity.title}")
                print(f"   ID: {entity.id}")
                print(f"   Type: {'Channel' if dialog.is_channel else 'Group'}")
                
                # Test with different ID formats
                test_ids = [entity.id, -entity.id, -1000000000000 - entity.id]
                for test_id in test_ids:
                    try:
                        test_entity = await client.get_entity(test_id)
                        print(f"   Working ID format: {test_id}")
                        break
                    except:
                        continue
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        await client.disconnect()

if __name__ == "__main__":
    asyncio.run(test_channel_access())