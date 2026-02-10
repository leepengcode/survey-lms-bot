import mysql.connector
from mysql.connector import pooling
from bot.config import Config
import logging

logger = logging.getLogger(__name__)


class Database:
    def __init__(self):
        """Initialize database connection pool"""
        try:
            self.pool = pooling.MySQLConnectionPool(
                pool_name="survey_pool",
                pool_size=5,
                host=Config.MYSQL_HOST,
                port=Config.MYSQL_PORT,
                database=Config.MYSQL_DATABASE,
                user=Config.MYSQL_USER,
                password=Config.MYSQL_PASSWORD,
                charset="utf8mb4",
                collation="utf8mb4_unicode_ci",
            )
            logger.info("Database connection pool created successfully")
        except mysql.connector.Error as err:
            logger.error(f"Error creating connection pool: {err}")
            raise

    def get_connection(self):
        """Get a connection from the pool"""
        return self.pool.get_connection()

    def save_survey_response(self, user_data):
        """
        Save completed survey response to database

        Args:
            user_data (dict): Dictionary containing:
                - full_name
                - telegram_username
                - phone_number
                - telegram_user_id
                - question_1 to question_5

        Returns:
            bool: True if successful, False otherwise
        """
        connection = None
        cursor = None

        try:
            connection = self.get_connection()
            cursor = connection.cursor()

            query = """
                INSERT INTO survey_responses 
                (full_name, telegram_username, telegram_user_id,
                question_1, question_2, question_3, question_4, question_5)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """

            values = (
                user_data["full_name"],
                user_data.get("telegram_username", "N/A"),
                user_data["telegram_user_id"],
                user_data["question_1"],
                user_data["question_2"],
                user_data["question_3"],
                user_data["question_4"],
                user_data["question_5"],
            )

            cursor.execute(query, values)
            connection.commit()

            logger.info(f"Survey response saved for user: {user_data['full_name']}")
            return True

        except mysql.connector.Error as err:
            logger.error(f"Database error: {err}")
            if connection:
                connection.rollback()
            return False

        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

    def test_connection(self):
        """Test database connection"""
        try:
            connection = self.get_connection()
            cursor = connection.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            cursor.close()
            connection.close()
            return result is not None
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return False
