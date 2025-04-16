"""
Script to generate embeddings incrementally for existing tenders
Handles large numbers of tenders with checkpointing and rate limiting
"""
import logging
import time
import argparse
from app import app, db
import embeddings
from models import Tender, TenderEmbedding

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Default batch size
DEFAULT_BATCH_SIZE = 50
# Default delay between batches in seconds to avoid rate limits
DEFAULT_DELAY = 2

def generate_embeddings_incrementally(batch_size=DEFAULT_BATCH_SIZE, delay=DEFAULT_DELAY, max_batches=None):
    """
    Generate embeddings incrementally with checkpointing
    
    Args:
        batch_size (int): Number of tenders to process in each batch
        delay (int): Seconds to wait between batches
        max_batches (int, optional): Maximum number of batches to process. Default is None (process all).
    """
    with app.app_context():
        # First check if we need to clean up expired embeddings
        removed = embeddings.cleanup_expired_embeddings()
        logger.info(f"Removed {removed} expired embeddings")
        
        # Get count of tenders needing embeddings
        unprocessed_count = get_unprocessed_count()
        logger.info(f"Total tenders needing embeddings: {unprocessed_count}")
        
        processed_batches = 0
        total_processed = 0
        
        # Continue processing until all are done or max_batches is reached
        while unprocessed_count > 0 and (max_batches is None or processed_batches < max_batches):
            # Process one batch
            processed = process_single_batch(batch_size)
            total_processed += processed
            processed_batches += 1
            
            logger.info(f"Batch {processed_batches} complete. Processed {processed} tenders. Total so far: {total_processed}")
            
            # Exit if no more to process
            if processed == 0:
                break
                
            # Get updated count for next iteration
            unprocessed_count = get_unprocessed_count()
            
            # Add delay between batches to avoid rate limits
            if unprocessed_count > 0 and (max_batches is None or processed_batches < max_batches):
                logger.info(f"Waiting {delay} seconds before next batch...")
                time.sleep(delay)
        
        logger.info(f"Embedding generation complete. Total tenders processed: {total_processed}")
        return total_processed

def get_unprocessed_count():
    """Get count of tenders that need embeddings"""
    from utils import get_saudi_now
    now = get_saudi_now()
    
    # Count tenders that:
    # 1. Don't have an embedding yet
    # 2. Have a submission deadline in the future or null
    count = db.session.query(Tender).outerjoin(
        TenderEmbedding, 
        Tender.tender_id == TenderEmbedding.tender_id
    ).filter(
        TenderEmbedding.id.is_(None)
    ).filter(
        (Tender.submission_deadline.is_(None)) | (Tender.submission_deadline > now)
    ).count()
    
    return count

def process_single_batch(batch_size):
    """Process a single batch of tenders and return the number processed"""
    processed = embeddings.batch_embed_tenders(limit=batch_size)
    return processed

if __name__ == "__main__":
    # Set up command line arguments
    parser = argparse.ArgumentParser(description='Generate embeddings incrementally for tenders')
    parser.add_argument('--batch-size', type=int, default=DEFAULT_BATCH_SIZE,
                        help=f'Number of tenders to process in each batch (default: {DEFAULT_BATCH_SIZE})')
    parser.add_argument('--delay', type=int, default=DEFAULT_DELAY,
                        help=f'Seconds to wait between batches (default: {DEFAULT_DELAY})')
    parser.add_argument('--max-batches', type=int, default=None,
                        help='Maximum number of batches to process (default: process all)')
    
    args = parser.parse_args()
    
    # Run the incremental embedding generation
    generate_embeddings_incrementally(
        batch_size=args.batch_size,
        delay=args.delay,
        max_batches=args.max_batches
    )