# Telegram Survey LMS Bot

A Telegram bot for conducting surveys in Khmer language with MySQL database storage and Telegram channel notifications.

## Features

- Interactive survey flow with multiple-choice questions
- User data collection (Full Name, Username, Phone Number)
- MySQL database storage using Docker
- Real-time notifications to Telegram channel
- Survey data stored only after completion (not per question)
- Support for Khmer language questions

## Prerequisites

Before starting, you need:

1. **Telegram Bot Token**
   - Already have: `Survey LMS` bot
   - Token stored in `.env` file

2. **Telegram Channel**
   - Create a new Telegram channel for receiving survey notifications
   - Add your bot as an administrator to the channel
   - Get the Channel ID (we'll guide you on this)

3. **Software Requirements**
   - Python 3.9 or higher
   - Docker and Docker Compose
   - Git (optional)

## Technology Stack

- **Bot Framework**: python-telegram-bot (v20.x)
- **Database**: MySQL 8.0
- **Containerization**: Docker & Docker Compose
- **Python Libraries**: 
  - python-telegram-bot
  - mysql-connector-python
  - python-dotenv

## Environment Variables

Create a `.env` file in the project root with:

```env
# Telegram Bot Configuration
API_TOKEN=your_bot_token_here

# Telegram Channel for Notifications
CHANNEL_ID=@your_channel_username_or_chat_id

# MySQL Database Configuration
MYSQL_ROOT_PASSWORD=your_secure_root_password
MYSQL_DATABASE=survey_lms
MYSQL_USER=survey_user
MYSQL_PASSWORD=your_secure_password
MYSQL_HOST=mysql
MYSQL_PORT=3306
```

## Database Schema

The bot will create a table `survey_responses` with:

- `id` - Auto-increment primary key
- `full_name` - User's full name
- `telegram_username` - Telegram username
- `phone_number` - Phone number (optional)
- `telegram_user_id` - Telegram user ID
- `question_1` - Answer to question 1
- `question_2` - Answer to question 2
- `question_3` - Answer to question 3
- `question_4` - Answer to question 4
- `question_5` - Answer to question 5
- `created_at` - Timestamp of survey completion

## Survey Questions

1. **Question 1**: Study time per day at home
2. **Question 2**: Preferred learning method
3. **Question 3**: Biggest study obstacle
4. **Question 4**: Difficulty level of sciences
5. **Question 5**: Main study goal

## Installation & Setup

Detailed setup instructions will be provided step by step.

## Usage

1. User starts the bot with `/start`
2. User enters their full name
3. Bot presents 5 questions with multiple-choice answers
4. After completing all questions, data is saved to database
5. Notification is sent to Telegram channel
6. User receives thank you message

## Project Structure

See below for complete folder structure.

## License

MIT License

## Support

For issues or questions, contact the development team.


# Project Folder Structure

```
survey-lms-bot/
│
├── .env                          # Environment variables (NOT committed to git)
├── .gitignore                    # Git ignore file
├── README.md                     # Project documentation
├── requirements.txt              # Python dependencies
├── docker-compose.yml            # Docker services configuration
│
├── bot/                          # Main bot application
│   ├── __init__.py
│   ├── main.py                   # Bot entry point
│   ├── config.py                 # Configuration loader
│   ├── handlers.py               # Telegram handlers (start, messages, callbacks)
│   ├── database.py               # Database connection and operations
│   ├── questions.py              # Survey questions and choices data
│   └── notifications.py          # Telegram channel notification sender
│
├── sql/                          # SQL scripts
│   └── init.sql                  # Database initialization script
│
└── logs/                         # Log files (created automatically)
    └── .gitkeep
```

## File Descriptions

### Root Level Files

- **.env**: Contains sensitive configuration (API tokens, database credentials)
- **.gitignore**: Specifies files to exclude from version control
- **README.md**: Project documentation and setup guide
- **requirements.txt**: Python package dependencies
- **docker-compose.yml**: Defines MySQL container and network configuration

### bot/ Directory

- **__init__.py**: Makes bot directory a Python package
- **main.py**: Application entry point, starts the bot
- **config.py**: Loads environment variables and validates configuration
- **handlers.py**: Contains all Telegram bot handlers (commands, button clicks)
- **database.py**: Database connection pool, queries, and data operations
- **questions.py**: Survey questions and answer choices in Khmer
- **notifications.py**: Sends formatted notifications to Telegram channel

### sql/ Directory

- **init.sql**: Database schema creation script (runs on first MySQL startup)

### logs/ Directory

- Automatically created for storing application logs
- **.gitkeep**: Keeps empty directory in git

## Important Notes

1. **Never commit .env file** - Contains sensitive tokens and passwords
2. **Database data persists** - MySQL data stored in Docker volume
3. **User session data** - Stored in memory during survey (conversation handler)
4. **Khmer text encoding** - Uses UTF-8 throughout the application