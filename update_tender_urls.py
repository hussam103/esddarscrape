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
        str: The search results URL for the tender title using the MultipleSearch parameter
    """
    if not tender_title or len(tender_title.strip()) < 5:
        logger.warning(f"Tender title too short or empty: '{tender_title}'")
        return None
        
    try:
        # Use the full tender title for the search
        # URL encode the search term
        encoded_search = urllib.parse.quote(tender_title)
        
        # Generate a direct search URL using the correct format
        # This uses the AllTendersForVisitor endpoint with the MultipleSearch parameter
        base_url = "https://tenders.etimad.sa/Tender/AllTendersForVisitor"
        search_url = (f"{base_url}?&MultipleSearch={encoded_search}&TenderCategory=&TenderActivityId=0"
                      f"&ReferenceNumber=&TenderNumber=&agency=&ConditionaBookletRange=&PublishDateId=5"
                      f"&LastOfferPresentationDate=&LastOfferPresentationDate=&TenderAreasIdString="
                      f"&TenderTypeId=&TenderActivityId=&TenderSubActivityId=&AgencyCode="
                      f"&FromLastOfferPresentationDateString=&ToLastOfferPresentationDateString="
                      f"&SortDirection=DESC&Sort=SubmitionDate&PageSize=6&IsSearch=true"
                      f"&ConditionaBookletRange=&PublishDateId=5&PageNumber=1")
        
        logger.info(f"Created search URL for tender title: '{tender_title}'")
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
            # Initialize the query to specifically target tenders with the old URL format
            # that need to be updated to the search URL format
            query = Tender.query.filter(
                Tender.tender_url.like('%DetaielsForVisitors%')
            )
            
            # Apply limit if specified
            if limit and limit > 0:
                tenders = query.limit(limit).all()
                logger.info(f"Processing limited set of {len(tenders)} tenders with old format URLs")
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
                
                # Always generate a search URL based on the tender title
                # No need to extract IDs from old URLs since we're switching to search URLs
                        
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