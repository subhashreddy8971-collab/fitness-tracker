import logging
import os
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from config import TELEGRAM_BOT_TOKEN
from database.db import init_db
from bot.handlers import handle_message

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

def main():
    """Start the bot."""
    # Initialize Database
    init_db()
    logger.info("Database initialized.")

    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN not found in environment variables.")
        return

    # Create the Application
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Unified message handler for Photos and Text (Conversational)
    # Note: We can keep a basic /start for new users, but handled conversationally
    application.add_handler(CommandHandler("start", handle_message)) 
    
    # Catch all text and photos
    application.add_handler(MessageHandler(filters.PHOTO | filters.TEXT, handle_message))

    # Run the bot
    logger.info("Bot is polling...")
    application.run_polling()

if __name__ == "__main__":
    main()
