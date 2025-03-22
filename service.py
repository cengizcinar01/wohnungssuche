"""Service layer for the apartment search application."""
import asyncio
import logging
from typing import Dict, List, Optional, Any, Set
import time
from datetime import datetime

from config import config
from database import DatabaseManager, ListingRepository
from scraper import ApartmentScraper, WebDriverFactory
from notifier import NotificationService, create_notifier
# removed analyze_description import as it's no longer used

logger = logging.getLogger(__name__)

class ApartmentService:
    """Core service for the apartment search application."""
    
    def __init__(self, 
                 db_repo: ListingRepository,
                 notifier: Optional[NotificationService] = None):
        """
        Initialize the apartment service.
        
        Args:
            db_repo: Repository for database operations
            notifier: Optional notification service
        """
        self.db_repo = db_repo
        self.notifier = notifier
        self.processed_ids: Set[str] = set()
    
    async def process_listing(self, basic_info: Dict[str, Any], scraper: ApartmentScraper) -> bool:
        """
        Process a single apartment listing by fetching full details,
        saving to database, and sending notifications.
        
        Args:
            basic_info: Basic listing information from search results
            scraper: Scraper instance to fetch additional details
        
        Returns:
            True if listing was processed successfully
        """
        listing_id = basic_info['listing_id']
        
        if listing_id in self.processed_ids or self.db_repo.listing_exists(listing_id):
            logger.debug(f"Listing {listing_id} already processed, skipping")
            return False
        
        try:
            logger.info(f"Processing listing: {listing_id} - {basic_info.get('title', '')}")
            
            # Get full description if available
            full_description = scraper.get_full_listing_description(basic_info['url'])
            if full_description:
                basic_info['description'] = full_description
            
            # Set all listings as suitable since we're not filtering
            basic_info['status'] = 'suitable'
            
            # Save to database
            self.db_repo.save_listing(basic_info)
            logger.info(f"Saved listing {listing_id}")
            
            # Send notification for all listings
            if self.notifier:
                await self.notifier.send_listing_notification(basic_info)
                logger.info(f"Notification sent for listing: {listing_id}")
            
            # Mark as processed
            self.db_repo.mark_listing_processed(listing_id)
            self.processed_ids.add(listing_id)
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing listing {listing_id}: {str(e)}")
            if basic_info.get('listing_id'):
                self.db_repo.mark_listing_error(listing_id, str(e))
            return False
    
    async def search_apartments(self) -> Dict[str, int]:
        """
        Perform a complete apartment search cycle.
        
        Returns:
            Dictionary with statistics about the search
        """
        stats = {
            'total_found': 0,
            'processed': 0,
            'errors': 0,
        }
        
        start_time = time.time()
        logger.info("Starting new search cycle...")
        
        # Add retry logic for scraper initialization
        max_scraper_retries = 3
        scraper_retry_count = 0
        
        while scraper_retry_count < max_scraper_retries:
            try:
                with ApartmentScraper() as scraper:
                    try:
                        # Initialize the scraper with consent acceptance
                        scraper.driver.get("https://www.kleinanzeigen.de")
                        scraper.handle_consent_banner()
                    except Exception as e:
                        logger.error(f"Failed to initialize scraper: {e}")
                        raise
                    
                    # Process each search URL (district)
                    for url in config.SEARCH_URLS:
                        try:
                            # Get basic listings data from search results
                            listings_data = scraper.check_search_results(url)
                            stats['total_found'] += len(listings_data)
                            
                            # Process each listing
                            for basic_info in listings_data:
                                try:
                                    await self.process_listing(basic_info, scraper)
                                    stats['processed'] += 1
                                except Exception as e:
                                    logger.error(f"Error processing individual listing: {str(e)}")
                                    stats['errors'] += 1
                                
                                # Brief pause between listings
                                await asyncio.sleep(1)
                            
                        except Exception as e:
                            logger.error(f"Error checking search URL {url}: {str(e)}")
                            stats['errors'] += 1
                        
                        # Pause between districts to avoid rate limiting
                        await asyncio.sleep(2)
                
                # If we got here without exception, break out of the retry loop
                break
                
            except Exception as e:
                scraper_retry_count += 1
                logger.error(f"Scraper failed (attempt {scraper_retry_count}/{max_scraper_retries}): {e}")
                if scraper_retry_count >= max_scraper_retries:
                    logger.error("Maximum scraper retry attempts reached, giving up")
                else:
                    logger.info(f"Retrying with a new scraper instance in 10 seconds...")
                    await asyncio.sleep(10)
        
        # Log statistics
        duration = time.time() - start_time
        logger.info(
            f"Search cycle completed in {duration:.1f}s. "
            f"Found: {stats['total_found']}, "
            f"Processed: {stats['processed']}, "
            f"Errors: {stats['errors']}"
        )
        
        return stats

class ApartmentSearchRunner:
    """Runner for continuous apartment searching."""
    
    def __init__(self):
        """Initialize the search runner with necessary services."""
        # Database
        self.db_manager = DatabaseManager()
        self.listing_repo = ListingRepository(self.db_manager)
        
        # Notifier
        self.notifier = create_notifier()
        
        # Core service
        self.apartment_service = ApartmentService(
            db_repo=self.listing_repo,
            notifier=self.notifier
        )
        
        # Control flags
        self.is_running = False
        self.search_task = None
    
    async def start(self) -> None:
        """Start the apartment search service."""
        if self.is_running:
            logger.warning("Search service is already running")
            return
        
        self.is_running = True
        logger.info("Starting apartment search service")
        
        # Start the continuous search loop
        self.search_task = asyncio.create_task(self._search_loop())
    
    async def stop(self) -> None:
        """Stop the apartment search service."""
        if not self.is_running:
            logger.warning("Search service is not running")
            return
        
        logger.info("Stopping apartment search service")
        self.is_running = False
        
        if self.search_task:
            self.search_task.cancel()
            try:
                await self.search_task
            except asyncio.CancelledError:
                pass
        
        # Clean up
        self.db_manager.close()
        logger.info("Apartment search service stopped")
    
    async def _search_loop(self) -> None:
        """Continuous search loop with configured interval."""
        consecutive_failures = 0
        max_consecutive_failures = 3
        
        while self.is_running:
            try:
                # Attempt a search cycle
                stats = await self.apartment_service.search_apartments()
                
                # Reset failure counter on success
                if consecutive_failures > 0:
                    logger.info(f"Search recovered after {consecutive_failures} consecutive failures")
                    consecutive_failures = 0
                
            except Exception as e:
                # Increment failure counter
                consecutive_failures += 1
                logger.error(f"Error in search cycle ({consecutive_failures}/{max_consecutive_failures}): {str(e)}")
                
                # Increase wait time after failures to avoid hammering the site
                if consecutive_failures >= max_consecutive_failures:
                    logger.critical(f"Too many consecutive failures ({consecutive_failures}). Taking a longer break.")
                    await asyncio.sleep(config.CHECK_INTERVAL * 2)  # Longer break after multiple failures
                    consecutive_failures = 0  # Reset after the long break
            
            # Normal wait interval between cycles
            wait_time = config.CHECK_INTERVAL
            logger.info(f"Waiting {wait_time} seconds until next search cycle...")
            await asyncio.sleep(wait_time)