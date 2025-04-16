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
        """Fetch tenders from the API"""
        tenders = []
        
        # Just get page 1 with a large batch size
        page_num = 1
        logger.info(f"Fetching page {page_num}")
        
        # Parameters for API request
        params = {
            'pageNumber': page_num,
            'pageSize': 300,  # Get 300 tenders at once
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
                logger.info(f"Successfully got response from API endpoint")
                
                try:
                    # Parse the JSON response
                    api_data = json.loads(response.text)
                    logger.info(f"Successfully parsed JSON from API response")
                    
                    # Extract tender data based on expected structure
                    if 'data' in api_data and isinstance(api_data['data'], list):
                        tender_items = api_data['data']
                        logger.info(f"Found {len(tender_items)} items in API response")
                        
                        # Process each tender item
                        for item in tender_items:
                            try:
                                # Extract required fields
                                tender_id = str(item.get('tenderId', ''))
                                tender_title = item.get('tenderName', '')
                                organization = item.get('agencyName', 'Unknown')
                                tender_type = item.get('tenderTypeName', 'Unknown')
                                
                                # Extract main activities and duration
                                main_activities = item.get('mainActivity', '')
                                duration = item.get('tenderDuration', '')
                                reference_number = item.get('tenderNumber', '')
                                
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
                                if 'lastEnqueryDate' in item and item['lastEnqueryDate']:
                                    try:
                                        date_str = item['lastEnqueryDate']
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
                                if 'openingDate' in item and item['openingDate']:
                                    try:
                                        date_str = item['openingDate']
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
                                        'tender_url': url
                                    })
                                    
                            except Exception as e:
                                logger.error(f"Error processing tender item: {e}")
                                continue
                    else:
                        logger.warning(f"Invalid response format - no data field or not a list")
                        
                except Exception as e:
                    logger.error(f"Error parsing API response: {e}")
            else:
                logger.error(f"Bad response status: {response.status_code}")
                logger.debug(f"Response content: {response.text[:500]}...")
                
        except requests.exceptions.Timeout:
            logger.error(f"Request timed out")
        except Exception as e:
            logger.error(f"Error fetching tenders: {e}")
            
        return tenders
    
    def save_tenders_to_db(self, tenders):
        """Save tenders to the database"""
        new_count = 0
        updated_count = 0
        
        try:
            for tender_data in tenders:
                # Check if tender already exists
                existing_tender = Tender.query.filter_by(tender_id=tender_data['tender_id']).first()
                
                if existing_tender:
                    # Update existing tender
                    existing_tender.tender_title = tender_data['tender_name']
                    existing_tender.organization = tender_data['agency']
                    existing_tender.tender_type = tender_data['category']
                    existing_tender.city = tender_data.get('city', 'Unknown')
                    existing_tender.price = tender_data.get('price', '')
                    
                    if 'start_date' in tender_data and tender_data['start_date']:
                        existing_tender.publication_date = tender_data['start_date']
                    
                    if 'end_date' in tender_data and tender_data['end_date']:
                        existing_tender.submission_deadline = tender_data['end_date']
                    
                    existing_tender.tender_url = tender_data['url']
                    existing_tender.updated_at = datetime.datetime.utcnow()
                    updated_count += 1
                else:
                    # Create new tender
                    new_tender = Tender(
                        tender_id=tender_data['tender_id'],
                        tender_title=tender_data['tender_name'],
                        organization=tender_data['agency'],
                        tender_type=tender_data['category'],
                        city=tender_data.get('city', 'Unknown'),
                        price=tender_data.get('price', ''),
                        publication_date=tender_data.get('start_date'),
                        submission_deadline=tender_data.get('end_date'),
                        tender_url=tender_data['url'],
                        # Set default values for other required fields
                        reference_number='',
                        main_activities='',
                        duration='',
                        created_at=datetime.datetime.utcnow(),
                        updated_at=datetime.datetime.utcnow()
                    )
                    db.session.add(new_tender)
                    new_count += 1
                
                # Commit in batches to avoid long transactions
                if (new_count + updated_count) % 50 == 0:
                    db.session.commit()
            
            # Final commit for any remaining tenders
            db.session.commit()
            
        except Exception as e:
            logger.error(f"Error saving tenders to database: {e}")
            db.session.rollback()
            raise
        
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
                log_entry.end_time = datetime.datetime.utcnow()
                db.session.commit()
                
                logger.info(f"Scraping completed. New tenders: {new_count}, Updated tenders: {updated_count}")
            else:
                # Update log entry with zero results
                log_entry.status = "WARNING"
                log_entry.message = "No tenders found"
                log_entry.end_time = datetime.datetime.utcnow()
                db.session.commit()
                
                logger.warning("No tenders found")
            
        except Exception as e:
            # Update log entry with error
            log_entry.status = "ERROR"
            log_entry.message = f"Error during scraping: {str(e)}"
            log_entry.end_time = datetime.datetime.utcnow()
            db.session.commit()
            
            logger.error(f"Error during scraping: {str(e)}")
            raise

def run_scraper():
    """Run the scraper and return the results"""
    logger.info("Starting scraper job")
    scraper = EtimadScraper()
    try:
        scraper.scrape()
        logger.info("Scraper job completed successfully")
    except Exception as e:
        logger.error(f"Scraper job failed: {str(e)}")
