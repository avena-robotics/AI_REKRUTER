-- Add new algorithm type
ALTER TYPE algorithm_type ADD VALUE IF NOT EXISTS 'EVALUATION_BY_AI'; 

-- Remove score_ai column from answers table
ALTER TABLE candidate_answers DROP COLUMN IF EXISTS score_ai;

-- Add ai_explanation column to candidate_answers table
ALTER TABLE candidate_answers ADD COLUMN IF NOT EXISTS ai_explanation text;

-- Modify score columns in candidates table to use FLOAT
ALTER TABLE candidates 
    ALTER COLUMN po1_score TYPE FLOAT USING (CAST(po1_score AS NUMERIC))::FLOAT,
    ALTER COLUMN po2_score TYPE FLOAT USING (CAST(po2_score AS NUMERIC))::FLOAT,
    ALTER COLUMN po2_5_score TYPE FLOAT USING (CAST(po2_5_score AS NUMERIC))::FLOAT,
    ALTER COLUMN po3_score TYPE FLOAT USING (CAST(po3_score AS NUMERIC))::FLOAT,
    ALTER COLUMN po4_score TYPE FLOAT USING (CAST(po4_score AS NUMERIC))::FLOAT,
    ALTER COLUMN total_score TYPE FLOAT USING (CAST(total_score AS NUMERIC))::FLOAT;

-- Modify score column in candidate_answers table to use FLOAT
ALTER TABLE candidate_answers 
    ALTER COLUMN score TYPE FLOAT USING (CAST(score AS NUMERIC))::FLOAT;

-- Add check constraints to ensure scores are not negative
ALTER TABLE candidates
    ADD CONSTRAINT check_po1_score CHECK (po1_score >= 0),
    ADD CONSTRAINT check_po2_score CHECK (po2_score >= 0),
    ADD CONSTRAINT check_po2_5_score CHECK (po2_5_score >= 0),
    ADD CONSTRAINT check_po3_score CHECK (po3_score >= 0),
    ADD CONSTRAINT check_po4_score CHECK (po4_score >= 0),
    ADD CONSTRAINT check_total_score CHECK (total_score >= 0);

-- Add token expiry days columns to campaigns table
ALTER TABLE campaigns
    ADD COLUMN IF NOT EXISTS po1_token_expiry_days INTEGER NOT NULL DEFAULT 7,
    ADD COLUMN IF NOT EXISTS po2_token_expiry_days INTEGER NOT NULL DEFAULT 7,
    ADD COLUMN IF NOT EXISTS po3_token_expiry_days INTEGER NOT NULL DEFAULT 7;

-- Add check constraints to ensure days are positive
ALTER TABLE campaigns
    ADD CONSTRAINT check_po1_token_expiry_days CHECK (po1_token_expiry_days > 0),
    ADD CONSTRAINT check_po2_token_expiry_days CHECK (po2_token_expiry_days > 0),
    ADD CONSTRAINT check_po3_token_expiry_days CHECK (po3_token_expiry_days > 0);
