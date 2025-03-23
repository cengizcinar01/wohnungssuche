"""Configuration module for the apartment search application."""
import os
from typing import Dict, List, Union, Any
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Application-wide configuration with sensible defaults."""
    
    # Search criteria
    SEARCH_CONFIG = {
        'min_rooms': 3,
        'max_rooms': 4,
        'min_size': 70,
        'max_size': 95,
        'max_price': 973,
        'districts': {
            'woltmershausen': '26',      # Location ID for Woltmershausen
            'neustadt': '41',            # Location ID for Neustadt
            'arsten': '18881',           # Location ID for Arsten
            'habenhausen': '17479',      # Location ID for Habenhausen
            'huckelriede': '13502',      # Location ID for Huckelriede
            'kattenturm': '21199'        # Location ID for Kattenturm
        }
    }
    
    # Search URLs (generated from config)
    @property
    def SEARCH_URLS(self) -> List[str]:
        """Generate search URLs based on configuration."""
        return [
            f"https://www.kleinanzeigen.de/s-wohnung-mieten/{district}/preis::{self.SEARCH_CONFIG['max_price']}/c203l{location_id}+wohnung_mieten.qm_d:{self.SEARCH_CONFIG['min_size']:.2f}%2C{self.SEARCH_CONFIG['max_size']:.2f}+wohnung_mieten.zimmer_d:{self.SEARCH_CONFIG['min_rooms']}%2C{self.SEARCH_CONFIG['max_rooms']}"
            for district, location_id in self.SEARCH_CONFIG['districts'].items()
        ]
    
    # Notification
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
    
    @property
    def TELEGRAM_CHAT_IDS(self) -> List[str]:
        """Get list of Telegram chat IDs from environment variable."""
        chat_ids = os.getenv('TELEGRAM_CHAT_IDS', '')
        return [id.strip() for id in chat_ids.split(',') if id.strip()]
    
    # Database
    DATABASE_URL = os.getenv('DATABASE_URL', '')
    
    # Timing
    CHECK_INTERVAL = 100  # 5 minutes
    PAGE_LOAD_TIMEOUT = 10  # seconds
    ELEMENT_TIMEOUT = 10  # seconds for element waits (decreased from 15)
    
    # Browser settings
    HEADLESS_MODE = True  # Set to False to see the browser window
    
    # Contact message
    PREDEFINED_TEXT = """Guten Tag,

wir sind eine ruhige Familie mit drei schulpflichtigen Kindern und suchen eine passende Wohnung. Wir haben als Familie eine Zeit lang in der Türkei gelebt und dort versucht, uns ein Leben aufzubauen. Nun sind wir wieder in Deutschland und möchten hier einen Neuanfang starten. Die Mietzahlung erfolgt direkt vom Jobcenter, was Ihnen eine pünktliche und sichere Zahlung garantiert.

Als Nichtraucher ohne Haustiere und mit deutscher Staatsbürgerschaft bieten wir ein unkompliziertes Mietverhältnis. Derzeit sind wir bei Bekannten untergebracht und würden uns über einen baldigen Besichtigungstermin freuen.

Für Rückfragen stehe ich Ihnen gerne unter 01575 5259983 zur Verfügung.

Vielen Dank für Ihre Zeit und eine Rückmeldung!

Mit freundlichen Grüßen

R. Cinar"""
    
    def __init__(self):
        """Validate configuration on initialization."""
        if not self.DATABASE_URL:
            raise ValueError("DATABASE_URL not found in environment variables")
        
        # Optional validation
        if not self.TELEGRAM_BOT_TOKEN or not self.TELEGRAM_CHAT_IDS:
            print("Warning: Telegram not fully configured. Notifications will be disabled.")

# Create a global config instance
config = Config()
