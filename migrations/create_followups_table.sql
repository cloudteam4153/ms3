-- Migration: Create followups table
-- This table stores follow-up items associated with messages from email/slack

CREATE TABLE IF NOT EXISTS followups (
    followup_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    source_msg_id INT NOT NULL COMMENT 'Associates followup with specific message',
    title VARCHAR(255) NOT NULL,
    status ENUM('open', 'done') DEFAULT 'open',
    due_at DATETIME NULL,
    priority INT NOT NULL DEFAULT 1 CHECK (priority >= 1 AND priority <= 5),
    message_type ENUM('email', 'slack') NOT NULL,
    sender VARCHAR(255) NOT NULL,
    subject VARCHAR(255) NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_user_id (user_id),
    INDEX idx_source_msg_id (source_msg_id),
    INDEX idx_status (status),
    INDEX idx_priority (priority),
    INDEX idx_due_at (due_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
