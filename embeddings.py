"""
Utility for creating and managing vector embeddings with OpenAI
"""

import os
import datetime
import logging
import numpy as np
from openai import OpenAI
from app import db
from models import Tender, TenderEmbedding

# The newest OpenAI model is "gpt-4o" which was released May 13, 2024.
# Do not change this unless explicitly requested by the user
EMBEDDING_MODEL = "text-embedding-3-large"  # 3072 dimensions
MAX_BATCH_SIZE = 50  # Process embeddings in batches

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize OpenAI client
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

def create_embedding(text):
    """Create an OpenAI embedding for the given text"""
    if not text or len(text.strip()) == 0:
        logger.warning(f"Empty text provided for embedding")
        # Return a zero vector if text is empty
        return np.zeros(3072).tolist()
    
    try:
        response = client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=text,
            dimensions=3072
        )
        return response.data[0].embedding
    except Exception as e:
        logger.error(f"Error creating embedding: {str(e)}")
        # Return a zero vector in case of error
        return np.zeros(3072).tolist()

def embed_tender(tender):
    """Create and store embedding for a single tender"""
    text = tender.get_text_for_embedding()
    
    try:
        # Check if embedding already exists
        existing_embedding = TenderEmbedding.query.filter_by(tender_id=tender.tender_id).first()
        
        if existing_embedding:
            logger.info(f"Embedding already exists for tender {tender.tender_id}")
            return False
        
        # Create embedding
        embedding_vector = create_embedding(text)
        
        # Store embedding
        new_embedding = TenderEmbedding(
            tender_id=tender.tender_id,
            embedding=embedding_vector
        )
        
        db.session.add(new_embedding)
        db.session.commit()
        
        logger.info(f"Created embedding for tender {tender.tender_id}")
        return True
    
    except Exception as e:
        logger.error(f"Error embedding tender {tender.tender_id}: {str(e)}")
        db.session.rollback()
        return False

def batch_embed_tenders(limit=None):
    """Create embeddings for all tenders that don't have them yet
    
    Args:
        limit (int, optional): Maximum number of tenders to process. Defaults to None (all).
    
    Returns:
        int: Number of tenders successfully embedded
    """
    now = datetime.datetime.utcnow()
    
    # Find all tenders that:
    # 1. Don't have an embedding yet
    # 2. Have a submission deadline in the future or null
    query = db.session.query(Tender).outerjoin(
        TenderEmbedding, 
        Tender.tender_id == TenderEmbedding.tender_id
    ).filter(
        TenderEmbedding.id.is_(None)
    ).filter(
        (Tender.submission_deadline.is_(None)) | (Tender.submission_deadline > now)
    )
    
    if limit:
        tenders = query.limit(limit).all()
    else:
        tenders = query.all()
    
    logger.info(f"Found {len(tenders)} tenders without embeddings")
    
    count = 0
    
    # Process tenders in batches
    for i in range(0, len(tenders), MAX_BATCH_SIZE):
        batch = tenders[i:i+MAX_BATCH_SIZE]
        batch_texts = [t.get_text_for_embedding() for t in batch]
        
        try:
            # Create embeddings for the batch
            response = client.embeddings.create(
                model=EMBEDDING_MODEL,
                input=batch_texts,
                dimensions=3072
            )
            
            # Store embeddings
            for j, tender in enumerate(batch):
                try:
                    embedding_vector = response.data[j].embedding
                    new_embedding = TenderEmbedding(
                        tender_id=tender.tender_id,
                        embedding=embedding_vector
                    )
                    
                    db.session.add(new_embedding)
                    count += 1
                except Exception as e:
                    logger.error(f"Error storing embedding for tender {tender.tender_id}: {str(e)}")
            
            # Commit the batch
            db.session.commit()
            logger.info(f"Processed batch of {len(batch)} tenders")
            
        except Exception as e:
            logger.error(f"Error creating batch embeddings: {str(e)}")
            db.session.rollback()
    
    logger.info(f"Created embeddings for {count} tenders")
    return count

def cleanup_expired_embeddings():
    """Remove embeddings for tenders with passed submission deadlines"""
    now = datetime.datetime.utcnow()
    
    # Find embeddings for tenders with passed deadlines
    expired_embeddings = db.session.query(TenderEmbedding).join(
        Tender, 
        TenderEmbedding.tender_id == Tender.tender_id
    ).filter(
        Tender.submission_deadline < now
    ).all()
    
    logger.info(f"Found {len(expired_embeddings)} expired embeddings to remove")
    
    count = 0
    for embedding in expired_embeddings:
        try:
            db.session.delete(embedding)
            count += 1
        except Exception as e:
            logger.error(f"Error removing embedding {embedding.id}: {str(e)}")
    
    db.session.commit()
    logger.info(f"Removed {count} expired embeddings")
    return count

def search_similar_tenders(query_text, limit=10, today_only=False):
    """Search for tenders similar to the query text
    
    Args:
        query_text (str): Text to search for
        limit (int, optional): Maximum number of results. Defaults to 10.
        today_only (bool, optional): If True, only search in tenders published today. Defaults to False.
    
    Returns:
        list: List of tenders sorted by similarity
    """
    # Create embedding for the query
    query_embedding = create_embedding(query_text)
    
    # Get current date for filtering
    now = datetime.datetime.utcnow()
    
    # Base query
    query = db.session.query(
        Tender, 
        TenderEmbedding.embedding.cosine_distance(query_embedding).label('distance')
    ).join(
        TenderEmbedding,
        Tender.tender_id == TenderEmbedding.tender_id
    )
    
    # Filter out tenders with passed submission dates
    query = query.filter(
        (Tender.submission_deadline.is_(None)) | (Tender.submission_deadline > now)
    )
    
    # If today_only is True, filter to only show tenders published today
    if today_only:
        # Get the start of today
        today_start = datetime.datetime.combine(now.date(), datetime.time.min)
        query = query.filter(Tender.publication_date >= today_start)
    
    # Order by similarity and limit results
    results = query.order_by('distance').limit(limit).all()
    
    # Extract tenders from results
    tenders = [{"tender": r[0].to_dict(), "similarity": 1 - r[1]} for r in results]
    
    return tenders