#!/usr/bin/env python3
"""
Check count of different URL formats in the database
"""
from app import app
from models import Tender

def check_url_counts():
    """Check counts of different URL formats in the database"""
    with app.app_context():
        # Count tenders with DetaielsForVisitors URLs
        old_format_count = Tender.query.filter(
            Tender.tender_url.like('%DetaielsForVisitors%')
        ).count()
        
        # Count tenders with TenderDetails URLs
        details_format_count = Tender.query.filter(
            Tender.tender_url.like('%TenderDetails%')
        ).count()
        
        # Count tenders with AllTendersForVisitor search URLs
        search_format_count = Tender.query.filter(
            Tender.tender_url.like('%AllTendersForVisitor%MultipleSearch=%')
        ).count()
        
        print(f"Tenders with DetaielsForVisitors URLs: {old_format_count}")
        print(f"Tenders with TenderDetails URLs: {details_format_count}")
        print(f"Tenders with AllTendersForVisitor search URLs: {search_format_count}")
        
        # Show a few examples of search URLs
        print("\nExample search URLs:")
        search_tenders = Tender.query.filter(
            Tender.tender_url.like('%AllTendersForVisitor%MultipleSearch=%')
        ).limit(3).all()
        
        for i, tender in enumerate(search_tenders):
            print(f"{i+1}. {tender.tender_id}: {tender.tender_title[:50]}...")
            print(f"   URL: {tender.tender_url}")
            print(f"   Length: {len(tender.tender_url)} characters")
            print()

if __name__ == "__main__":
    check_url_counts()