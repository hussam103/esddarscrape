import logging
import requests
import json
import datetime
import time
import random
from urllib.parse import urljoin
from models import Tender, ScrapingLog
from app import db

logger = logging.getLogger(__name__)

class EtimadScraper:
    BASE_URL = "https://tenders.etimad.sa"
    TENDER_API_URL = "https://tenders.etimad.sa/Tender/AllSupplierTendersForVisitorAsync"
    TENDER_DETAILS_BASE_URL = "https://tenders.etimad.sa/Tender/DetaielsForVisitors"
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9,ar;q=0.8',
            'Content-Type': 'application/json',
            'Origin': 'https://tenders.etimad.sa',
            'Referer': 'https://tenders.etimad.sa/Tender/Tenders/1',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
            'Connection': 'keep-alive',
        }
        self.session = requests.Session()
        # Set default language cookie to help with authentication
        self.session.cookies.set('language', 'ar-SA', domain='tenders.etimad.sa')
    
    def _prepare_request(self):
        """Prepare the request by visiting the main page to get cookies and tokens"""
        try:
            main_page = self.session.get(self.BASE_URL, headers=self.headers)
            main_page.raise_for_status()
            
            # Extract the anti-forgery token
            import re
            token_match = re.search(r'name="__RequestVerificationToken" type="hidden" value="([^"]+)"', main_page.text)
            if token_match:
                token_value = token_match.group(1)
                logger.debug(f"Extracted RequestVerificationToken: {token_value[:10]}...")
                
                # Add the token to headers
                self.headers['RequestVerificationToken'] = token_value
                
                # Also add a form field for the token
                self.session.cookies.set('__RequestVerificationToken', token_value, domain='tenders.etimad.sa')
            else:
                logger.warning("Could not extract RequestVerificationToken from the page")
            
            logger.debug("Successfully visited main page to get cookies and tokens")
            # Add a small delay to simulate human behavior
            time.sleep(random.uniform(1, 3))
        except requests.RequestException as e:
            logger.error(f"Error preparing request: {str(e)}")
            raise
    
    def _parse_datetime(self, datetime_str):
        """Parse datetime string from Etimad format to Python datetime"""
        if not datetime_str:
            return None
        
        try:
            # Try to handle various datetime formats
            formats = [
                "%Y-%m-%dT%H:%M:%S",  # ISO format
                "%Y-%m-%d %H:%M:%S",
                "%d/%m/%Y %H:%M:%S",
                "%d/%m/%Y",
                "%Y-%m-%d"
            ]
            
            for fmt in formats:
                try:
                    return datetime.datetime.strptime(datetime_str.split('.')[0], fmt)
                except ValueError:
                    continue
                    
            logger.warning(f"Could not parse datetime: {datetime_str}")
            return None
        except Exception as e:
            logger.error(f"Error parsing datetime {datetime_str}: {str(e)}")
            return None

    def scrape(self):
        """Scrape tender data from etimad.sa"""
        # Create a scraping log entry
        log_entry = ScrapingLog(status="RUNNING")
        db.session.add(log_entry)
        db.session.commit()
        
        try:
            logger.info("Starting scraping process")
            self._prepare_request()
            
            # Define the payload to get 300 tenders from page 1
            # Simplified payload based on current API requirements
            payload = {
                "PageNumber": 1,
                "PageSize": 300,
                "OrderByValue": {},
                "SelectedGovAgencies": [],
                "SearchText": "",
                "SelectedTenderActivities": []
            }
            
            logger.debug(f"Sending payload: {payload}")
            
            # Make the API request
            response = self.session.post(
                self.TENDER_API_URL,
                headers=self.headers,
                json=payload
            )
            
            # Log the response status and headers for debugging
            logger.debug(f"Response status: {response.status_code}")
            logger.debug(f"Response headers: {response.headers}")
            response.raise_for_status()
            
            data = response.json()
            
            if not data or 'Tenders' not in data:
                logger.error("Invalid response format or no tenders found")
                log_entry.status = "ERROR"
                log_entry.message = "Invalid response format or no tenders found"
                log_entry.end_time = datetime.datetime.utcnow()
                db.session.commit()
                return
            
            tenders = data.get('Tenders', [])
            logger.info(f"Found {len(tenders)} tenders")
            
            new_count = 0
            updated_count = 0
            
            for tender_data in tenders:
                tender_id = tender_data.get('IdString')
                
                if not tender_id:
                    logger.warning("Tender without ID found, skipping")
                    continue
                
                # Check if tender already exists
                existing_tender = Tender.query.filter_by(tender_id=tender_id).first()
                
                if existing_tender:
                    # Update existing tender
                    existing_tender.tender_title = tender_data.get('TenderName')
                    existing_tender.organization = tender_data.get('AgencyName')
                    existing_tender.tender_type = tender_data.get('TenderType')
                    existing_tender.reference_number = tender_data.get('TenderNumber')
                    existing_tender.main_activities = tender_data.get('MainActivities')
                    existing_tender.publication_date = self._parse_datetime(tender_data.get('ReleaseDate'))
                    existing_tender.submission_deadline = self._parse_datetime(tender_data.get('ClosingDate'))
                    existing_tender.opening_date = self._parse_datetime(tender_data.get('OpeningDate'))
                    existing_tender.duration = tender_data.get('TenderDuration')
                    existing_tender.inquiry_deadline = self._parse_datetime(tender_data.get('LastInqueryDate'))
                    existing_tender.tender_url = f"{self.TENDER_DETAILS_BASE_URL}?StenderID={tender_id}"
                    existing_tender.updated_at = datetime.datetime.utcnow()
                    updated_count += 1
                else:
                    # Create new tender
                    new_tender = Tender(
                        tender_id=tender_id,
                        tender_title=tender_data.get('TenderName'),
                        organization=tender_data.get('AgencyName'),
                        tender_type=tender_data.get('TenderType'),
                        reference_number=tender_data.get('TenderNumber'),
                        main_activities=tender_data.get('MainActivities'),
                        publication_date=self._parse_datetime(tender_data.get('ReleaseDate')),
                        submission_deadline=self._parse_datetime(tender_data.get('ClosingDate')),
                        opening_date=self._parse_datetime(tender_data.get('OpeningDate')),
                        duration=tender_data.get('TenderDuration'),
                        inquiry_deadline=self._parse_datetime(tender_data.get('LastInqueryDate')),
                        tender_url=f"{self.TENDER_DETAILS_BASE_URL}?StenderID={tender_id}"
                    )
                    db.session.add(new_tender)
                    new_count += 1
                
                # Commit in batches to avoid long transactions
                if (new_count + updated_count) % 50 == 0:
                    db.session.commit()
            
            # Final commit for any remaining tenders
            db.session.commit()
            
            # Update the log entry
            log_entry.status = "SUCCESS"
            log_entry.tenders_scraped = len(tenders)
            log_entry.new_tenders = new_count
            log_entry.updated_tenders = updated_count
            log_entry.message = f"Successfully scraped {len(tenders)} tenders. New: {new_count}, Updated: {updated_count}"
            log_entry.end_time = datetime.datetime.utcnow()
            db.session.commit()
            
            logger.info(f"Scraping completed. New tenders: {new_count}, Updated tenders: {updated_count}")
            
        except Exception as e:
            logger.error(f"Error during scraping: {str(e)}")
            log_entry.status = "ERROR"
            log_entry.message = f"Error during scraping: {str(e)}"
            log_entry.end_time = datetime.datetime.utcnow()
            db.session.commit()
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
