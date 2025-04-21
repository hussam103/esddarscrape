import datetime
from app import db
from pgvector.sqlalchemy import Vector
from utils import get_saudi_now

class Tender(db.Model):
    __tablename__ = 'tenders'
    
    id = db.Column(db.Integer, primary_key=True)
    tender_id = db.Column(db.String(255), unique=True, nullable=False, index=True)
    reference_number = db.Column(db.String(255), nullable=True)
    publication_date = db.Column(db.DateTime, nullable=True)
    tender_type = db.Column(db.String(255), nullable=True)
    tender_title = db.Column(db.String(500), nullable=True)
    organization = db.Column(db.String(255), nullable=True)
    tender_url = db.Column(db.String(500), nullable=True)
    main_activities = db.Column(db.Text, nullable=True)
    duration = db.Column(db.String(255), nullable=True)
    inquiry_deadline = db.Column(db.DateTime, nullable=True)
    submission_deadline = db.Column(db.DateTime, nullable=True)
    opening_date = db.Column(db.DateTime, nullable=True)
    # Additional fields for new data structure
    city = db.Column(db.String(255), nullable=True)
    price = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=get_saudi_now)
    updated_at = db.Column(db.DateTime, default=get_saudi_now, onupdate=get_saudi_now)
    
    def to_dict(self):
        # Check if tender_url is in search format, if not, use a fallback URL to search page
        url = self.tender_url
        if url and not "AllTendersForVisitor?MultipleSearch=" in url:
            # Create a fallback search URL based on the tender title
            search_term = self.tender_title[:100] if self.tender_title else "Unknown Tender"
            import urllib.parse
            encoded_search_term = urllib.parse.quote(search_term)
            url = f"https://tenders.etimad.sa/Tender/AllTendersForVisitor?MultipleSearch={encoded_search_term}&IsSearch=true&PageSize=6"
            
        return {
            'id': self.id,
            'tender_id': self.tender_id,
            'reference_number': self.reference_number,
            'publication_date': self.publication_date.isoformat() if self.publication_date else None,
            'tender_type': self.tender_type,
            'tender_title': self.tender_title,
            'organization': self.organization,
            'tender_url': url,  # Use the search format URL
            'main_activities': self.main_activities,
            'duration': self.duration,
            'inquiry_deadline': self.inquiry_deadline.isoformat() if self.inquiry_deadline else None,
            'submission_deadline': self.submission_deadline.isoformat() if self.submission_deadline else None,
            'opening_date': self.opening_date.isoformat() if self.opening_date else None,
            'city': self.city,
            'price': self.price,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
    def get_text_for_embedding(self):
        """Get the text that will be used for embedding"""
        title = self.tender_title or ""
        org = self.organization or ""
        activities = self.main_activities or ""
        # Combine title, organization, and main activities for better semantic search
        return f"{title} {org} {activities}"


class TenderEmbedding(db.Model):
    """Store vector embeddings for tenders"""
    __tablename__ = 'tender_embeddings'
    
    id = db.Column(db.Integer, primary_key=True)
    tender_id = db.Column(db.String(255), db.ForeignKey('tenders.tender_id', ondelete='CASCADE'), nullable=False, unique=True)
    embedding = db.Column(Vector(1536))  # 1536 dimensions for text-embedding-3-small
    created_at = db.Column(db.DateTime, default=get_saudi_now)
    
    # Relationship to the tender
    tender = db.relationship('Tender', foreign_keys=[tender_id], backref=db.backref('embedding_rel', uselist=False, cascade='all, delete-orphan'))
    
    def __repr__(self):
        return f"<TenderEmbedding {self.tender_id}>"

class ScrapingLog(db.Model):
    __tablename__ = 'scraping_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    start_time = db.Column(db.DateTime, default=get_saudi_now)
    end_time = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(50), nullable=False, default='RUNNING')  # RUNNING, SUCCESS, ERROR
    message = db.Column(db.Text, nullable=True)
    tenders_scraped = db.Column(db.Integer, default=0)
    new_tenders = db.Column(db.Integer, default=0)
    updated_tenders = db.Column(db.Integer, default=0)
    
    def to_dict(self):
        return {
            'id': self.id,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'status': self.status,
            'message': self.message,
            'tenders_scraped': self.tenders_scraped,
            'new_tenders': self.new_tenders,
            'updated_tenders': self.updated_tenders
        }
