import logging
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler
from bot.questions import QUESTIONS, WELCOME_MESSAGE, THANK_YOU_MESSAGE
from bot.database import Database
from bot.notifications import NotificationSender

logger = logging.getLogger(__name__)

# Conversation states
FULL_NAME, QUESTION_1, QUESTION_2, QUESTION_3, QUESTION_4, QUESTION_5 = range(6)

# These will be initialized later
db = None
notifier = None


def initialize_services():
    """Initialize database and notifier after config is loaded"""
    global db, notifier
    if db is None:
        db = Database()
    if notifier is None:
        notifier = NotificationSender()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    user = update.effective_user

    # Initialize user data storage
    context.user_data.clear()
    context.user_data["telegram_user_id"] = user.id
    context.user_data["telegram_username"] = user.username if user.username else "N/A"

    # Send welcome message
    await update.message.reply_text(WELCOME_MESSAGE, reply_markup=ReplyKeyboardRemove())

    return FULL_NAME


async def receive_full_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive full name and show Question 1"""
    full_name = update.message.text.strip()

    if not full_name:
        await update.message.reply_text("Please enter your full name:")
        return FULL_NAME

    # Save full name
    context.user_data["full_name"] = full_name

    # Show Question 1 with buttons
    keyboard = [[choice] for choice in QUESTIONS[1]["choices"]]
    reply_markup = ReplyKeyboardMarkup(
        keyboard, one_time_keyboard=True, resize_keyboard=True
    )

    await update.message.reply_text(QUESTIONS[1]["text"], reply_markup=reply_markup)

    return QUESTION_1


async def receive_answer_1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive answer 1 and show Question 2"""
    answer = update.message.text
    context.user_data["question_1"] = answer

    # Show Question 2
    keyboard = [[choice] for choice in QUESTIONS[2]["choices"]]
    reply_markup = ReplyKeyboardMarkup(
        keyboard, one_time_keyboard=True, resize_keyboard=True
    )

    await update.message.reply_text(QUESTIONS[2]["text"], reply_markup=reply_markup)

    return QUESTION_2


async def receive_answer_2(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive answer 2 and show Question 3"""
    answer = update.message.text
    context.user_data["question_2"] = answer

    # Show Question 3
    keyboard = [[choice] for choice in QUESTIONS[3]["choices"]]
    reply_markup = ReplyKeyboardMarkup(
        keyboard, one_time_keyboard=True, resize_keyboard=True
    )

    await update.message.reply_text(QUESTIONS[3]["text"], reply_markup=reply_markup)

    return QUESTION_3


async def receive_answer_3(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive answer 3 and show Question 4"""
    answer = update.message.text
    context.user_data["question_3"] = answer

    # Show Question 4
    keyboard = [[choice] for choice in QUESTIONS[4]["choices"]]
    reply_markup = ReplyKeyboardMarkup(
        keyboard, one_time_keyboard=True, resize_keyboard=True
    )

    await update.message.reply_text(QUESTIONS[4]["text"], reply_markup=reply_markup)

    return QUESTION_4


async def receive_answer_4(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive answer 4 and show Question 5"""
    answer = update.message.text
    context.user_data["question_4"] = answer

    # Show Question 5
    keyboard = [[choice] for choice in QUESTIONS[5]["choices"]]
    reply_markup = ReplyKeyboardMarkup(
        keyboard, one_time_keyboard=True, resize_keyboard=True
    )

    await update.message.reply_text(QUESTIONS[5]["text"], reply_markup=reply_markup)

    return QUESTION_5


async def receive_answer_5(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive answer 5, save to database, send notification, and end survey"""
    answer = update.message.text
    context.user_data["question_5"] = answer

    # Save to database
    success = db.save_survey_response(context.user_data)

    if success:
        # Send notification to channel
        await notifier.send_survey_notification(context.user_data)
        logger.info(f"Survey completed by: {context.user_data['full_name']}")
    else:
        logger.error(f"Failed to save survey for: {context.user_data['full_name']}")

    # Send thank you message
    await update.message.reply_text(
        THANK_YOU_MESSAGE, reply_markup=ReplyKeyboardRemove()
    )

    # Clear user data
    context.user_data.clear()

    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel the survey"""
    await update.message.reply_text(
        "Survey cancelled. Type /start to begin again.",
        reply_markup=ReplyKeyboardRemove(),
    )
    context.user_data.clear()
    return ConversationHandler.END
