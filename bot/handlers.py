import logging
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler
from bot.questions import (
    QUESTIONS,
    WELCOME_MESSAGE,
    THANK_YOU_MESSAGE,
    ASK_SCHOOL_MESSAGE,
    ASK_CLASS_MESSAGE,
    COMPUTER_USAGE_QUESTION,
)
from bot.database import Database
from bot.notifications import NotificationSender

logger = logging.getLogger(__name__)

# Conversation states
(
    FULL_NAME,
    SCHOOL_NAME,
    CLASS_NAME,
    COMPUTER_USAGE,
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
) = range(14)

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
    """Receive full name and ask for school name"""
    full_name = update.message.text.strip()

    if not full_name:
        await update.message.reply_text("សូមបញ្ចូលឈ្មោះពេញរបស់អ្នក：")
        return FULL_NAME

    # Save full name
    context.user_data["full_name"] = full_name

    # Ask for school name
    await update.message.reply_text(ASK_SCHOOL_MESSAGE)

    return SCHOOL_NAME


async def receive_school_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive school name and ask for class"""
    school_name = update.message.text.strip()

    if not school_name:
        await update.message.reply_text("សូមបញ្ចូលឈ្មោះសាលារបស់អ្នក：")
        return SCHOOL_NAME

    # Save school name
    context.user_data["school_name"] = school_name

    # Ask for class
    await update.message.reply_text(ASK_CLASS_MESSAGE)

    return CLASS_NAME


# async def receive_class_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     """Receive class name and show Question 1"""
#     class_name = update.message.text.strip()

#     if not class_name:
#         await update.message.reply_text("សូមបញ្ចូលថ្នាក់ដែលអ្នកកំពុងបង្រៀន：")
#         return CLASS_NAME

#     # Save class name
#     context.user_data["class_name"] = class_name

#     # Show Question 1 with buttons
#     keyboard = [[choice] for choice in QUESTIONS[1]["choices"]]
#     reply_markup = ReplyKeyboardMarkup(
#         keyboard, one_time_keyboard=True, resize_keyboard=True
#     )

#     await update.message.reply_text(QUESTIONS[1]["text"], reply_markup=reply_markup)

#     return QUESTION_1


async def receive_class_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive class name and show Computer Usage question"""
    class_name = update.message.text.strip()

    if not class_name:
        await update.message.reply_text("សូមបញ្ចូលថ្នាក់ដែលអ្នកបង្រៀន៖")
        return CLASS_NAME

    # Save class name
    context.user_data["class_name"] = class_name

    # Show Computer Usage question with buttons
    keyboard = [[choice] for choice in COMPUTER_USAGE_QUESTION["choices"]]
    reply_markup = ReplyKeyboardMarkup(
        keyboard, one_time_keyboard=True, resize_keyboard=True
    )

    await update.message.reply_text(
        COMPUTER_USAGE_QUESTION["text"], reply_markup=reply_markup
    )

    return COMPUTER_USAGE


async def receive_computer_usage(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive computer usage answer - end survey if 'No', continue if 'Yes'"""
    answer = update.message.text
    context.user_data["computer_usage"] = answer

    # Check if user selected "ខ. មិនធ្លាប់" (No/Never used)
    if answer == "ខ. មិនធ្លាប់":
        # End survey early - save data without questions 1-10
        # Set questions 1-10 as "N/A" since they didn't answer
        for i in range(1, 11):
            context.user_data[f"question_{i}"] = "N/A"

        # Save to database
        success = db.save_survey_response(context.user_data)

        if success:
            # Send notification to channel
            await notifier.send_survey_notification(context.user_data)
            logger.info(
                f"Survey completed early (no computer) by: {context.user_data['full_name']}"
            )
        else:
            logger.error(f"Failed to save survey for: {context.user_data['full_name']}")

        # Send thank you message
        await update.message.reply_text(
            THANK_YOU_MESSAGE, reply_markup=ReplyKeyboardRemove()
        )

        # Clear user data
        context.user_data.clear()

        return ConversationHandler.END

    # User selected "ក. ធ្លាប់" (Yes/Used before) - continue to Question 1
    else:
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
    """Receive answer 5 and show Question 6"""
    answer = update.message.text
    context.user_data["question_5"] = answer

    # Show Question 6
    keyboard = [[choice] for choice in QUESTIONS[6]["choices"]]
    reply_markup = ReplyKeyboardMarkup(
        keyboard, one_time_keyboard=True, resize_keyboard=True
    )

    await update.message.reply_text(QUESTIONS[6]["text"], reply_markup=reply_markup)

    return QUESTION_6


async def receive_answer_6(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive answer 6 and show Question 7"""
    answer = update.message.text
    context.user_data["question_6"] = answer

    keyboard = [[choice] for choice in QUESTIONS[7]["choices"]]
    reply_markup = ReplyKeyboardMarkup(
        keyboard, one_time_keyboard=True, resize_keyboard=True
    )

    await update.message.reply_text(QUESTIONS[7]["text"], reply_markup=reply_markup)

    return QUESTION_7


async def receive_answer_7(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive answer 7 and show Question 8"""
    answer = update.message.text
    context.user_data["question_7"] = answer

    keyboard = [[choice] for choice in QUESTIONS[8]["choices"]]
    reply_markup = ReplyKeyboardMarkup(
        keyboard, one_time_keyboard=True, resize_keyboard=True
    )

    await update.message.reply_text(QUESTIONS[8]["text"], reply_markup=reply_markup)

    return QUESTION_8


async def receive_answer_8(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive answer 8 and show Question 9"""
    answer = update.message.text
    context.user_data["question_8"] = answer

    keyboard = [[choice] for choice in QUESTIONS[9]["choices"]]
    reply_markup = ReplyKeyboardMarkup(
        keyboard, one_time_keyboard=True, resize_keyboard=True
    )

    await update.message.reply_text(QUESTIONS[9]["text"], reply_markup=reply_markup)

    return QUESTION_9


async def receive_answer_9(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive answer 9 and show Question 10 (text input)"""
    answer = update.message.text
    context.user_data["question_9"] = answer

    # Question 10 is text input - no buttons
    await update.message.reply_text(
        QUESTIONS[10]["text"], reply_markup=ReplyKeyboardRemove()
    )

    return QUESTION_10


async def receive_answer_10(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive answer 10 (text), save to database, send notification, and end survey"""
    answer = update.message.text
    context.user_data["question_10"] = answer

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
        "ការស្ទង់មតិត្រូវបានបោះបង់។ វាយពាក្យ /start ដើម្បីចាប់ផ្តើមឡើងវិញ។",
        reply_markup=ReplyKeyboardRemove(),
    )
    context.user_data.clear()
    return ConversationHandler.END


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Log errors caused by updates"""
    logger.error(f"Update {update} caused error {context.error}")

    # Notify user
    if update and update.effective_message:
        await update.effective_message.reply_text(
            "សូមអភ័យទោស មានបញ្ហាបច្ចេកទេស! សូមព្យាយាមម្តងទៀត ឬទាក់ទងអ្នកគ្រប់គ្រង។"
        )
