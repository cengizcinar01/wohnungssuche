"""Notification module for apartment search results."""
import asyncio
import logging
from typing import Dict, Any, Optional, List, Callable
import requests
from telegram import Bot
from telegram.ext import Application, CommandHandler, CallbackContext
from telegram.error import TelegramError

from config import config

logger = logging.getLogger(__name__)

class NotificationService:
    """Base notification service interface."""
    
    async def send_notification(self, message: str) -> bool:
        """Send a notification with the given message."""
        raise NotImplementedError("Subclasses must implement send_notification")

class TelegramNotifier(NotificationService):
    """Telegram-based notification service."""
    
    def __init__(self, bot_token: str, chat_id: str):
        """Initialize with the Telegram bot token and chat ID."""
        self.bot_token = bot_token
        self.chat_id = chat_id
        self._bot = None
        self.use_fallback = False
    
    @property
    def bot(self) -> Optional[Bot]:
        """Lazy-initialize the bot instance."""
        if self._bot is None and self.bot_token and not self.use_fallback:
            try:
                self._bot = Bot(self.bot_token)
            except Exception as e:
                logger.error(f"Failed to initialize Telegram bot: {e}")
                self.use_fallback = True
                return None
        return self._bot
    
    async def send_notification(self, message: str) -> bool:
        """Send a notification via Telegram."""
        # Check if we should use the fallback method
        if self.use_fallback or not self.bot_token or not self.chat_id:
            return self._send_notification_fallback(message)
            
        # Try to use the async bot API first
        if not self.bot:
            logger.warning("Telegram bot not initialized, using fallback method")
            return self._send_notification_fallback(message)
        
        try:
            # Try the async approach first
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode="HTML"
            )
            logger.info("Notification sent successfully via async API")
            return True
        except TelegramError as e:
            logger.error(f"Error sending Telegram message via async API: {e}")
            # If the async approach fails, try the fallback
            return self._send_notification_fallback(message)
    
    def _send_notification_fallback(self, message: str) -> bool:
        """Send a notification using standard HTTP requests as fallback."""
        if not self.bot_token or not self.chat_id:
            logger.warning("Telegram configuration missing, check .env file")
            return False
            
        try:
            response = requests.post(
                f"https://api.telegram.org/bot{self.bot_token}/sendMessage",
                json={
                    "chat_id": self.chat_id,
                    "text": message,
                    "parse_mode": "HTML"
                },
                timeout=10
            )
            response.raise_for_status()
            logger.info("Notification sent successfully via fallback HTTP API")
            return True
        except requests.RequestException as e:
            logger.error(f"Error sending Telegram message via HTTP API: {e}")
            return False
    
    def format_listing_message(self, listing_details: Dict[str, Any]) -> str:
        """Format a listing into a notification message."""
        return f"""Neue Wohnung gefunden!

Ort: {listing_details.get('location', 'Keine Angabe')}
Preis: {listing_details.get('price', 'Keine Angabe')}€
Größe: {listing_details.get('size', 'Keine Angabe')}m²
Zimmer: {listing_details.get('rooms', 'Keine Angabe')}

Link: {listing_details['url']}"""
    
    async def send_listing_notification(self, listing_details: Dict[str, Any]) -> bool:
        """Send a notification for a new apartment listing."""
        message = self.format_listing_message(listing_details)
        return await self.send_notification(message)
    
    async def send_predefined_text(self) -> bool:
        """Send the predefined text message for apartment inquiries."""
        return await self.send_notification(config.PREDEFINED_TEXT)

class TelegramBotService:
    """
    Simple Telegram bot service that uses direct API calls instead of Application.
    This avoids dependency on the polling mechanism that's causing issues.
    """
    
    def __init__(self, bot_token: str):
        """Initialize with the Telegram bot token."""
        self.bot_token = bot_token
        self.bot = None
        self.running = False
        self.update_task = None
        self.last_update_id = 0
    
    async def start(self) -> None:
        """Start the Telegram bot service."""
        if not self.bot_token:
            logger.warning("Telegram bot token not provided, bot will not start")
            return
        
        try:
            # Simply create the bot instance directly
            self.bot = Bot(self.bot_token)
            logger.info("Successfully created Telegram bot instance")
            
            # Don't start a background polling task
            # Just mark as running for the manual API functionality
            self.running = True
            logger.info("Telegram bot service started in manual API mode")
        except Exception as e:
            logger.error(f"Failed to start Telegram bot: {e}")
    
    async def stop(self) -> None:
        """Stop the Telegram bot service."""
        self.running = False
        logger.info("Telegram bot service stopped")
    
    async def check_for_commands(self) -> None:
        """
        Manual method to check for and process commands.
        This can be called periodically from elsewhere in the application
        if command handling is needed.
        """
        if not self.bot or not self.running:
            return
            
        try:
            updates = await self.bot.get_updates(
                offset=self.last_update_id + 1,
                timeout=10
            )
            
            for update in updates:
                if update.update_id > self.last_update_id:
                    self.last_update_id = update.update_id
                
                if update.message and update.message.text == '/text':
                    await self._handle_text_command(update.message)
        except Exception as e:
            logger.error(f"Error checking Telegram updates: {e}")
    
    async def _handle_text_command(self, message) -> None:
        """Send the predefined text message in response to a /text command."""
        if not self.bot:
            return
            
        try:
            await self.bot.send_message(
                chat_id=message.chat_id,
                text=config.PREDEFINED_TEXT,
                parse_mode="HTML"
            )
            logger.info(f"Sent predefined text to chat {message.chat_id}")
        except Exception as e:
            logger.error(f"Error sending predefined text: {e}")
            
            # Fallback to direct API
            self._send_text_fallback(message.chat_id, config.PREDEFINED_TEXT)
    
    def _send_text_fallback(self, chat_id, text) -> bool:
        """Send text using direct HTTP API as fallback."""
        try:
            response = requests.post(
                f"https://api.telegram.org/bot{self.bot_token}/sendMessage",
                json={
                    "chat_id": chat_id,
                    "text": text,
                    "parse_mode": "HTML"
                },
                timeout=10
            )
            response.raise_for_status()
            return True
        except Exception as e:
            logger.error(f"Error in fallback text sending: {e}")
            return False

# Factory function to create the appropriate notifier
def create_notifier() -> Optional[NotificationService]:
    """Create and return a notifier based on configuration."""
    if config.TELEGRAM_BOT_TOKEN and config.TELEGRAM_CHAT_ID:
        return TelegramNotifier(config.TELEGRAM_BOT_TOKEN, config.TELEGRAM_CHAT_ID)
    else:
        logger.warning("No notification configuration found")
        return None