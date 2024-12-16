-- Update timestamps in tests table
ALTER TABLE tests
    ALTER COLUMN created_at TYPE TIMESTAMP WITH TIME ZONE,
    ALTER COLUMN updated_at TYPE TIMESTAMP WITH TIME ZONE;

-- Update timestamps in campaigns table
ALTER TABLE campaigns
    ALTER COLUMN created_at TYPE TIMESTAMP WITH TIME ZONE,
    ALTER COLUMN updated_at TYPE TIMESTAMP WITH TIME ZONE;

-- Update timestamps in candidates table
ALTER TABLE candidates
    ALTER COLUMN created_at TYPE TIMESTAMP WITH TIME ZONE,
    ALTER COLUMN updated_at TYPE TIMESTAMP WITH TIME ZONE,
    ALTER COLUMN po1_started_at TYPE TIMESTAMP WITH TIME ZONE,
    ALTER COLUMN po2_started_at TYPE TIMESTAMP WITH TIME ZONE,
    ALTER COLUMN po3_started_at TYPE TIMESTAMP WITH TIME ZONE,
    ALTER COLUMN po1_completed_at TYPE TIMESTAMP WITH TIME ZONE,
    ALTER COLUMN po2_completed_at TYPE TIMESTAMP WITH TIME ZONE,
    ALTER COLUMN po3_completed_at TYPE TIMESTAMP WITH TIME ZONE,
    ALTER COLUMN access_token_po2_expires_at TYPE TIMESTAMP WITH TIME ZONE,
    ALTER COLUMN access_token_po3_expires_at TYPE TIMESTAMP WITH TIME ZONE;

-- Update timestamps in candidate_answers table
ALTER TABLE candidate_answers
    ALTER COLUMN created_at TYPE TIMESTAMP WITH TIME ZONE;

-- Update timestamps in users table
ALTER TABLE users
    ALTER COLUMN created_at TYPE TIMESTAMP WITH TIME ZONE,
    ALTER COLUMN updated_at TYPE TIMESTAMP WITH TIME ZONE;

-- Update timestamps in groups table
ALTER TABLE groups
    ALTER COLUMN created_at TYPE TIMESTAMP WITH TIME ZONE,
    ALTER COLUMN updated_at TYPE TIMESTAMP WITH TIME ZONE;

-- Update timestamps in candidate_notes table
ALTER TABLE candidate_notes
    ALTER COLUMN created_at TYPE TIMESTAMP WITH TIME ZONE,
    ALTER COLUMN updated_at TYPE TIMESTAMP WITH TIME ZONE; 