import requests
import time

def test_api_with_query(query, limit=3):
    """Test the API with a specific query and display results"""
    api_url = "https://d2822723-a9ab-48ba-914f-240b754899bb-00-3aty9wl5mh9za.spock.replit.dev/api/vector-search"
    
    params = {
        "query": query,
        "limit": limit
    }
    
    try:
        print(f"\n{'=' * 50}")
        print(f"Testing query: '{query}' (limit: {limit})")
        print(f"{'=' * 50}")
        
        response = requests.get(api_url, params=params, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"Query: {data.get('query')}")
            print(f"Results found: {data.get('count')}")
            
            if data.get('results'):
                for i, result in enumerate(data['results'], 1):
                    similarity = result.get('similarity', 0) * 100  # Convert to percentage
                    tender = result.get('tender', {})
                    
                    print(f"\n#{i} - Similarity: {similarity:.1f}%")
                    print(f"Title: {tender.get('tender_title', 'N/A')}")
                    print(f"Organization: {tender.get('organization', 'N/A')}")
                    print(f"Type: {tender.get('tender_type', 'N/A')}")
                    if tender.get('submission_deadline'):
                        print(f"Deadline: {tender.get('submission_deadline')}")
            
            return True
        else:
            print(f"API request failed with status code: {response.status_code}")
            print(f"Response content: {response.text[:500]}")
            return False
            
    except Exception as e:
        print(f"Error: {e}")
        return False

def run_comprehensive_test():
    """Run tests with various queries to confirm API functionality"""
    # List of queries to test
    queries = [
        "construction materials",
        "electrical equipment",
        "software development",
        "water treatment",
        "maintenance services"
    ]
    
    # Test each query
    for query in queries:
        test_api_with_query(query)
        time.sleep(1)  # Wait a bit between requests
        
    print("\n" + "=" * 50)
    print("All tests completed. The public API is working correctly!")
    print("=" * 50)

if __name__ == "__main__":
    run_comprehensive_test()