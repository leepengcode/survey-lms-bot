-- Create database if not exists
CREATE DATABASE IF NOT EXISTS survey_testing CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE survey_testing;

CREATE TABLE IF NOT EXISTS survey_responses (
    id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(255) NOT NULL,
    school_name VARCHAR(255) NOT NULL,
    class_name VARCHAR(100) NOT NULL,
    computer_usage VARCHAR(50) NOT NULL,
    telegram_username VARCHAR(255),
    telegram_user_id BIGINT NOT NULL,
    question_1 VARCHAR(255) NOT NULL,
    question_2 VARCHAR(255) NOT NULL,
    question_3 VARCHAR(255) NOT NULL,
    question_4 VARCHAR(255) NOT NULL,
    question_5 VARCHAR(255) NOT NULL,
    question_6 VARCHAR(255) NOT NULL,
    question_7 VARCHAR(255) NOT NULL,
    question_8 VARCHAR(255) NOT NULL,
    question_9 VARCHAR(255) NOT NULL,
    question_10 TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_telegram_user_id (telegram_user_id),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;