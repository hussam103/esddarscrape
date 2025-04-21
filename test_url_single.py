#!/usr/bin/env python3
"""
Test updating a single tender URL to search URL
"""
import sys
from app import app, db
from models import Tender
from update_tender_urls import search_tender_by_title

def test_single_update():
    """Test updating a single tender URL to search URL"""
    with app.app_context():
        try:
            # Get one tender with DetaielsForVisitors URL to update
            tender = Tender.query.filter(
                Tender.tender_url.like('%DetaielsForVisitors%')
            ).first()
            
            if not tender:
                print("No tenders with DetaielsForVisitors URLs found.")
                return False
            
            print(f"Selected tender: {tender.tender_id}")
            print(f"Title: {tender.tender_title}")
            print(f"Old URL: {tender.tender_url}")
            
            # Generate a search URL for the tender
            search_url = search_tender_by_title(tender.tender_title)
            
            if not search_url:
                print("Failed to generate search URL.")
                return False
                
            print(f"Generated search URL: {search_url}")
            print(f"URL length: {len(search_url)} characters")
            
            # Update the tender URL
            old_url = tender.tender_url
            tender.tender_url = search_url
            db.session.commit()
            
            # Verify the update
            updated_tender = Tender.query.get(tender.id)
            print(f"Updated URL in database: {updated_tender.tender_url}")
            
            # Restore the original URL (for testing purposes)
            tender.tender_url = old_url
            db.session.commit()
            
            if len(search_url) <= 500:
                print("Test passed: URL is within 500 character limit")
                return True
            else:
                print(f"Test failed: URL exceeds 500 character limit ({len(search_url)} characters)")
                return False
            
        except Exception as e:
            print(f"Error testing URL update: {str(e)}")
            return False
            
if __name__ == "__main__":
    print("Testing single tender URL update...")
    success = test_single_update()
    print("\nTest completed")
    sys.exit(0 if success else 1)