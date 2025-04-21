"""
Migration script to change vector size from 3072 to 1536 dimensions
"""
import logging
from app import app, db
from pgvector.sqlalchemy import Vector

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_vector_size():
    """Migrate the vector size in the tender_embeddings table"""
    try:
        logger.info("Starting vector size migration...")
        
        with app.app_context():
            # Step 1: Clear all existing embeddings, they will be regenerated
            logger.info("Deleting all existing embeddings...")
            from sqlalchemy import text
            db.session.execute(text("DELETE FROM tender_embeddings"))
            db.session.commit()
            logger.info("Deleted all existing embeddings")
            
            # Step 2: Update the vector dimension in the table
            logger.info("Updating vector dimension in tender_embeddings table...")
            db.session.execute(text("ALTER TABLE tender_embeddings DROP COLUMN embedding"))
            db.session.commit()
            
            # Step 3: Add the column back with the new dimension
            db.session.execute(text("ALTER TABLE tender_embeddings ADD COLUMN embedding vector(1536)"))
            db.session.commit()
            logger.info("Vector dimension updated to 1536")
            
            logger.info("Vector size migration completed successfully")
            return True
            
    except Exception as e:
        logger.error(f"Error migrating vector size: {str(e)}")
        return False

if __name__ == "__main__":
    migrate_vector_size()