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
ETIMAD_SEARCH_URL = "https://tenders.etimad.sa/Tender/GetTendersForVisitor"

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
    if not tender_title or len(tender_title.strip()) < 5:
        logger.warning(f"Tender title too short or empty: '{tender_title}'")
        return None
        
    try:
        # Try to find a good search term - use the first 3-5 words of the title
        # This improves search results by focusing on distinctive words
        words = tender_title.split()
        search_term = " ".join(words[:min(5, len(words))])
        
        # Create API search parameters
        params = {
            'pageNumber': 1,
            'pageSize': 24,
            'tenderStatusId': None,
            'tenderTypeId': None,
            'tenderActivityId': None,
            'searchText': search_term,
            'fromDate': None,
            'toDate': None
        }
        
        logger.info(f"Searching for tender with term: '{search_term}'")
        logger.info(f"Search URL: {ETIMAD_SEARCH_URL}")
        
        # Make request with longer timeout for search
        response = requests.get(
            ETIMAD_SEARCH_URL, 
            params=params,
            headers=HEADERS, 
            timeout=60
        )
        
        if response.status_code != 200:
            logger.error(f"Failed to search for tender: {tender_title}. Status code: {response.status_code}")
            return None
        
        # Parse JSON response
        try:
            data = response.json()
            if not data or 'tenders' not in data or not data['tenders'] or not data['tenders'].get('data'):
                logger.warning(f"No search results found for tender: {tender_title}")
                return None
                
            # Extract tender links from JSON
            tenders_data = data['tenders']['data']
            
                # Create simulated "links" for processing similar to HTML parsing
            tender_links = []
            for t in tenders_data:
                tender_id = t.get('id')
                title = t.get('title', '')
                
                if tender_id and title:
                    # Create a simple object with the needed attributes
                    class Link:
                        def __init__(self, href, text):
                            self._href = href
                            self._text = text
                            
                        def get(self, attr):
                            if attr == 'href':
                                return self._href
                                
                        def get_text(self, strip=True):
                            return self._text
                    
                    # Create link with direct URL to tender details
                    link = Link(f"/Tender/TenderDetails/{tender_id}", title)
                    tender_links.append(link)
                    
            if not tender_links:
            logger.warning(f"No search results found for tender: {tender_title}")
            return None
        
        logger.info(f"Found {len(tender_links)} potential matches")
        
        # Find the link that most closely matches the tender title using fuzzy matching
        best_match = None
        best_match_score = 0
        
        for link in tender_links:
            link_text = link.get_text(strip=True)
            if not link_text:
                continue
                
            # Calculate similarity between link text and tender title
            # Simple similarity: count of common words
            tender_words = set(tender_title.lower().split())
            link_words = set(link_text.lower().split())
            common_words = tender_words.intersection(link_words)
            
            # Score based on common words and length similarity
            score = len(common_words) / max(len(tender_words), len(link_words))
            
            logger.debug(f"Match score for '{link_text}': {score}")
            
            if score > best_match_score:
                href = link.get('href')
                if href:
                    best_match = f"{ETIMAD_BASE_URL}{href}"
                    best_match_score = score
        
        # Consider it a match if the score is above a reasonable threshold
        if best_match and best_match_score > 0.3:  # Adjust threshold as needed
            logger.info(f"Found URL for tender with score {best_match_score:.2f}: {best_match}")
            return best_match
        else:
            # If no good match, try using the first result as a fallback
            if tender_links and tender_links[0].get('href'):
                fallback_url = f"{ETIMAD_BASE_URL}{tender_links[0].get('href')}"
                logger.warning(f"No strong match found, using first result: {fallback_url}")
                return fallback_url
            
            logger.warning(f"No matching tender found for: {tender_title}")
            return None
            
    except Exception as e:
        logger.error(f"Error searching for tender: {tender_title}. Error: {str(e)}")
        return None

def update_tender_urls(limit=None):
    """
    Update tender URLs in the database by searching for each tender on Etimad website
    
    Args:
        limit (int, optional): Maximum number of tenders to process. Default is None (process all).
        
    Returns:
        int: Number of tenders successfully updated
    """
    with app.app_context():
        try:
            # Get tenders from the database
            query = Tender.query
            
            # Apply limit if specified
            if limit and limit > 0:
                # Prioritize tenders with no URL or invalid URL format
                tenders_needing_update = query.filter(
                    (Tender.tender_url == None) | 
                    (Tender.tender_url == '') | 
                    (Tender.tender_url.like('%StenderID=%5BID%5D%'))
                ).limit(limit).all()
                
                # If we don't have enough tenders needing update, get more up to the limit
                if len(tenders_needing_update) < limit:
                    remaining = limit - len(tenders_needing_update)
                    # Exclude the ones we already got
                    ids_to_exclude = [t.id for t in tenders_needing_update]
                    more_tenders = []
                    if ids_to_exclude:
                        more_tenders = query.filter(~Tender.id.in_(ids_to_exclude)).limit(remaining).all()
                    else:
                        more_tenders = query.limit(remaining).all()
                    tenders = tenders_needing_update + more_tenders
                else:
                    tenders = tenders_needing_update
                
                logger.info(f"Processing limited set of {len(tenders)} tenders")
            else:
                # Get all tenders if no limit
                tenders = query.all()
                logger.info(f"Processing all {len(tenders)} tenders in the database")
            
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