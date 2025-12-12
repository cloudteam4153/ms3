-- Migration: Alter user_id columns to support UUIDs (VARCHAR)
-- The service now uses UUID strings for user_id instead of integers

-- Alter tasks table
ALTER TABLE tasks MODIFY COLUMN user_id VARCHAR(36) NOT NULL COMMENT 'User ID (UUID)';

-- Alter todos table
ALTER TABLE todos MODIFY COLUMN user_id VARCHAR(36) NOT NULL COMMENT 'User ID (UUID)';

-- Alter followups table
ALTER TABLE followups MODIFY COLUMN user_id VARCHAR(36) NOT NULL COMMENT 'User ID (UUID)';

