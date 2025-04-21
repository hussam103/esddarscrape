"""
Test script for searching tender URLs
"""
import logging
from app import app
from update_tender_urls import search_tender_by_title

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_url_search():
    """Test the search_tender_by_title function with a few sample tender titles"""
    with app.app_context():
        sample_titles = [
            "مشروع أنظمة قياس التدفق المزدوجة بنقاط الارتباط بين أنظمة النقل وقطاع التوزيع المنطقة الجنوبية",
            "مشروع انشاء صالة تجربة المريض للمستشفيات والمراكز الصحية",
            "توريد قطع غيار وصيانة معدات وآليات البلدية",
            "تنفيذ مشروع الخدمات الاستشارية  للاشراف على مشاريع تطوير المباني",
            "اعمال تشغيل وصيانة ونظافة منشآت الاسكان"
        ]
        
        print("Testing URL search functionality...")
        
        for title in sample_titles:
            print(f"\nSearching for: '{title}'")
            url = search_tender_by_title(title)
            
            if url:
                print(f"Found URL: {url}")
            else:
                print("No URL found")
        
        print("\nTest completed")

if __name__ == "__main__":
    test_url_search()