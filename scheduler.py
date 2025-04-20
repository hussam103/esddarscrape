import logging
import datetime
import pytz
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from flask import Flask
from scraper import run_scraper
import generate_embeddings_incremental
from embeddings import cleanup_expired_embeddings
from utils import get_saudi_now, SAUDI_TIMEZONE

logger = logging.getLogger(__name__)

def init_scheduler(app: Flask):
    """Initialize the scheduler to run the scraper and embedding jobs"""
    scheduler = BackgroundScheduler()
    
    # Schedule the scraper to run every hour to fetch both page 1 and page 2
    # Use minute=0 to run at the beginning of each hour
    scheduler.add_job(
        func=run_scraper_with_app_context(app),
        trigger=CronTrigger(minute='0', timezone=SAUDI_TIMEZONE),  # Run every hour
        id='scraper_job',
        name='Scrape Etimad Tenders (Hourly)',
        replace_existing=True
    )
    
    # Schedule embeddings generation to run at 10 AM, 6 PM, and 2 AM (Saudi Arabia time, GMT+3)
    # This is equivalent to 7 AM, 3 PM, and 11 PM UTC
    # Run after scraper to ensure new tenders are processed
    scheduler.add_job(
        func=run_embeddings_with_app_context(app),
        trigger=CronTrigger(hour='10,18,2', minute='0', timezone=SAUDI_TIMEZONE),
        id='embeddings_job',
        name='Generate Tender Embeddings',
        replace_existing=True
    )
    
    # Add initial scrape job to run immediately after startup without blocking
    scheduler.add_job(
        func=run_scraper_with_app_context(app),
        trigger='date',  # Run once immediately
        id='initial_scrape',
        name='Initial Etimad Tenders Scrape',
        replace_existing=True
    )
    
    # Add initial embeddings job to run 2 minutes after startup without blocking
    # This gives time for the initial scrape to complete first
    scheduler.add_job(
        func=run_embeddings_with_app_context(app),
        trigger='date',  # Run once after a delay
        run_date=get_saudi_now() + datetime.timedelta(minutes=2),
        id='initial_embeddings',
        name='Initial Tender Embeddings Generation',
        replace_existing=True
    )
    
    # Schedule cleanup of expired embeddings to run daily at 8 AM (Saudi Arabia time, GMT+3)
    # This is equivalent to 5 AM UTC
    scheduler.add_job(
        func=run_cleanup_with_app_context(app),
        trigger=CronTrigger(hour='8', minute='0', timezone=SAUDI_TIMEZONE),
        id='cleanup_job',
        name='Clean Up Expired Embeddings',
        replace_existing=True
    )
    
    # Add initial cleanup job to run 1 minute after startup
    scheduler.add_job(
        func=run_cleanup_with_app_context(app),
        trigger='date',  # Run once after a delay
        run_date=get_saudi_now() + datetime.timedelta(minutes=1),
        id='initial_cleanup',
        name='Initial Expired Embeddings Cleanup',
        replace_existing=True
    )
    
    # Start the scheduler
    scheduler.start()
    logger.info("Scheduler started, scraper will run every hour to fetch both page 1 and page 2")
    logger.info("Embeddings generator will run at 10 AM, 6 PM, and 2 AM (Saudi Arabia time, GMT+3)")
    logger.info("Expired embeddings cleanup will run daily at 8 AM (Saudi Arabia time, GMT+3)")
    logger.info("Initial scrape will run in the background after startup")

def run_scraper_with_app_context(app: Flask):
    """Return a function that runs the scraper within the app context"""
    def wrapper():
        with app.app_context():
            run_scraper()
    return wrapper


def run_embeddings_with_app_context(app: Flask):
    """Return a function that runs the embeddings generator within the app context"""
    def wrapper():
        with app.app_context():
            # Process 3 batches of 50 tenders each, with a 5-second delay between batches
            generate_embeddings_incremental.generate_embeddings_incrementally(
                batch_size=50,
                delay=5,
                max_batches=3
            )
    return wrapper


def run_cleanup_with_app_context(app: Flask):
    """Return a function that runs the expired embeddings cleanup within the app context"""
    def wrapper():
        with app.app_context():
            # Clean up expired embeddings
            removed = cleanup_expired_embeddings()
            logger.info(f"Cleaned up {removed} expired embeddings from vector database")
    return wrapper
