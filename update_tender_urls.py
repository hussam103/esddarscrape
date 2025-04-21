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
    Create a search URL for a tender on Etimad website based on its title
    
    Args:
        tender_title (str): The title of the tender to search for
        
    Returns:
        str: The search results URL for the tender title
    """
    if not tender_title or len(tender_title.strip()) < 5:
        logger.warning(f"Tender title too short or empty: '{tender_title}'")
        return None
        
    try:
        # Take the first 5 words (or all words if fewer) for the search term
        words = tender_title.split()
        search_term = " ".join(words[:min(5, len(words))])
        
        # URL encode the search term
        encoded_search = urllib.parse.quote(search_term)
        
        # Generate a direct search URL with the encoded search term
        # This links directly to the search results page for the tender title
        search_url = f"https://tenders.etimad.sa/Tender/List?SearchText={encoded_search}"
        
        logger.info(f"Created search URL for tender title: '{search_term}'")
        logger.info(f"Search URL: {search_url}")
        
        return search_url
            
    except Exception as e:
        logger.error(f"Error generating search URL for tender: {tender_title}. Error: {str(e)}")
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
                
                # Skip if tender already has a TenderDetails URL (which is the preferred format)
                if tender.tender_url and "TenderDetails" in tender.tender_url:
                    logger.info(f"Tender {tender.tender_id} already has a TenderDetails URL: {tender.tender_url}")
                    skipped_count += 1
                    continue
                
                # Process tenders with DetaielsForVisitors URLs to upgrade them to TenderDetails format
                # Or process tenders with no URLs or placeholder URLs
                
                # If the tender already has a DetaielsForVisitors URL, try to extract the ID and create a direct URL
                if tender.tender_url and "DetaielsForVisitors" in tender.tender_url:
                    # Try to extract the tender ID from the existing URL
                    try:
                        import re
                        tender_id_match = re.search(r'StenderID=(\d+)', tender.tender_url)
                        
                        if tender_id_match:
                            extracted_id = tender_id_match.group(1)
                            # Create a direct URL using the extracted ID
                            direct_url = f"https://tenders.etimad.sa/Tender/TenderDetails/{extracted_id}"
                            logger.info(f"Created direct URL from existing URL: {direct_url}")
                            
                            # Skip the search step
                            logger.info(f"Skipping search for tender {tender.tender_id} as we extracted the ID from existing URL")
                            
                            # Go to update step
                            try:
                                # Update the tender URL
                                tender.tender_url = direct_url
                                db.session.commit()
                                updated_count += 1
                                logger.info(f"Updated URL for tender {tender.tender_id}: {direct_url}")
                                # Continue to next tender
                                continue
                            except Exception as e:
                                logger.error(f"Failed to update URL for tender {tender.tender_id}: {str(e)}")
                                db.session.rollback()
                                failed_count += 1
                                # Continue to next tender
                                continue
                    except Exception as e:
                        logger.error(f"Error extracting ID from URL {tender.tender_url}: {str(e)}")
                        # Continue with search as fallback
                        pass
                        
                # Search for the tender by title to get a search URL
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