import asyncio
from telegram import Bot
from dotenv import load_dotenv
import os

load_dotenv()


async def test_send():
    bot = Bot(token=os.getenv("API_TOKEN"))
    channel_id = os.getenv("CHANNEL_ID")

    print(f"Testing send to channel: {channel_id}")

    try:
        message = await bot.send_message(
            chat_id=channel_id, text="🧪 Test message from bot"
        )
        print(f"✅ SUCCESS! Message sent: {message.message_id}")
    except Exception as e:
        print(f"❌ ERROR: {e}")


asyncio.run(test_send())
