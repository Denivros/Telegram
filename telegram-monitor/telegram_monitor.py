#!/usr/bin/env python3
"""
Telegram Group Monitor for n8n Integration

This script monitors a Telegram group using your personal account
and sends all messages and events to an n8n webhook.

Features:
- Monitor messages in real-time
- Track member joins/leaves
- Send media information
- Handle message edits and deletions
- Robust error handling and reconnection
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from typing import Dict, Any, Optional

import requests
from telethon import TelegramClient, events
from telethon.errors import SessionPasswordNeededError, FloodWaitError
from telethon.tl.types import (
    MessageMediaPhoto, MessageMediaDocument, 
    MessageMediaContact, MessageMediaGeo,
    MessageMediaWebPage, User, Chat, Channel
)
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
API_ID = os.getenv('TELEGRAM_API_ID')
API_HASH = os.getenv('TELEGRAM_API_HASH')
PHONE_NUMBER = os.getenv('TELEGRAM_PHONE')
GROUP_ID = os.getenv('TELEGRAM_GROUP_ID')  # Can be group username or ID
N8N_WEBHOOK_URL = os.getenv('N8N_WEBHOOK_URL')
SESSION_NAME = os.getenv('SESSION_NAME', 'telegram_monitor')

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('telegram_monitor.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class TelegramMonitor:
    def __init__(self):
        self.client = None
        self.target_group = None
        self.running = False
        
    def validate_config(self) -> bool:
        """Validate that all required configuration is present."""
        required_vars = [
            ('TELEGRAM_API_ID', API_ID),
            ('TELEGRAM_API_HASH', API_HASH),
            ('TELEGRAM_PHONE', PHONE_NUMBER),
            ('TELEGRAM_GROUP_ID', GROUP_ID),
            ('N8N_WEBHOOK_URL', N8N_WEBHOOK_URL)
        ]
        
        missing_vars = []
        for var_name, var_value in required_vars:
            if not var_value:
                missing_vars.append(var_name)
        
        if missing_vars:
            logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
            return False
        
        return True
    
    async def initialize_client(self):
        """Initialize and authenticate the Telegram client."""
        try:
            self.client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
            
            await self.client.start(phone=PHONE_NUMBER)
            
            if not await self.client.is_user_authorized():
                logger.error("Failed to authorize user")
                return False
            
            # Get information about the target group
            try:
                # Convert GROUP_ID to integer if it's a numeric string
                group_id = GROUP_ID
                if isinstance(group_id, str) and group_id.lstrip('-').isdigit():
                    group_id = int(group_id)
                
                self.target_group = await self.client.get_entity(group_id)
                logger.info(f"Successfully connected to group: {self.target_group.title}")
            except Exception as e:
                logger.error(f"Could not find group {GROUP_ID}: {e}")
                return False
            
            return True
            
        except SessionPasswordNeededError:
            logger.error("Two-step verification is enabled. Please disable it temporarily or implement 2FA handling.")
            return False
        except Exception as e:
            logger.error(f"Failed to initialize client: {e}")
            return False
    
    def send_to_n8n(self, data: Dict[str, Any]) -> bool:
        """Send data to n8n webhook."""
        try:
            # Add timestamp to all messages
            data['timestamp'] = datetime.now().isoformat()
            data['monitor_source'] = 'telegram_group_monitor'
            
            response = requests.post(
                N8N_WEBHOOK_URL,
                json=data,
                timeout=30,
                headers={'Content-Type': 'application/json'}
            )
            
            response.raise_for_status()
            logger.info(f"Successfully sent data to n8n: {data.get('event_type', 'unknown')}")
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send data to n8n: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending to n8n: {e}")
            return False
    
    def format_user_info(self, user) -> Dict[str, Any]:
        """Extract user information safely."""
        if not user:
            return {}
        
        return {
            'id': user.id,
            'first_name': getattr(user, 'first_name', ''),
            'last_name': getattr(user, 'last_name', ''),
            'username': getattr(user, 'username', ''),
            'phone': getattr(user, 'phone', ''),
            'is_bot': getattr(user, 'bot', False),
            'is_verified': getattr(user, 'verified', False),
            'is_premium': getattr(user, 'premium', False)
        }
    
    def format_media_info(self, media) -> Dict[str, Any]:
        """Extract media information."""
        if not media:
            return {}
        
        media_info = {'has_media': True}
        
        if isinstance(media, MessageMediaPhoto):
            media_info.update({
                'media_type': 'photo',
                'photo_id': media.photo.id if media.photo else None
            })
        elif isinstance(media, MessageMediaDocument):
            doc = media.document
            media_info.update({
                'media_type': 'document',
                'document_id': doc.id if doc else None,
                'file_name': None,
                'mime_type': doc.mime_type if doc else None,
                'file_size': doc.size if doc else None
            })
            # Try to get filename from attributes
            if doc and doc.attributes:
                for attr in doc.attributes:
                    if hasattr(attr, 'file_name') and attr.file_name:
                        media_info['file_name'] = attr.file_name
                        break
        elif isinstance(media, MessageMediaContact):
            media_info.update({
                'media_type': 'contact',
                'contact_phone': media.phone_number,
                'contact_name': f"{media.first_name} {media.last_name}".strip()
            })
        elif isinstance(media, MessageMediaGeo):
            media_info.update({
                'media_type': 'location',
                'latitude': media.geo.lat,
                'longitude': media.geo.long
            })
        elif isinstance(media, MessageMediaWebPage):
            webpage = media.webpage
            media_info.update({
                'media_type': 'webpage',
                'webpage_url': webpage.url if webpage else None,
                'webpage_title': webpage.title if webpage else None,
                'webpage_description': webpage.description if webpage else None
            })
        else:
            media_info.update({
                'media_type': 'other',
                'media_class': media.__class__.__name__
            })
        
        return media_info
    
    async def setup_event_handlers(self):
        """Set up event handlers for different types of Telegram events."""
        
        @self.client.on(events.NewMessage(chats=self.target_group))
        async def handle_new_message(event):
            """Handle new messages in the group."""
            try:
                message = event.message
                sender = await event.get_sender()
                
                data = {
                    'event_type': 'new_message',
                    'message_id': message.id,
                    'message_text': message.text or '',
                    'message_date': message.date.isoformat(),
                    'sender': self.format_user_info(sender),
                    'is_reply': message.reply_to is not None,
                    'reply_to_message_id': message.reply_to.reply_to_msg_id if message.reply_to else None,
                    'is_forward': message.forward is not None,
                    'forward_from': {},
                    'media': self.format_media_info(message.media),
                    'group_info': {
                        'id': self.target_group.id,
                        'title': getattr(self.target_group, 'title', ''),
                        'username': getattr(self.target_group, 'username', '')
                    }
                }
                
                # Add forward information if available
                if message.forward:
                    forward_info = {}
                    if message.forward.from_id:
                        try:
                            forward_sender = await self.client.get_entity(message.forward.from_id)
                            forward_info = self.format_user_info(forward_sender)
                        except:
                            forward_info = {'id': message.forward.from_id.user_id if hasattr(message.forward.from_id, 'user_id') else None}
                    
                    data['forward_from'] = forward_info
                    data['forward_date'] = message.forward.date.isoformat() if message.forward.date else None
                
                self.send_to_n8n(data)
                
            except Exception as e:
                logger.error(f"Error handling new message: {e}")
        
        @self.client.on(events.MessageEdited(chats=self.target_group))
        async def handle_message_edited(event):
            """Handle message edits."""
            try:
                message = event.message
                sender = await event.get_sender()
                
                data = {
                    'event_type': 'message_edited',
                    'message_id': message.id,
                    'new_text': message.text or '',
                    'edit_date': message.edit_date.isoformat() if message.edit_date else None,
                    'original_date': message.date.isoformat(),
                    'sender': self.format_user_info(sender),
                    'media': self.format_media_info(message.media),
                    'group_info': {
                        'id': self.target_group.id,
                        'title': getattr(self.target_group, 'title', ''),
                        'username': getattr(self.target_group, 'username', '')
                    }
                }
                
                self.send_to_n8n(data)
                
            except Exception as e:
                logger.error(f"Error handling message edit: {e}")
        
        @self.client.on(events.MessageDeleted())
        async def handle_message_deleted(event):
            """Handle message deletions."""
            try:
                # Note: We can only get message IDs for deleted messages
                data = {
                    'event_type': 'message_deleted',
                    'deleted_message_ids': event.deleted_ids,
                    'group_info': {
                        'id': self.target_group.id,
                        'title': getattr(self.target_group, 'title', ''),
                        'username': getattr(self.target_group, 'username', '')
                    }
                }
                
                self.send_to_n8n(data)
                
            except Exception as e:
                logger.error(f"Error handling message deletion: {e}")
        
        @self.client.on(events.ChatAction(chats=self.target_group))
        async def handle_chat_action(event):
            """Handle user joins, leaves, and other chat actions."""
            try:
                action_user = None
                if event.user_id:
                    try:
                        action_user = await self.client.get_entity(event.user_id)
                    except:
                        action_user = None
                
                data = {
                    'event_type': 'chat_action',
                    'action_type': event.action.__class__.__name__,
                    'user': self.format_user_info(action_user) if action_user else {},
                    'action_date': event.date.isoformat() if event.date else None,
                    'group_info': {
                        'id': self.target_group.id,
                        'title': getattr(self.target_group, 'title', ''),
                        'username': getattr(self.target_group, 'username', '')
                    }
                }
                
                self.send_to_n8n(data)
                
            except Exception as e:
                logger.error(f"Error handling chat action: {e}")
        
        logger.info("Event handlers set up successfully")
    
    async def run(self):
        """Main run loop."""
        if not self.validate_config():
            return False
        
        logger.info("Starting Telegram Group Monitor...")
        
        if not await self.initialize_client():
            logger.error("Failed to initialize client")
            return False
        
        await self.setup_event_handlers()
        
        # Send startup notification to n8n
        startup_data = {
            'event_type': 'monitor_started',
            'group_info': {
                'id': self.target_group.id,
                'title': getattr(self.target_group, 'title', ''),
                'username': getattr(self.target_group, 'username', ''),
                'member_count': getattr(self.target_group, 'participants_count', 'unknown')
            }
        }
        self.send_to_n8n(startup_data)
        
        logger.info("Monitor is running. Press Ctrl+C to stop.")
        self.running = True
        
        try:
            # Keep the client running
            await self.client.run_until_disconnected()
        except KeyboardInterrupt:
            logger.info("Received interrupt signal")
        except FloodWaitError as e:
            logger.warning(f"Flood wait error: {e}. Waiting {e.seconds} seconds...")
            await asyncio.sleep(e.seconds)
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
        finally:
            self.running = False
            if self.client:
                await self.client.disconnect()
            
            # Send shutdown notification
            shutdown_data = {
                'event_type': 'monitor_stopped',
                'group_info': {
                    'id': self.target_group.id if self.target_group else None,
                    'title': getattr(self.target_group, 'title', '') if self.target_group else '',
                }
            }
            self.send_to_n8n(shutdown_data)
            
        logger.info("Monitor stopped")
        return True


async def main():
    """Main entry point."""
    monitor = TelegramMonitor()
    await monitor.run()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutting down gracefully...")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)