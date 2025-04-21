"""
Test script for the vector migration process from 3072 to 1536 dimensions
"""
import requests
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_vector_migration():
    """Test the vector migration API endpoint"""
    try:
        # Endpoint for the migration
        url = "http://localhost:5000/api/embeddings/migrate-vector-size"
        
        logger.info("Starting vector migration test...")
        
        # Make the API request to trigger the migration
        response = requests.post(url)
        
        # Check if the request was successful
        if response.status_code == 200:
            data = response.json()
            logger.info(f"API responded: {data.get('message')}")
            
            # Check for expected fields in the response
            if 'status' in data and data['status'] == 'success':
                logger.info("Vector migration process started successfully")
            else:
                logger.error(f"Unexpected response: {data}")
                return False
        else:
            logger.error(f"API request failed with status code: {response.status_code}")
            logger.error(f"Response content: {response.text[:500]}")
            return False
            
        logger.info("Waiting for migration process to complete (this may take a while)...")
        
        # Wait some time for the process to potentially complete
        time.sleep(10)
        
        logger.info("Vector migration test completed. Check application logs for migration results.")
        return True
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Error connecting to API: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return False

if __name__ == "__main__":
    test_vector_migration()