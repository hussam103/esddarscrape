import requests
import json

def test_public_api_endpoint():
    """Test if the public API endpoint is working"""
    
    # The API URL to test
    api_url = "https://d2822723-a9ab-48ba-914f-240b754899bb-00-3aty9wl5mh9za.spock.replit.dev/api/vector-search"
    
    # Parameters for the API request
    params = {
        "query": "solar power",
        "limit": 3
    }
    
    try:
        # Make the API request
        print(f"Testing API endpoint: {api_url}")
        print(f"With parameters: {params}")
        
        response = requests.get(api_url, params=params, timeout=15)
        
        # Check if the request was successful
        if response.status_code == 200:
            data = response.json()
            print(f"API is working! Status code: {response.status_code}")
            print(f"Query: {data.get('query')}")
            print(f"Results found: {data.get('count')}")
            
            # Print a sample of the results
            if data.get('results'):
                print("\nSample result:")
                sample = data['results'][0]
                print(f"Similarity score: {sample.get('similarity', 'N/A')}")
                tender = sample.get('tender', {})
                print(f"Title: {tender.get('tender_title', 'N/A')}")
                print(f"Organization: {tender.get('organization', 'N/A')}")
                
            return True
        else:
            print(f"API request failed with status code: {response.status_code}")
            print(f"Response content: {response.text[:500]}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"Error connecting to API: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False

if __name__ == "__main__":
    test_public_api_endpoint()