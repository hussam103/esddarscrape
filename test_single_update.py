"""
Test updating a single tender's URL with our new search URL format
"""
from app import app, db
from models import Tender
from update_tender_urls import search_tender_by_title

def update_single_tender():
    """Update a single tender with the new search URL format"""
    with app.app_context():
        # Get a tender with DetaielsForVisitors URL
        tender = Tender.query.filter(Tender.tender_url.like('%DetaielsForVisitors%')).first()
        
        if not tender:
            print("No tender with DetaielsForVisitors URL found")
            return False
        
        # Print the tender details before update
        print(f"Tender ID: {tender.tender_id}")
        print(f"Tender Title: {tender.tender_title}")
        print(f"Old URL: {tender.tender_url}")
        
        # Generate the new search URL
        new_url = search_tender_by_title(tender.tender_title)
        
        if not new_url:
            print("Failed to generate search URL")
            return False
            
        # Print the new URL
        print(f"New URL: {new_url}")
        
        # Update the tender URL
        tender.tender_url = new_url
        db.session.commit()
        
        # Verify the update
        updated_tender = Tender.query.get(tender.id)
        print(f"Updated URL in database: {updated_tender.tender_url}")
        
        return updated_tender.tender_url == new_url

if __name__ == "__main__":
    print("Testing single tender URL update...")
    success = update_single_tender()
    print(f"Test {'passed' if success else 'failed'}")