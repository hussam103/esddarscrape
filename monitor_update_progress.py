#!/usr/bin/env python3
"""
Monitor the progress of tender URL updates
"""
import time
from app import app
from models import Tender

def monitor_progress():
    """Monitor the progress of tender URL updates"""
    with app.app_context():
        # Initial counts
        old_format_count = Tender.query.filter(
            Tender.tender_url.like('%DetaielsForVisitors%')
        ).count()
        
        search_format_count = Tender.query.filter(
            Tender.tender_url.like('%AllTendersForVisitor%MultipleSearch=%')
        ).count()
        
        details_format_count = Tender.query.filter(
            Tender.tender_url.like('%TenderDetails%')
        ).count()
        
        print(f"Initial Counts:")
        print(f"Tenders with old format URLs: {old_format_count}")
        print(f"Tenders with search format URLs: {search_format_count}")
        print(f"Tenders with TenderDetails URLs: {details_format_count}")
        print()
        
        # Monitor progress every 10 seconds for 5 minutes (30 checks)
        for i in range(30):
            time.sleep(10)
            
            # Get current counts
            current_old_count = Tender.query.filter(
                Tender.tender_url.like('%DetaielsForVisitors%')
            ).count()
            
            current_search_count = Tender.query.filter(
                Tender.tender_url.like('%AllTendersForVisitor%MultipleSearch=%')
            ).count()
            
            # Calculate progress
            updated = old_format_count - current_old_count
            total_updated = search_format_count + updated
            progress_percent = updated / old_format_count * 100 if old_format_count > 0 else 0
            
            print(f"Check {i+1}: Updated {updated} out of {old_format_count} tenders ({progress_percent:.1f}%)")
            print(f"Tenders with old format URLs: {current_old_count}")
            print(f"Tenders with search format URLs: {current_search_count}")
            print()
            
            # If all tenders have been updated, exit early
            if current_old_count == 0:
                print("All tenders have been updated!")
                break
        
        print("Final counts:")
        final_old_count = Tender.query.filter(
            Tender.tender_url.like('%DetaielsForVisitors%')
        ).count()
        
        final_search_count = Tender.query.filter(
            Tender.tender_url.like('%AllTendersForVisitor%MultipleSearch=%')
        ).count()
        
        print(f"Tenders with old format URLs: {final_old_count}")
        print(f"Tenders with search format URLs: {final_search_count}")
        print(f"Tenders with TenderDetails URLs: {details_format_count}")

if __name__ == "__main__":
    print("Monitoring tender URL update progress...")
    monitor_progress()
    print("\nMonitoring completed")