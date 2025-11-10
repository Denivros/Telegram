"""
Configuration file for MT5 Trading Bot
Contains all constants, settings, and helper functions
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# =============================================================================
# TELEGRAM CONFIGURATION
# =============================================================================
API_ID = os.getenv('TELEGRAM_API_ID')
API_HASH = os.getenv('TELEGRAM_API_HASH')
BOT_TOKEN = os.getenv('BOT_TOKEN')
PHONE_NUMBER = os.getenv('TELEGRAM_PHONE')  # Keep for fallback
STRING_SESSION = os.getenv('STRING_SESSION')  # StringSession for authentication
GROUP_ID = os.getenv('TELEGRAM_GROUP_ID')
SESSION_NAME = os.getenv('SESSION_NAME', 'telegram_monitor')

# =============================================================================
# MT5 VPS CONNECTION CONFIGURATION
# =============================================================================
MT5_LOGIN = int(os.getenv('MT5_LOGIN', '0'))
MT5_PASSWORD = os.getenv('MT5_PASSWORD', '')
MT5_SERVER = os.getenv('MT5_SERVER', '')

# =============================================================================
# TRADING CONFIGURATION
# =============================================================================
DEFAULT_VOLUME = float(os.getenv('DEFAULT_VOLUME', '0.09'))
DEFAULT_VOLUME_MULTI = float(os.getenv('DEFAULT_VOLUME_MULTI', '0.01'))  # Multiplier for triple entry volumes
BE_PARTIAL_VOLUME = float(os.getenv('BE_PARTIAL_VOLUME', '0.01'))  # Volume to close when moving to BE (single entry)
BE_PARTIAL_VOLUME_MULTI = float(os.getenv('BE_PARTIAL_VOLUME_MULTI', '0.01'))  # Volume to close when moving to BE (multi-entry)
PARTIALS_VOLUME = float(os.getenv('PARTIALS_VOLUME', '0.02'))      # Volume to close for partial profits (single entry)
PARTIALS_VOLUME_MULTI = float(os.getenv('PARTIALS_VOLUME_MULTI', '0.01'))      # Volume to close for partial profits (multi-entry)
ENTRY_STRATEGY = os.getenv('ENTRY_STRATEGY', 'adaptive')  # adaptive, midpoint, range_break, momentum, dual_entry, triple_entry, multi_tp_entry, multi_position_entry
MAGIC_NUMBER = int(os.getenv('MAGIC_NUMBER', '123456'))

# Multi-TP Strategy Configuration
MULTI_TP_PIPS = [200, 400, 600, 800]  # TP1, TP2, TP3, TP4 in pips (TP5 uses signal's TP)
MULTI_TP_VOLUMES = [0.01, 0.01, 0.01, 0.01, 0.01]  # Volume for each TP level

# Multi-Position Distribution Strategy Configuration
NUMBER_POSITIONS_MULTI = int(os.getenv('NUMBER_POSITIONS_MULTI', '9'))  # Total positions to open
POSITION_VOLUME_MULTI = 0.01  # Volume for each position in multi-position strategy

# =============================================================================
# N8N WEBHOOKS CONFIGURATION
# =============================================================================
N8N_TELEGRAM_FEEDBACK = os.getenv('N8N_TELEGRAM_FEEDBACK', 'https://n8n.srv881084.hstgr.cloud/webhook/91126b9d-bd23-4e92-8891-5bfb217455c7')
N8N_LOG_WEBHOOK = N8N_TELEGRAM_FEEDBACK  # Use same webhook for all logs

# =============================================================================
# MESSAGE FILTERING CONFIGURATION
# =============================================================================
# Words/phrases to ignore - won't log as "MESSAGE IGNORED"
IGNORE_WORDS = [
    'reason for',
    'looking at',
    'weekly trading summary', 
    'weekly journals', 
    'fucking', 
    'elite trader', 
    'analysis',
    'strategy',
    'summary',
    'haha', 
    'livestream',
    'twitch',
    'how to', 
    'trading summary',
    'btc',
    'btcusd', 
    'bitcoin', 
    'gbpjpy', 
    'zoom',
    'recaps',
    'recap',
    'shit',
    'w in the chat',
    'stream', 
    'livestream',
    'channel',
    'batch', 
    'how to split risk',
    'vip discussion',
    'youtube',
    'twitch',
    'discord',
    'strategy',
    'fucking',
    'fuck',
    'haha',
    'lol',
    'NZDJPY'
]

# =============================================================================
# OVH VPS MANAGEMENT CONFIGURATION
# =============================================================================
OVH_ENDPOINT = os.getenv('OVH_ENDPOINT', 'ovh-eu')
OVH_APPLICATION_KEY = os.getenv('OVH_APPLICATION_KEY')
OVH_APPLICATION_SECRET = os.getenv('OVH_APPLICATION_SECRET')
OVH_CONSUMER_KEY = os.getenv('OVH_CONSUMER_KEY')
OVH_SERVICE_NAME = os.getenv('OVH_SERVICE_NAME')  # Your VPS service name (e.g., 'vpsXXXXXX.ovh.net')

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================
def get_partials_volume():
    """Get partial profit volume based on current strategy"""
    if ENTRY_STRATEGY in ['dual_entry', 'triple_entry', 'multi_tp_entry', 'multi_position_entry']:
        return PARTIALS_VOLUME_MULTI
    return PARTIALS_VOLUME

def get_be_partial_volume():
    """Get break-even partial volume based on current strategy"""
    if ENTRY_STRATEGY in ['dual_entry', 'triple_entry', 'multi_tp_entry', 'multi_position_entry']:
        return BE_PARTIAL_VOLUME_MULTI
    return BE_PARTIAL_VOLUME