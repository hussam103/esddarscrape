"""
Database migration script to add new columns to the tenders table
"""
import logging
import sqlite3
from app import app

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_database():
    """Add new columns to the tenders table"""
    logger.info("Starting database migration")
    
    # Get the database path from the app config
    db_path = app.config["SQLALCHEMY_DATABASE_URI"].replace("sqlite:///", "")
    logger.info(f"Database path: {db_path}")
    
    try:
        # Connect to the SQLite database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if city column exists
        cursor.execute("PRAGMA table_info(tenders)")
        columns = [col[1] for col in cursor.fetchall()]
        
        # Add city column if it doesn't exist
        if 'city' not in columns:
            logger.info("Adding city column to tenders table")
            cursor.execute("ALTER TABLE tenders ADD COLUMN city TEXT")
        else:
            logger.info("city column already exists")
        
        # Add price column if it doesn't exist
        if 'price' not in columns:
            logger.info("Adding price column to tenders table")
            cursor.execute("ALTER TABLE tenders ADD COLUMN price TEXT")
        else:
            logger.info("price column already exists")
        
        # Commit the changes and close the connection
        conn.commit()
        conn.close()
        
        logger.info("Database migration completed successfully")
        return True
    except Exception as e:
        logger.error(f"Error during database migration: {e}")
        return False

if __name__ == "__main__":
    with app.app_context():
        migrate_database()