import mysql.connector
from dotenv import load_dotenv
import os

load_dotenv()

print(f"Testing with: {os.getenv('MYSQL_USER')}@{os.getenv('MYSQL_HOST')}")

try:
    connection = mysql.connector.connect(
        host=os.getenv("MYSQL_HOST"),
        port=int(os.getenv("MYSQL_PORT")),
        database=os.getenv("MYSQL_DATABASE"),
        user=os.getenv("MYSQL_USER"),
        password=os.getenv("MYSQL_PASSWORD"),
    )
    print("✅ SUCCESS!")
    connection.close()
except mysql.connector.Error as err:
    print(f"❌ ERROR: {err}")
