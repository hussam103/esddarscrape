"""
Script to update tender URLs by searching for each tender on Etimad website
"""
import requests
from bs4 import BeautifulSoup
import time
import logging
import urllib.parse
from app import app, db
from models import Tender

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Etimad website base URL
ETIMAD_BASE_URL = "https://tenders.etimad.sa"
ETIMAD_SEARCH_URL = "https://tenders.etimad.sa/Tender/tendersList"

# Sleep time between requests to avoid rate limiting
SLEEP_TIME = 2

# Headers to mimic a browser
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Referer": "https://tenders.etimad.sa/",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Cache-Control": "max-age=0"
}

def search_tender_by_title(tender_title):
    """
    Search for a tender on Etimad website by its title
    
    Args:
        tender_title (str): The title of the tender to search for
        
    Returns:
        str: The tender URL if found, None otherwise
    """
    try:
        # URL encode the tender title
        encoded_title = urllib.parse.quote(tender_title)
        
        # Create search URL
        search_url = f"{ETIMAD_SEARCH_URL}?SearchText={encoded_title}"
        logger.info(f"Searching for tender: {tender_title}")
        logger.info(f"Search URL: {search_url}")
        
        # Make request
        response = requests.get(search_url, headers=HEADERS, timeout=30)
        
        if response.status_code != 200:
            logger.error(f"Failed to search for tender: {tender_title}. Status code: {response.status_code}")
            return None
        
        # Parse HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Look for tender links in the search results
        tender_links = soup.select("div.card-body h5.card-title a")
        
        if not tender_links:
            logger.warning(f"No search results found for tender: {tender_title}")
            return None
        
        # Find the link that most closely matches the tender title
        best_match = None
        for link in tender_links:
            link_text = link.get_text(strip=True)
            if link_text and (link_text.lower() in tender_title.lower() or tender_title.lower() in link_text.lower()):
                href = link.get('href')
                if href:
                    best_match = f"{ETIMAD_BASE_URL}{href}"
                    break
        
        if best_match:
            logger.info(f"Found URL for tender: {tender_title}. URL: {best_match}")
            return best_match
        else:
            logger.warning(f"No matching tender found for: {tender_title}")
            return None
            
    except Exception as e:
        logger.error(f"Error searching for tender: {tender_title}. Error: {str(e)}")
        return None

def update_tender_urls():
    """
    Update tender URLs in the database by searching for each tender on Etimad website
    """
    with app.app_context():
        try:
            # Get all tenders from the database
            tenders = Tender.query.all()
            logger.info(f"Found {len(tenders)} tenders in the database")
            
            # Initialize counters
            updated_count = 0
            failed_count = 0
            skipped_count = 0
            
            # Process each tender
            for i, tender in enumerate(tenders):
                logger.info(f"Processing tender {i+1}/{len(tenders)}: {tender.tender_id}")
                
                # Skip if the tender already has a valid URL from Etimad
                # Valid URLs could be in several formats based on the site structure
                if tender.tender_url and tender.tender_url.startswith("https://tenders.etimad.sa/") and not tender.tender_url.endswith("StenderID=%5BID%5D"):
                    logger.info(f"Tender {tender.tender_id} already has a valid URL: {tender.tender_url}")
                    skipped_count += 1
                    continue
                
                # Search for the tender by title to get the actual URL
                search_result_url = search_tender_by_title(tender.tender_title)
                
                # If we found a URL from search, use it, otherwise skip this tender
                if search_result_url:
                    direct_url = search_result_url
                else:
                    # Skip this tender if search fails - no fallback URL
                    logger.warning(f"Could not find URL for tender {tender.tender_id} by searching, skipping")
                    failed_count += 1
                    continue
                
                try:
                    # Update the tender URL
                    tender.tender_url = direct_url
                    db.session.commit()
                    updated_count += 1
                    logger.info(f"Updated URL for tender {tender.tender_id}: {direct_url}")
                except Exception as e:
                    logger.error(f"Failed to update URL for tender {tender.tender_id}: {str(e)}")
                    db.session.rollback()
                    failed_count += 1
                
                # Sleep to avoid rate limiting
                time.sleep(SLEEP_TIME)
            
            logger.info(f"Update completed. Updated: {updated_count}, Failed: {failed_count}, Skipped: {skipped_count}")
            return updated_count
            
        except Exception as e:
            logger.error(f"Error updating tender URLs: {str(e)}")
            return 0

if __name__ == "__main__":
    update_tender_urls()