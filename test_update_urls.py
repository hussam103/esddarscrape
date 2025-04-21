"""
Test script for updating tender URLs
"""
import requests
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_update_urls():
    """Test the update tender URLs API endpoint"""
    try:
        # The endpoint URL
        url = "http://localhost:5000/api/update-tender-urls"
        
        logger.info("Starting URL update test...")
        
        # Make the request
        response = requests.post(url)
        
        # Check status code
        if response.status_code == 200:
            data = response.json()
            logger.info(f"Response: {data}")
            
            if 'status' in data and data['status'] == 'success':
                logger.info("URL update started successfully")
                return True
            else:
                logger.error(f"Unexpected response: {data}")
                return False
        else:
            logger.error(f"Request failed with status code: {response.status_code}")
            logger.error(f"Response content: {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return False
    
if __name__ == "__main__":
    test_update_urls()