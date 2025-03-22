"""Main application entry point for the apartment search service."""
import asyncio
import logging
import signal
import sys
from typing import Dict, Any, Optional, Set

from config import config
from database import DatabaseManager, ListingRepository
from service import ApartmentSearchRunner
from notifier import TelegramBotService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('apartment_search.log')
    ]
)
logger = logging.getLogger(__name__)

class ApartmentSearchApp:
    """Main application class for the apartment search service."""
    
    def __init__(self):
        """Initialize the application components."""
        self.search_runner = ApartmentSearchRunner()
        self.telegram_bot = None
        self.is_running = False
        
        # Only initialize Telegram bot if tokens are provided
        if config.TELEGRAM_BOT_TOKEN and config.TELEGRAM_CHAT_ID:
            self.telegram_bot = TelegramBotService(config.TELEGRAM_BOT_TOKEN)
    
    async def start(self) -> None:
        """Start all application services."""
        logger.info("Starting Apartment Search Application")
        
        # Setup signal handlers for graceful shutdown
        self._setup_signal_handlers()
        
        try:
            # Initialize but don't actively use the Telegram bot
            # Just have it available for sending notifications
            if self.telegram_bot:
                try:
                    # Simple initialization only, no polling
                    await self.telegram_bot.start()
                    logger.info("Telegram notification service initialized")
                except Exception as e:
                    logger.error(f"Failed to initialize Telegram service: {e}")
                    logger.info("Continuing without Telegram functionality")
                    self.telegram_bot = None
            else:
                logger.info("Telegram not configured, continuing without it")
            
            # Start the apartment search service (the main functionality)
            await self.search_runner.start()
            
            self.is_running = True
            logger.info("Application started successfully")
            
            # Keep the application running
            while self.is_running:
                # Check for Telegram commands if bot is available
                if self.telegram_bot:
                    await self.telegram_bot.check_for_commands()
                
                await asyncio.sleep(5)
                
        except Exception as e:
            logger.error(f"Error starting application: {e}")
            await self.stop()
    
    async def stop(self) -> None:
        """Stop all application services."""
        logger.info("Stopping application...")
        self.is_running = False
        
        # Stop services
        await self.search_runner.stop()
        
        # Stop Telegram bot if it was initialized
        if self.telegram_bot:
            try:
                await self.telegram_bot.stop()
            except Exception as e:
                logger.error(f"Error stopping Telegram bot: {e}")
        
        logger.info("Application stopped")
    
    def _setup_signal_handlers(self) -> None:
        """Setup handlers for system signals."""
        for sig in (signal.SIGINT, signal.SIGTERM):
            asyncio.get_event_loop().add_signal_handler(
                sig,
                lambda s=sig: asyncio.create_task(self._handle_signal(s))
            )
    
    async def _handle_signal(self, signal_received: int) -> None:
        """Handle system signals for graceful shutdown."""
        logger.info(f"Received exit signal {signal_received.name}...")
        await self.stop()

async def main() -> None:
    """Application entry point."""
    app = ApartmentSearchApp()
    try:
        await app.start()
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
    finally:
        await app.stop()

if __name__ == "__main__":
    try:
        # Make it visible that app is starting
        print("\n=== Wohnungssuche Application Starting ===\n")
        asyncio.run(main())
    except Exception as e:
        logger.critical(f"Unhandled exception: {e}", exc_info=True)
        sys.exit(1)