"""
Migration script to add pgvector extension and set up the vector embeddings table.
"""

import logging
from app import db, app
from models import TenderEmbedding
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_pgvector():
    """Set up the pgvector extension and create the vector embeddings table"""
    try:
        with db.engine.connect() as conn:
            # Enable pgvector extension if it's not already enabled
            conn.execute(sa.text("CREATE EXTENSION IF NOT EXISTS vector"))
            conn.commit()
            logger.info("Enabled pgvector extension")
        
        # Create the tender_embeddings table if it doesn't exist
        db.create_all()
        logger.info("Created tender_embeddings table")
        
        return True
    except Exception as e:
        logger.error(f"Error setting up pgvector: {str(e)}")
        return False

if __name__ == "__main__":
    with app.app_context():
        setup_pgvector()