"""
Test script for updating tender URLs
"""
import logging
from app import app
from update_tender_urls import update_tender_urls
from models import Tender, db

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_update_urls():
    """Test the update tender URLs API endpoint"""
    with app.app_context():
        print("Testing tender URL update process...")
        
        # Get count of tenders with old DetaielsForVisitors URLs before update
        old_format_urls_before = (
            Tender.query.filter(
                Tender.tender_url.like('%DetaielsForVisitors%')
            ).count()
        )
        print(f"Tenders with old format URLs before update: {old_format_urls_before}")
        
        # Get count of tenders with no URL or placeholder URL before update
        missing_urls_before = (
            Tender.query.filter(
                (Tender.tender_url == None) | 
                (Tender.tender_url == '') | 
                (Tender.tender_url.like('%StenderID=%5BID%5D%'))
            ).count()
        )
        print(f"Tenders with missing or placeholder URLs before update: {missing_urls_before}")
        
        # Limit to 5 tenders to avoid timeouts
        limit = 5
        print(f"Updating up to {limit} tender URLs...")
        
        # Run the update function
        updated_count = update_tender_urls(limit=limit)
        
        print(f"Successfully updated {updated_count} tender URLs")
        
        # Get count of tenders with old DetaielsForVisitors URLs after update
        old_format_urls_after = (
            Tender.query.filter(
                Tender.tender_url.like('%DetaielsForVisitors%')
            ).count()
        )
        print(f"Tenders with old format URLs after update: {old_format_urls_after}")
        
        # Get count of tenders with no URL or placeholder URL after update
        missing_urls_after = (
            Tender.query.filter(
                (Tender.tender_url == None) | 
                (Tender.tender_url == '') | 
                (Tender.tender_url.like('%StenderID=%5BID%5D%'))
            ).count()
        )
        print(f"Tenders with missing or placeholder URLs after update: {missing_urls_after}")
        
        # Get count of tenders with new TenderDetails URLs after update
        new_format_urls_after = (
            Tender.query.filter(
                Tender.tender_url.like('%TenderDetails%')
            ).count()
        )
        print(f"Tenders with new format URLs after update: {new_format_urls_after}")
        
        # Get a few examples of updated URLs
        updated_tenders = Tender.query.filter(
            Tender.tender_url.like('https://tenders.etimad.sa/Tender/TenderDetails/%')
        ).limit(3).all()
        
        print("\nExample updated tender URLs:")
        for tender in updated_tenders:
            print(f"- {tender.tender_id}: {tender.tender_title[:50]}... --> {tender.tender_url}")
        
        print("\nTest completed")

if __name__ == "__main__":
    test_update_urls()