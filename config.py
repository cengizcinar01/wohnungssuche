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
    
    # Filtering
    NEGATIVE_KEYWORDS = [
        'keine leistungsempfänger',
        'keine jobcenter',
        'keine sozialleistungen',
        'keine hartz',
        'keine arbeitslosengeld',
        'nur berufstätige',
        'nur an berufstätige',
        'keine alg',
        'keine arbeitslosen',
        'keine sozialhilfe',
        'nur mit festanstellung',
        'nur mit unbefristeter festanstellung',
        'nur arbeitnehmer',
    ]
    
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
    ELEMENT_TIMEOUT = 15  # seconds for element waits
    
    # Browser settings
    HEADLESS_MODE = True  # Set to False to see the browser window
    
    # Contact message
    PREDEFINED_TEXT = """Guten Tag,

wir sind eine Familie mit 3 schulpflichtigen Kindern und suchen nach Rückkehr aus der Türkei dringend eine Wohnung. Derzeit sind wir provisorisch bei Bekannten untergebracht.

Kurz zu uns:
Wir sind ruhig, Nichtraucher, keine Haustiere und besitzen alle die deutsche Staatsbürgerschaft. Mietzahlung übernimmt vollständig das Jobcenter mit Direktüberweisung an Sie.

Für weitere Informationen bin ich jederzeit unter der Nummer 01575 5259983 erreichbar.

Würde mich über einen Besichtigungstermin freuen.

LG

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