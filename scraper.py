"""
Direct scraper for Etimad Tenders without proxy
Uses direct connection to fetch tender data
"""
import logging
import requests
import json
import urllib3
import time
import datetime
from models import Tender, ScrapingLog
from app import db
from utils import get_saudi_now

# Set up logging
logger = logging.getLogger(__name__)

# Disable InsecureRequestWarning
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class EtimadScraper:
    """Scraper for etimad.sa tenders website"""
    
    BASE_URL = "https://tenders.etimad.sa"
    API_ENDPOINT = "/Tender/AllSupplierTendersForVisitorAsync"
    TENDER_DETAILS_URL = "/Tender/TenderDetails/"
    
    def __init__(self):
        # Set up headers to mimic a browser
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36',
            'Accept': 'application/json, text/javascript, */*; q=0.01',
            'Accept-Language': 'en-US,en;q=0.9,ar;q=0.8',
            'Referer': 'https://tenders.etimad.sa/',
            'Origin': 'https://tenders.etimad.sa',
            'X-Requested-With': 'XMLHttpRequest',
            'Connection': 'keep-alive',
        }
        
        # Initialize session
        self.session = requests.Session()
    
    def fetch_tenders(self):
        """Fetch tenders from the API for both page 1 and page 2"""
        all_tenders = []
        
        # Fetch both page 1 and page 2
        for page_num in [1, 2]:
            tenders = []
            logger.info(f"Fetching page {page_num}")
            
            # Parameters for API request
            params = {
                'pageNumber': page_num,
                'pageSize': 24,  # Fetch 24 tenders per page as requested
            }
            
            api_url = f"{self.BASE_URL}{self.API_ENDPOINT}"
            logger.info(f"Making request to {api_url} with params: {params}")
            
            try:
                # Make the request
                response = self.session.get(
                    api_url,
                    params=params,
                    headers=self.headers,
                    timeout=30,
                    verify=False  # Skip SSL verification
                )
                
                if response.status_code == 200:
                    logger.info(f"Successfully got response from API endpoint for page {page_num}")
                    
                    try:
                        # Parse the JSON response
                        api_data = json.loads(response.text)
                        logger.info(f"Successfully parsed JSON from API response for page {page_num}")
                        
                        # Extract tender data based on expected structure
                        if 'data' in api_data and isinstance(api_data['data'], list):
                            tender_items = api_data['data']
                            logger.info(f"Found {len(tender_items)} items in API response for page {page_num}")
                            
                            # Process each tender item
                            for item in tender_items:
                                try:
                                    # Extract required fields
                                    tender_id = str(item.get('tenderId', ''))
                                    tender_title = item.get('tenderName', '')
                                    organization = item.get('agencyName', 'Unknown')
                                    tender_type = item.get('tenderTypeName', 'Unknown')
                                    
                                    # Extract main activities and duration
                                    main_activities = item.get('tenderActivityName', '')
                                    duration = str(item.get('remainingDays', '')) + ' days'
                                    reference_number = item.get('tenderNumber', '')
                                    
                                    # Try to get city and price information
                                    city = item.get('branchName', '').split(' ')[-1] if item.get('branchName') else ''
                                    price = str(item.get('invitationCost', '')) if item.get('invitationCost') else str(item.get('financialFees', ''))
                                    
                                    # Process dates
                                    publication_date = None
                                    if 'submitionDate' in item and item['submitionDate']:
                                        try:
                                            date_str = item['submitionDate']
                                            if isinstance(date_str, str) and 'T' in date_str:
                                                date_str = date_str.split('T')[0]
                                            publication_date = datetime.datetime.strptime(date_str, '%Y-%m-%d')
                                        except Exception as e:
                                            logger.warning(f"Error parsing publication date: {e}")
                                    
                                    inquiry_deadline = None
                                    if 'lastEnqueriesDate' in item and item['lastEnqueriesDate']:
                                        try:
                                            date_str = item['lastEnqueriesDate']
                                            if isinstance(date_str, str) and 'T' in date_str:
                                                date_str = date_str.split('T')[0]
                                            inquiry_deadline = datetime.datetime.strptime(date_str, '%Y-%m-%d')
                                        except Exception as e:
                                            logger.warning(f"Error parsing inquiry deadline: {e}")
                                    
                                    submission_deadline = None
                                    if 'lastOfferPresentationDate' in item and item['lastOfferPresentationDate']:
                                        try:
                                            date_str = item['lastOfferPresentationDate']
                                            if isinstance(date_str, str) and 'T' in date_str:
                                                date_str = date_str.split('T')[0]
                                            submission_deadline = datetime.datetime.strptime(date_str, '%Y-%m-%d')
                                        except Exception as e:
                                            logger.warning(f"Error parsing submission deadline: {e}")
                                    
                                    opening_date = None
                                    if 'offersOpeningDate' in item and item['offersOpeningDate']:
                                        try:
                                            date_str = item['offersOpeningDate']
                                            if isinstance(date_str, str) and 'T' in date_str:
                                                date_str = date_str.split('T')[0]
                                            opening_date = datetime.datetime.strptime(date_str, '%Y-%m-%d')
                                        except Exception as e:
                                            logger.warning(f"Error parsing opening date: {e}")
                                    
                                    # Construct URL with the specific format you requested
                                    url = f"{self.BASE_URL}/Tender/DetaielsForVisitors?StenderID={tender_id}" if tender_id else ""
                                    
                                    # Only add valid tenders
                                    if tender_id and tender_title:
                                        tenders.append({
                                            'tender_id': tender_id,
                                            'tender_title': tender_title,
                                            'organization': organization,
                                            'tender_type': tender_type,
                                            'main_activities': main_activities,
                                            'duration': duration,
                                            'reference_number': reference_number,
                                            'publication_date': publication_date,
                                            'inquiry_deadline': inquiry_deadline,
                                            'submission_deadline': submission_deadline,
                                            'opening_date': opening_date,
                                            'tender_url': url,
                                            'city': city,
                                            'price': price
                                        })
                                        
                                except Exception as e:
                                    logger.error(f"Error processing tender item: {e}")
                                    continue
                        else:
                            logger.warning(f"Invalid response format for page {page_num} - no data field or not a list")
                            
                    except Exception as e:
                        logger.error(f"Error parsing API response for page {page_num}: {e}")
                else:
                    logger.error(f"Bad response status for page {page_num}: {response.status_code}")
                    logger.debug(f"Response content: {response.text[:500]}...")
                    
            except requests.exceptions.Timeout:
                logger.error(f"Request timed out for page {page_num}")
            except Exception as e:
                logger.error(f"Error fetching tenders for page {page_num}: {e}")
            
            logger.info(f"Found {len(tenders)} valid tenders on page {page_num}")
            all_tenders.extend(tenders)
            
            # Add a small delay between page requests to avoid overloading the server
            time.sleep(1)
            
        logger.info(f"Total tenders fetched from all pages: {len(all_tenders)}")
        return all_tenders
    
    def save_tenders_to_db(self, tenders):
        """Save tenders to the database using batch processing to improve reliability"""
        new_count = 0
        updated_count = 0
        batch_size = 50  # Process in smaller batches to reduce transaction time
        
        try:
            # Split tenders into smaller batches for more reliable processing
            for i in range(0, len(tenders), batch_size):
                batch = tenders[i:i+batch_size]
                batch_new = 0
                batch_updated = 0
                
                try:
                    # Process each tender in the current batch
                    for tender_data in batch:
                        try:
                            # Check if tender already exists, with better error handling for encoding issues
                            try:
                                tender_id = tender_data['tender_id']
                                # Ensure tender_id is a clean ASCII string to avoid encoding issues
                                if not isinstance(tender_id, str):
                                    tender_id = str(tender_id)
                                # Remove any potential problematic characters
                                tender_id = ''.join(c for c in tender_id if c.isalnum() or c in '-_')
                                
                                existing_tender = Tender.query.filter_by(tender_id=tender_id).first()
                            except Exception as filter_error:
                                logger.error(f"Error filtering tender: {str(filter_error)}")
                                continue
                                
                            if existing_tender:
                                # Update existing tender
                                existing_tender.tender_title = tender_data['tender_title']
                                existing_tender.organization = tender_data['organization']
                                existing_tender.tender_type = tender_data['tender_type']
                                existing_tender.main_activities = tender_data.get('main_activities', '')
                                existing_tender.duration = tender_data.get('duration', '')
                                existing_tender.reference_number = tender_data.get('reference_number', '')
                                
                                if 'publication_date' in tender_data and tender_data['publication_date']:
                                    existing_tender.publication_date = tender_data['publication_date']
                                
                                if 'inquiry_deadline' in tender_data and tender_data['inquiry_deadline']:
                                    existing_tender.inquiry_deadline = tender_data['inquiry_deadline']
                                
                                if 'submission_deadline' in tender_data and tender_data['submission_deadline']:
                                    existing_tender.submission_deadline = tender_data['submission_deadline']
                                
                                if 'opening_date' in tender_data and tender_data['opening_date']:
                                    existing_tender.opening_date = tender_data['opening_date']
                                
                                existing_tender.tender_url = tender_data['tender_url']
                                existing_tender.city = tender_data.get('city', '')
                                existing_tender.price = tender_data.get('price', '')
                                existing_tender.updated_at = get_saudi_now()
                                batch_updated += 1
                            else:
                                # Create new tender with sanitized tender_id
                                new_tender = Tender(
                                    tender_id=tender_id,  # Use the sanitized tender_id
                                    tender_title=tender_data['tender_title'],
                                    organization=tender_data['organization'],
                                    tender_type=tender_data['tender_type'],
                                    main_activities=tender_data.get('main_activities', ''),
                                    duration=tender_data.get('duration', ''),
                                    reference_number=tender_data.get('reference_number', ''),
                                    publication_date=tender_data.get('publication_date'),
                                    inquiry_deadline=tender_data.get('inquiry_deadline'),
                                    submission_deadline=tender_data.get('submission_deadline'),
                                    opening_date=tender_data.get('opening_date'),
                                    tender_url=tender_data['tender_url'],
                                    city=tender_data.get('city', ''),
                                    price=tender_data.get('price', ''),
                                    created_at=get_saudi_now(),
                                    updated_at=get_saudi_now()
                                )
                                db.session.add(new_tender)
                                batch_new += 1
                        except Exception as e:
                            # Log the error but continue with next tender
                            logger.warning(f"Error processing tender {tender_data.get('tender_id', 'unknown')}: {str(e)}")
                            # Don't rollback the entire session here, just skip this tender
                    
                    # Commit the batch
                    try:
                        db.session.commit()
                        logger.info(f"Committed batch {i//batch_size + 1} with {batch_new} new and {batch_updated} updated tenders")
                        new_count += batch_new
                        updated_count += batch_updated
                    except Exception as e:
                        logger.error(f"Error committing batch {i//batch_size + 1}: {str(e)}")
                        db.session.rollback()
                        # Continue with next batch instead of failing the entire process
                
                except Exception as e:
                    logger.error(f"Error processing batch {i//batch_size + 1}: {str(e)}")
                    db.session.rollback()
                
                # Small delay between batches to prevent database overload
                time.sleep(0.1)
            
        except Exception as e:
            logger.error(f"Error in batch processing: {e}")
            db.session.rollback()
            # Don't raise the exception, let the process continue
        
        logger.info(f"Saved {new_count} new tenders and updated {updated_count} existing tenders")
        return new_count, updated_count

    def scrape(self):
        """Main scraper method"""
        # Create a scraping log entry
        log_entry = ScrapingLog(status="RUNNING")
        db.session.add(log_entry)
        db.session.commit()
        
        try:
            logger.info("Starting scraping process")
            
            # Fetch tenders from the API
            tenders = self.fetch_tenders()
            
            if tenders:
                logger.info(f"Found {len(tenders)} valid tenders")
                
                # Save tenders to database
                new_count, updated_count = self.save_tenders_to_db(tenders)
                
                # Update log entry
                log_entry.status = "SUCCESS"
                log_entry.tenders_scraped = len(tenders)
                log_entry.new_tenders = new_count
                log_entry.updated_tenders = updated_count
                log_entry.message = f"Successfully scraped {len(tenders)} tenders. New: {new_count}, Updated: {updated_count}"
                log_entry.end_time = get_saudi_now()
                db.session.commit()
                
                logger.info(f"Scraping completed. New tenders: {new_count}, Updated tenders: {updated_count}")
            else:
                # Update log entry with zero results
                log_entry.status = "WARNING"
                log_entry.message = "No tenders found"
                log_entry.end_time = get_saudi_now()
                db.session.commit()
                
                logger.warning("No tenders found")
            
        except Exception as e:
            # Update log entry with error
            log_entry.status = "ERROR"
            log_entry.message = f"Error during scraping: {str(e)}"
            log_entry.end_time = get_saudi_now()
            db.session.commit()
            
            logger.error(f"Error during scraping: {str(e)}")
            raise

def run_scraper():
    """Run the scraper and return the results with improved error handling"""
    logger.info("Starting scraper job")
    scraper = EtimadScraper()
    try:
        # Use a try/except block to catch any errors during scraping
        # but don't propagate them to the caller to prevent application crashes
        scraper.scrape()
        logger.info("Scraper job completed successfully")
        return True
    except Exception as e:
        logger.error(f"Scraper job failed: {str(e)}")
        
        # Create an error log entry if none was created in scrape()
        try:
            log_entry = ScrapingLog(
                status="ERROR",
                message=f"Scraper job failed with error: {str(e)}",
                end_time=get_saudi_now()
            )
            db.session.add(log_entry)
            db.session.commit()
        except Exception as log_error:
            logger.error(f"Could not create error log: {str(log_error)}")
            
        return False
