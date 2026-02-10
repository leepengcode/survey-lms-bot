import asyncio
from telegram import Bot
from dotenv import load_dotenv
import os

load_dotenv()


async def get_updates():
    bot = Bot(token=os.getenv("API_TOKEN"))
    updates = await bot.get_updates()

    print("Recent updates:")
    for update in updates[-5:]:  # Last 5 updates
        if update.channel_post:
            print(f"Channel ID: {update.channel_post.chat.id}")
            print(f"Channel Title: {update.channel_post.chat.title}")
            print("-" * 50)


asyncio.run(get_updates())
