#!/usr/bin/env python3
"""
Test script for updating tender URLs to search URLs
"""
import sys
from app import app, db
from models import Tender
from update_tender_urls import update_tender_urls

def test_update_urls():
    """Test updating tender URLs to search URLs"""
    with app.app_context():
        try:
            # Get count of tenders with DetaielsForVisitors format before update
            old_format_count_before = Tender.query.filter(
                Tender.tender_url.like('%DetaielsForVisitors%')
            ).count()
            
            # Get count of tenders with TenderDetails format before update
            details_format_count_before = Tender.query.filter(
                Tender.tender_url.like('%TenderDetails%')
            ).count()
            
            # Get count of search URL format before update
            search_format_count_before = Tender.query.filter(
                Tender.tender_url.like('%List?SearchText=%')
            ).count()
            
            print(f"Tenders with DetaielsForVisitors URLs before update: {old_format_count_before}")
            print(f"Tenders with TenderDetails URLs before update: {details_format_count_before}")
            print(f"Tenders with search URLs before update: {search_format_count_before}")
            
            # Update a limited number of tender URLs, specifically targeting DetaielsForVisitors URLs
            limit = 5
            print(f"Updating up to {limit} tender URLs...")
            
            # Get the first few tenders with the old format URL
            tenders_to_update = Tender.query.filter(
                Tender.tender_url.like('%DetaielsForVisitors%')
            ).limit(limit).all()
            
            for tender in tenders_to_update:
                print(f"- Before: {tender.tender_id}: {tender.tender_title[:40]}... --> {tender.tender_url}")
            
            # Run the update
            updated_count = update_tender_urls(limit=limit)
            print(f"Successfully updated {updated_count} tender URLs")
            
            # Re-fetch the same tenders to see their new URLs
            updated_tenders = []
            for tender in tenders_to_update:
                updated = Tender.query.get(tender.id)
                updated_tenders.append(updated)
                print(f"- After: {updated.tender_id}: {updated.tender_title[:40]}... --> {updated.tender_url}")
            
            # Get count of tenders with DetaielsForVisitors format after update
            old_format_count_after = Tender.query.filter(
                Tender.tender_url.like('%DetaielsForVisitors%')
            ).count()
            
            # Get count of tenders with TenderDetails format after update
            details_format_count_after = Tender.query.filter(
                Tender.tender_url.like('%TenderDetails%')
            ).count()
            
            # Get count of search URL format after update
            search_format_count_after = Tender.query.filter(
                Tender.tender_url.like('%List?SearchText=%')
            ).count()
            
            print(f"Tenders with DetaielsForVisitors URLs after update: {old_format_count_after}")
            print(f"Tenders with TenderDetails URLs after update: {details_format_count_after}")
            print(f"Tenders with search URLs after update: {search_format_count_after}")
            
            return True
            
        except Exception as e:
            print(f"Error testing tender URL update: {str(e)}")
            return False
            
if __name__ == "__main__":
    print("Testing tender URL update process...")
    success = test_update_urls()
    print("\nTest completed")
    sys.exit(0 if success else 1)