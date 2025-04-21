"""
Script to run the vector size migration
"""
import logging
from migrate_vector_size import migrate_vector_size
from regenerate_all_embeddings import regenerate_all_embeddings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_migration():
    """Run the vector size migration process"""
    try:
        # Step 1: Migrate the vector size in the database
        logger.info("Starting vector size migration process...")
        
        success = migrate_vector_size()
        if not success:
            logger.error("Vector size migration failed")
            return False
            
        # Step 2: Regenerate all embeddings with the new model
        logger.info("Regenerating embeddings with the new model...")
        count = regenerate_all_embeddings()
        
        logger.info(f"Migration completed successfully. Regenerated {count} embeddings.")
        return True
        
    except Exception as e:
        logger.error(f"Error during migration process: {str(e)}")
        return False

if __name__ == "__main__":
    run_migration()