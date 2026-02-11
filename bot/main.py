import logging
from telegram import Update
from bot.handlers import initialize_services
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ConversationHandler,
)
from bot.config import Config
from bot.database import Database
from bot.handlers import (
    start,
    receive_full_name,
    receive_school_name,
    receive_class_name,
    receive_answer_1,
    receive_answer_2,
    receive_answer_3,
    receive_answer_4,
    receive_answer_5,
    receive_answer_6,
    receive_answer_7,
    receive_answer_8,
    receive_answer_9,
    receive_answer_10,
    cancel,
    FULL_NAME,
    SCHOOL_NAME,
    CLASS_NAME,
    QUESTION_1,
    QUESTION_2,
    QUESTION_3,
    QUESTION_4,
    QUESTION_5,
    QUESTION_6,
    QUESTION_7,
    QUESTION_8,
    QUESTION_9,
    QUESTION_10,
)

# Setup logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


def main():
    """Start the bot"""
    try:
        # Validate configuration
        Config.validate()
        logger.info("Configuration validated successfully")

        # Initialize services
        initialize_services()
        logger.info("Services initialized")

        # Test database connection
        db = Database()
        if db.test_connection():
            logger.info("Database connection successful")
        else:
            logger.error("Database connection failed")
            return

        # Create application
        application = Application.builder().token(Config.API_TOKEN).build()

        # Define conversation handler
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler("start", start)],
            states={
                FULL_NAME: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, receive_full_name)
                ],
                SCHOOL_NAME: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, receive_school_name)
                ],
                CLASS_NAME: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, receive_class_name)
                ],
                QUESTION_1: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, receive_answer_1)
                ],
                QUESTION_2: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, receive_answer_2)
                ],
                QUESTION_3: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, receive_answer_3)
                ],
                QUESTION_4: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, receive_answer_4)
                ],
                QUESTION_5: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, receive_answer_5)
                ],
                QUESTION_6: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, receive_answer_6)
                ],
                QUESTION_7: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, receive_answer_7)
                ],
                QUESTION_8: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, receive_answer_8)
                ],
                QUESTION_9: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, receive_answer_9)
                ],
                QUESTION_10: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, receive_answer_10)
                ],
            },
            fallbacks=[CommandHandler("cancel", cancel)],
        )

        # Add handlers
        application.add_handler(conv_handler)

        # Start bot
        logger.info("Bot started successfully!")
        logger.info("Press Ctrl+C to stop")
        application.run_polling(allowed_updates=Update.ALL_TYPES)

    except Exception as e:
        logger.error(f"Error starting bot: {e}")
        raise


if __name__ == "__main__":
    main()
