#!/usr/bin/env python3
"""
Check the current progress of tender URL updates
"""
from app import app
from models import Tender

def check_current_progress():
    """Check the current progress of tender URL updates"""
    with app.app_context():
        # Get counts
        old_format_count = Tender.query.filter(
            Tender.tender_url.like('%DetaielsForVisitors%')
        ).count()
        
        search_format_count = Tender.query.filter(
            Tender.tender_url.like('%AllTendersForVisitor%MultipleSearch=%')
        ).count()
        
        details_format_count = Tender.query.filter(
            Tender.tender_url.like('%TenderDetails%')
        ).count()
        
        total = old_format_count + search_format_count + details_format_count
        progress_percent = search_format_count / total * 100 if total > 0 else 0
        
        print(f"Current Progress: {search_format_count}/{total} tenders converted to search URLs ({progress_percent:.1f}%)")
        print(f"Tenders with old format URLs: {old_format_count}")
        print(f"Tenders with search format URLs: {search_format_count}")
        print(f"Tenders with TenderDetails URLs: {details_format_count}")
        
        # Show a few examples of recently updated URLs
        print("\nRecently updated tenders:")
        search_tenders = Tender.query.filter(
            Tender.tender_url.like('%AllTendersForVisitor%MultipleSearch=%')
        ).order_by(Tender.updated_at.desc()).limit(3).all()
        
        for i, tender in enumerate(search_tenders):
            print(f"{i+1}. {tender.tender_id}: {tender.tender_title[:50]}...")
            print(f"   URL: {tender.tender_url}")
            print(f"   Length: {len(tender.tender_url)} characters")
            print()

if __name__ == "__main__":
    check_current_progress()