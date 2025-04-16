"""
Script to generate initial embeddings for existing tenders
"""
import logging
from app import app, db
import embeddings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generate_initial_embeddings():
    """Generate embeddings for all tenders without them"""
    with app.app_context():
        # First check if we need to clean up expired embeddings
        removed = embeddings.cleanup_expired_embeddings()
        logger.info(f"Removed {removed} expired embeddings")
        
        # Then generate new embeddings
        count = embeddings.batch_embed_tenders()
        logger.info(f"Generated {count} new embeddings")

if __name__ == "__main__":
    generate_initial_embeddings()