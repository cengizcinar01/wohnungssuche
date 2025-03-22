"""Scraper module for apartment listing retrieval."""
import asyncio
import re
import time
from typing import Dict, List, Optional, Tuple, Any
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    StaleElementReferenceException
)

from config import config
from utils import retry


class WebDriverFactory:
    """Factory class for creating WebDriver instances."""
    
    @staticmethod
    def create_chrome_driver() -> webdriver.Chrome:
        """Create and configure a Chrome WebDriver instance."""
        options = Options()
        
        # Use system Chromium
        options.binary_location = "/usr/bin/chromium"
        
        # Common options
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        
        if config.HEADLESS_MODE:
            options.add_argument('--headless=new')  # new headless mode for Chrome
            # Additional headless optimizations
            options.add_argument('--disable-extensions')
            options.add_argument('--disable-setuid-sandbox')
            options.add_argument('--disable-software-rasterizer')
            options.add_argument('--window-size=1920,1080')
        else:
            options.add_argument('--start-maximized')
        
        service = Service(executable_path="/usr/bin/chromedriver")
        driver = webdriver.Chrome(service=service, options=options)
        driver.set_page_load_timeout(config.PAGE_LOAD_TIMEOUT)
        return driver


class ApartmentScraper:
    """Scraper for apartment listings."""
    
    def __init__(self):
        """Initialize the scraper with a WebDriver instance."""
        self.driver = WebDriverFactory.create_chrome_driver()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with driver cleanup."""
        if self.driver:
            self.driver.quit()
    
    def handle_consent_banner(self) -> None:
        """Handle the GDPR consent banner if it appears."""
        try:
            accept_button = WebDriverWait(self.driver, config.ELEMENT_TIMEOUT).until(
                EC.element_to_be_clickable((By.ID, "gdpr-banner-accept"))
            )
            print("Accepting consent banner...")
            accept_button.click()
            time.sleep(1)  # Wait for banner to disappear
        except TimeoutException:
            print("No consent banner found or already accepted")
    
    @retry(max_retries=3, delay=2)
    def get_full_listing_description(self, url: str) -> Optional[str]:
        """Get the full description from the listing page."""
        try:
            print(f"Fetching description...")
            
            # Load the page
            self.driver.get(url)
            time.sleep(2)  # Wait for initial load
            
            # Wait for description container
            description_container = WebDriverWait(self.driver, config.ELEMENT_TIMEOUT).until(
                EC.presence_of_element_located((By.ID, "viewad-description"))
            )
            
            # Wait a bit more for content to load
            time.sleep(1)
            
            # Get description text
            description_elem = description_container.find_element(By.ID, "viewad-description-text")
            description = description_elem.text.strip()
            
            if description:
                print("Successfully fetched description")
                return description
                
        except TimeoutException:
            print("Timeout while fetching description")
            raise
        except StaleElementReferenceException:
            print("Stale element encountered")
            raise
        except Exception as e:
            print(f"Error fetching description: {str(e)}")
            raise
        
        return None
    
    def check_search_results(self, url: str) -> List[Dict[str, Any]]:
        """
        Check search results for a specific district and return basic listing data.
        This method only collects the data visible on the search results page.
        """
        listings_data = []
        
        try:
            print(f"\n{'='*50}\n")
            print(f"Accessing URL: {url}")
            
            self.driver.get(url)
            time.sleep(2)  # Short wait for initial load
            
            district = url.split("/")[4].upper()
            print(f"Checking: {district}")
            
            # First check if there are no results
            try:
                no_results = WebDriverWait(self.driver, config.ELEMENT_TIMEOUT).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "span.breadcrump-summary"))
                )
                if "keine Ergebnisse" in no_results.text:
                    print(f"No listings found in {district}")
                    return []
            except TimeoutException:
                pass  # Continue with normal processing if no "no results" message found
            
            # Wait for the search results container
            try:
                results_container = WebDriverWait(self.driver, config.ELEMENT_TIMEOUT).until(
                    EC.presence_of_element_located((By.ID, "srchrslt-adtable"))
                )
            except TimeoutException:
                print(f"No results container found in {district}")
                return []
            
            # Get all valid listing articles
            listing_articles = results_container.find_elements(By.CSS_SELECTOR, "article.aditem")
            if not listing_articles:
                print(f"No listings found in {district}")
                return []
                
            print(f"Found {len(listing_articles)} listings to check")
            
            # Collect all listing data
            for article in listing_articles:
                try:
                    # Get listing ID
                    listing_id = article.get_attribute("data-adid")
                    if not listing_id:
                        continue
                    
                    # Get listing URL
                    listing_path = article.get_attribute("data-href")
                    if not listing_path:
                        continue
                    
                    listing_url = f"https://www.kleinanzeigen.de{listing_path}"
                    
                    # Extract all basic info
                    basic_info = {
                        'listing_id': listing_id,
                        'url': listing_url,
                        'title': '',
                        'price': None,
                        'size': None,
                        'rooms': None,
                        'location': '',
                        'description': ''
                    }
                    
                    # Use WebDriverWait for each element to handle stale elements
                    wait = WebDriverWait(self.driver, 5)
                    
                    try:
                        # Title
                        title_elem = wait.until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, f"article[data-adid='{listing_id}'] a.ellipsis"))
                        )
                        basic_info['title'] = title_elem.text.strip()
                        
                        # Price
                        price_elem = wait.until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, f"article[data-adid='{listing_id}'] p.aditem-main--middle--price-shipping--price"))
                        )
                        price_text = price_elem.text.strip()
                        basic_info['price'] = float(re.sub(r'[^\d.,]', '', price_text).replace(',', '.'))
                        
                        # Size and rooms from simpletags
                        simpletags = article.find_elements(By.CSS_SELECTOR, "span.simpletag")
                        for tag in simpletags:
                            text = tag.text.strip()
                            if 'm²' in text:
                                basic_info['size'] = float(re.sub(r'[^\d.,]', '', text).replace(',', '.'))
                            elif 'Zi.' in text:
                                # Clean up the room number text and remove any trailing periods
                                cleaned_text = text.rstrip('.')  # Remove trailing periods
                                number_only = re.sub(r'[^\d.,]', '', cleaned_text).replace(',', '.')
                                basic_info['rooms'] = float(number_only)
                        
                        # Location
                        location_elem = wait.until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, f"article[data-adid='{listing_id}'] div.aditem-main--top--left"))
                        )
                        basic_info['location'] = location_elem.text.strip()
                        
                        # Preview description
                        try:
                            desc_elem = wait.until(
                                EC.presence_of_element_located((By.CSS_SELECTOR, f"article[data-adid='{listing_id}'] p.aditem-main--middle--description"))
                            )
                            basic_info['description'] = desc_elem.text.strip()
                        except (TimeoutException, NoSuchElementException):
                            pass
                        
                        listings_data.append(basic_info)
                        print(f"Collected data for listing: {listing_id}")
                        
                    except (TimeoutException, NoSuchElementException, StaleElementReferenceException) as e:
                        print(f"Warning: Could not extract some basic info for listing {listing_id}: {str(e)}")
                        continue
                    
                except Exception as e:
                    print(f"Error collecting listing data: {str(e)}")
                    continue
                
        except Exception as e:
            print(f"Error checking {url}: {str(e)}")
        
        print(f"\n{'='*50}\n")
        return listings_data