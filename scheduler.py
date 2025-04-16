import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from flask import Flask
from scraper import run_scraper

logger = logging.getLogger(__name__)

def init_scheduler(app: Flask):
    """Initialize the scheduler to run the scraper 3 times a day"""
    scheduler = BackgroundScheduler()
    
    # Schedule the scraper to run at 6 AM, 2 PM, and 10 PM (UTC)
    scheduler.add_job(
        func=run_scraper_with_app_context(app),
        trigger=CronTrigger(hour='6,14,22', minute='0'),
        id='scraper_job',
        name='Scrape Etimad Tenders',
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
    
    # Start the scheduler
    scheduler.start()
    logger.info("Scheduler started, scraper will run at 6 AM, 2 PM, and 10 PM UTC")
    logger.info("Initial scrape will run in the background after startup")

def run_scraper_with_app_context(app: Flask):
    """Return a function that runs the scraper within the app context"""
    def wrapper():
        with app.app_context():
            run_scraper()
    return wrapper
