"""
Script to regenerate all embeddings with the new text structure
This will delete all existing embeddings and regenerate them with 
the updated get_text_for_embedding function that includes main activities
"""
import logging
from app import app, db
from models import TenderEmbedding
import generate_embeddings_incremental

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def delete_all_embeddings():
    """Delete all existing embeddings to force regeneration"""
    with app.app_context():
        try:
            # Count embeddings before deletion
            count = db.session.query(TenderEmbedding).count()
            logger.info(f"Deleting {count} existing embeddings")
            
            # Delete all embeddings
            db.session.query(TenderEmbedding).delete()
            db.session.commit()
            
            logger.info(f"Successfully deleted {count} embeddings")
            return count
        except Exception as e:
            logger.error(f"Error deleting embeddings: {str(e)}")
            db.session.rollback()
            return 0

def regenerate_all_embeddings():
    """Regenerate all embeddings with updated text structure"""
    # First delete all existing embeddings
    deleted = delete_all_embeddings()
    logger.info(f"Deleted {deleted} existing embeddings")
    
    # Now regenerate embeddings for all tenders
    with app.app_context():
        # Use incremental generator without any limits to process all tenders
        # Use small batch size and delay to avoid API rate limits
        total_processed = generate_embeddings_incremental.generate_embeddings_incrementally(
            batch_size=50,
            delay=5,
            max_batches=None  # Process all tenders
        )
        
        logger.info(f"Regenerated embeddings for {total_processed} tenders with new text structure")
        return total_processed

if __name__ == "__main__":
    regenerate_all_embeddings()