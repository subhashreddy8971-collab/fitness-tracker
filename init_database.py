from database.db import init_db, engine
from database.models import User, Workout, Meal, BodyMetric, DailySummary
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logger.info("Initializing database...")
    try:
        init_db()
        logger.info("Database tables created successfully!")
        logger.info(f"Database URL: {engine.url}")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
