import logging
from telegram import Bot
from telegram.error import TelegramError
from bot.config import Config
from bot.questions import QUESTIONS

logger = logging.getLogger(__name__)


class NotificationSender:
    def __init__(self):
        """Initialize notification sender with bot instance"""
        self.bot = Bot(token=Config.API_TOKEN)
        self.channel_id = Config.CHANNEL_ID

    async def send_survey_notification(self, user_data):
        """
        Send formatted survey response to Telegram channel

        Args:
            user_data (dict): Contains full_name, telegram_username, phone_number,
                             telegram_user_id, and question_1 to question_5

        Returns:
            bool: True if notification sent successfully, False otherwise
        """
        try:
            # Format the notification message
            message = self._format_notification(user_data)

            # Send to channel
            await self.bot.send_message(
                chat_id=self.channel_id, text=message, parse_mode="HTML"
            )

            logger.info(
                f"Notification sent to channel for user: {user_data['full_name']}"
            )
            return True

        except TelegramError as e:
            logger.error(f"Failed to send notification to channel: {e}")
            return False

    def _format_notification(self, user_data):
        """
        Format survey data into readable notification message

        Args:
            user_data (dict): User survey data

        Returns:
            str: Formatted message
        """
        # Header
        message = "<b>New Survey Response</b>\n"
        message += "━━━━━━━━━━━━━━━━━\n"
        # User information
        message += f"<b>Full Name:</b> {user_data['full_name']}\n"
        message += f"<b>School:</b> {user_data['school_name']}\n"
        message += f"<b>Class:</b> {user_data['class_name']}\n"
        message += f"<b>Username:</b> @{user_data.get('telegram_username', 'N/A')}\n\n"

        # Survey answers
        message += "━━━━━━━━━━━━━━━━━\n"

        for i in range(1, 11):
            question_text = QUESTIONS[i]["text"]
            answer = user_data[f"question_{i}"]
            message += f"{question_text}\n"
            message += f"<b>{answer}</b>\n"

        return message
