"""
Test the new search_tender_by_title function to make sure it creates search URLs correctly
"""
from update_tender_urls import search_tender_by_title
import logging
import urllib.parse

# Set up logging
logging.basicConfig(level=logging.INFO)

def test_search_url_generation():
    """Test that the search URL is generated correctly for a tender title"""
    # Sample tender title from our database
    tender_title = "تأمين وتوريد شبكات ري بمنطقة القصيم"
    
    # Generate search URL
    search_url = search_tender_by_title(tender_title)
    
    # Print the results
    print(f"Tender title: {tender_title}")
    print(f"Generated search URL: {search_url}")
    
    # Check the URL components
    parsed_url = urllib.parse.urlparse(search_url)
    query_params = urllib.parse.parse_qs(parsed_url.query)
    
    print(f"Base URL: {parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}")
    print(f"Search text parameter: {query_params.get('SearchText', ['Not found'])[0]}")
    
    return search_url is not None and "SearchText" in search_url

if __name__ == "__main__":
    print("Testing search URL generation...")
    success = test_search_url_generation()
    print(f"Test {'passed' if success else 'failed'}")