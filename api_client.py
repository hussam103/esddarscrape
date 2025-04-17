"""
API Client for connecting to the Vector Search API
"""
import requests
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import json

logger = logging.getLogger(__name__)

class VectorSearchAPIClient:
    """Client for connecting to the Vector Search API"""
    
    BASE_URL = "https://d2822723-a9ab-48ba-914f-240b754899bb-00-3aty9wl5mh9za.spock.replit.dev"
    VECTOR_SEARCH_ENDPOINT = "/api/vector-search"
    
    def __init__(self, base_url=None):
        """Initialize the API client with an optional base URL override"""
        self.base_url = base_url or self.BASE_URL
        
    def search_similar_tenders(self, query: str, limit: int = 10, today_only: bool = False) -> Dict[str, Any]:
        """
        Search for tenders similar to the query text
        
        Args:
            query (str): Text to search for
            limit (int, optional): Maximum number of results. Defaults to 10.
            today_only (bool, optional): If True, only search in tenders from the last 24 hours. Defaults to False.
            
        Returns:
            Dict: API response with query, results, count, and today_only fields
        """
        try:
            url = f"{self.base_url}{self.VECTOR_SEARCH_ENDPOINT}"
            params = {
                "query": query,
                "limit": limit,
                "today_only": str(today_only).lower()
            }
            
            logger.info(f"Sending vector search request to {url} with params: {params}")
            response = requests.get(url, params=params, timeout=30)
            
            if response.status_code != 200:
                logger.error(f"Error from vector search API: {response.status_code}, {response.text}")
                return {"error": f"API returned status code {response.status_code}", "results": [], "count": 0}
            
            data = response.json()
            logger.info(f"Received {data.get('count', 0)} results from vector search API")
            return data
            
        except requests.RequestException as e:
            logger.error(f"Request error when calling vector search API: {str(e)}")
            return {"error": str(e), "results": [], "count": 0}
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error from vector search API response: {str(e)}")
            return {"error": "Invalid JSON response from API", "results": [], "count": 0}
        except Exception as e:
            logger.error(f"Unexpected error when calling vector search API: {str(e)}")
            return {"error": str(e), "results": [], "count": 0}

    def get_initial_tenders(self, query: str, limit: int = 300) -> List[Dict[str, Any]]:
        """
        Get initial batch of tenders for a new user
        
        Args:
            query (str): Text to search for
            limit (int, optional): Maximum number of results. Defaults to 300.
            
        Returns:
            List[Dict]: List of tender objects
        """
        response = self.search_similar_tenders(query, limit=limit, today_only=False)
        if "error" in response:
            logger.error(f"Error fetching initial tenders: {response['error']}")
            return []
        
        # Extract just the tender objects from the results
        return [item["tender"] for item in response.get("results", [])]
    
    def get_latest_tenders(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get the latest tenders from the past 24 hours
        
        Args:
            query (str): Text to search for
            limit (int, optional): Maximum number of results. Defaults to 10.
            
        Returns:
            List[Dict]: List of tender objects
        """
        response = self.search_similar_tenders(query, limit=limit, today_only=True)
        if "error" in response:
            logger.error(f"Error fetching latest tenders: {response['error']}")
            return []
        
        # Extract just the tender objects from the results
        return [item["tender"] for item in response.get("results", [])]