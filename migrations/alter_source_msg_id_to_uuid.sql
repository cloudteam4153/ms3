-- Migration: Alter source_msg_id columns to support UUIDs (VARCHAR)
-- The integrations service uses UUIDs for message IDs, not integers

-- Alter tasks table (if it exists and has INT column)
ALTER TABLE tasks MODIFY COLUMN source_msg_id VARCHAR(36) NOT NULL COMMENT 'Associates task with specific message (UUID)';

-- Alter todos table (if it exists and has INT column)
ALTER TABLE todos MODIFY COLUMN source_msg_id VARCHAR(36) NOT NULL COMMENT 'Associates todo with specific message (UUID)';

-- Alter followups table (if it exists and has INT column)
ALTER TABLE followups MODIFY COLUMN source_msg_id VARCHAR(36) NOT NULL COMMENT 'Associates followup with specific message (UUID)';
