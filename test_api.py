import requests
import json

def test_vector_search_api():
    """Test the external vector search API without authentication"""
    
    # Use a general search query to fetch tenders
    query = "construction"
    
    # Build the URL (using localhost since we're testing locally)
    url = f"http://localhost:5000/api/vector-search"
    
    # Make the request
    response = requests.get(
        url,
        params={
            "query": query,
            "limit": 10,
            "today_only": "false"  # Get all tenders, not just today's
        }
    )
    
    # Check if the request was successful
    if response.status_code == 200:
        data = response.json()
        print(f"Query: {data['query']}")
        print(f"Total results: {data['count']}")
        print("\nTop 10 Tenders by Similarity:")
        print("=" * 80)
        
        for i, item in enumerate(data['results'], 1):
            tender = item['tender']
            similarity = item['similarity']
            
            print(f"Tender #{i} - Similarity Score: {similarity:.2f}")
            print(f"Title: {tender['tender_title']}")
            print(f"Organization: {tender['organization']}")
            print(f"Type: {tender['tender_type']}")
            if tender.get('submission_deadline'):
                print(f"Deadline: {tender['submission_deadline']}")
            if tender.get('price'):
                print(f"Price: {tender['price']}")
            print("-" * 80)
        
        # Pretty print the first result to see all available fields
        print("\nFull details of first result:")
        print(json.dumps(data['results'][0], indent=2))
        
        return data
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
        return None

if __name__ == "__main__":
    test_vector_search_api()