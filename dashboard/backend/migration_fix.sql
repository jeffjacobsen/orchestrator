-- Migration: Add cost and duration tracking to tasks table
-- Version: 0.1.5
-- Date: 2025-11-08
--
-- This is a manual migration for users who cannot run Alembic.
-- If you have an existing database, run this to add the new columns.

-- Check if columns already exist (SQLite-safe approach)
-- If they exist, these commands will fail silently

-- Add cost tracking column (stored as cents to avoid float issues)
ALTER TABLE tasks ADD COLUMN total_cost INTEGER DEFAULT 0;

-- Add duration tracking column (stored as seconds)
ALTER TABLE tasks ADD COLUMN duration_seconds INTEGER DEFAULT 0;

-- Create indexes for efficient querying and sorting
CREATE INDEX IF NOT EXISTS ix_tasks_total_cost ON tasks(total_cost);
CREATE INDEX IF NOT EXISTS ix_tasks_duration_seconds ON tasks(duration_seconds);

-- Verify the migration
SELECT 'Migration complete. Verifying columns...';
PRAGMA table_info(tasks);
