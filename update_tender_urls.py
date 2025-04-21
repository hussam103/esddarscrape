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
        
        # Create search parameters like the scraper does
        params = {
            'pageNumber': 1,
            'pageSize': 24,
            'SearchText': search_term
        }
        
        # Use the same endpoint as the scraper
        search_url = "https://tenders.etimad.sa/Tender/AllSupplierTendersForVisitorAsync"
        
        logger.info(f"Searching for tender with term: '{search_term}'")
        logger.info(f"Search URL: {search_url}")
        
        # Make request with longer timeout for search
        response = requests.get(
            search_url, 
            params=params,
            headers=HEADERS, 
            timeout=60
        )
        
        if response.status_code != 200:
            logger.error(f"Failed to search for tender: {tender_title}. Status code: {response.status_code}")
            return None
        
        # Parse JSON response
        data = response.json()
        
        # Check if we got any search results
        if not data or 'data' not in data or not data['data']:
            logger.warning(f"No search results found for tender: {tender_title}")
            return None
            
        # Extract tender data from JSON
        tenders_data = data['data']
        logger.info(f"Found {len(tenders_data)} potential matches")
        
        # Store tenders along with their match scores
        matches = []
        
        for t in tenders_data:
            tender_id = t.get('tenderId')  # This is the correct field from the API
            title = t.get('tenderName', '')
            
            if not tender_id or not title:
                continue
            
            # Calculate similarity between search result title and original tender title
            # Simple similarity: count of common words
            tender_words = set(tender_title.lower().split())
            result_words = set(title.lower().split())
            common_words = tender_words.intersection(result_words)
            
            # Score based on common words and length similarity
            score = len(common_words) / max(len(tender_words), len(result_words))
            
            # Construct the direct URL to the tender
            url = f"https://tenders.etimad.sa/Tender/TenderDetails/{tender_id}"
            
            logger.debug(f"Match score for '{title}': {score:.2f}")
            matches.append({
                'title': title,
                'url': url,
                'score': score
            })
        
        # If we didn't find any valid matches
        if not matches:
            logger.warning(f"No valid matches found for tender: {tender_title}")
            return None
            
        # Sort matches by score, highest first
        matches.sort(key=lambda x: x['score'], reverse=True)
        best_match = matches[0]
        
        # Consider it a match if the score is above a reasonable threshold
        threshold = 0.2  # Lower threshold to allow more matches
        if best_match['score'] > threshold:
            logger.info(f"Found URL for tender with score {best_match['score']:.2f}: {best_match['url']}")
            return best_match['url']
        else:
            # If no good match, use the first result as a fallback
            logger.warning(f"No strong match found, using first result: {best_match['url']}")
            return best_match['url']
            
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