from app import app
from routes import register_routes
from scheduler import init_scheduler
import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Register the routes
register_routes(app)

# Initialize the scheduler
init_scheduler(app)

if __name__ == "__main__":
    logger.info("Starting Etimad Tender Scraper service")
    app.run(host="0.0.0.0", port=5000, debug=True)
