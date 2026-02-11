import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    # Telegram Bot
    API_TOKEN = os.getenv("API_TOKEN")
    CHANNEL_ID = os.getenv("CHANNEL_ID")

    # MySQL Database
    MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
    MYSQL_PORT = int(os.getenv("MYSQL_PORT", 3306))
    MYSQL_DATABASE = os.getenv("MYSQL_DATABASE")
    MYSQL_USER = os.getenv("MYSQL_USER")
    MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")

    @classmethod
    def validate(cls):
        """Validate required configuration"""
        required = [
            "API_TOKEN",
            "CHANNEL_ID",
            "MYSQL_DATABASE",
            "MYSQL_USER",
            "MYSQL_PASSWORD",
        ]
        missing = [key for key in required if not getattr(cls, key)]

        if missing:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing)}"
            )

        return True
