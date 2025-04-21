"""
Test script for searching tender URLs
"""
import json
import logging
import requests
from app import app
from update_tender_urls import search_tender_by_title, HEADERS

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_url_search():
    """Test the search_tender_by_title function with a few sample tender titles"""
    with app.app_context():
        print("Testing direct API access first...")
        # Test direct API access with a simple search
        search_term = "توريد"
        
        # Use the scraper endpoint
        search_url = "https://tenders.etimad.sa/Tender/AllSupplierTendersForVisitorAsync"
        params = {
            'pageNumber': 1,
            'pageSize': 24,
            'SearchText': search_term
        }
        
        print(f"Making API request to {search_url} with params: {params}")
        
        try:
            # Make direct API request
            response = requests.get(search_url, params=params, headers=HEADERS, timeout=20)
            print(f"Response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                # Pretty print the first part of the response structure
                print("API Response Structure:")
                print(json.dumps(data.get('data', [])[:2] if data and 'data' in data else data, indent=2, ensure_ascii=False))
                
                # Count results
                results_count = len(data.get('data', [])) if data and 'data' in data else 0
                print(f"Found {results_count} results")
                
                # Show the first result
                if results_count > 0:
                    first_result = data['data'][0]
                    print("\nFirst result details:")
                    for k, v in first_result.items():
                        if k in ['stenderId', 'tenderName', 'entityName', 'activityName', 'startDate']:
                            print(f"{k}: {v}")
            else:
                print(f"Error: {response.status_code}")
                print(response.text)
        
        except Exception as e:
            print(f"Exception during API test: {str(e)}")
        
        # Now test our search function
        sample_titles = [
            "مشروع أنظمة قياس التدفق المزدوجة بنقاط الارتباط بين أنظمة النقل وقطاع التوزيع المنطقة الجنوبية",
            "اعمال توريد وتركيب مولدات كهربائية",
            "توريد قطع غيار وصيانة معدات وآليات",
            "خدمات تأمين وصيانة ونظافة",
            "استشارات هندسية"
        ]
        
        print("\n\nTesting URL search functionality with simplified titles...")
        
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