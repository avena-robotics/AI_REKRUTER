-- Add new algorithm type
ALTER TYPE algorithm_type ADD VALUE IF NOT EXISTS 'EVALUATION_BY_AI'; 

-- Remove score_ai column from answers table
ALTER TABLE candidate_answers DROP COLUMN IF EXISTS score_ai;

-- Add ai_explanation column to candidate_answers table
ALTER TABLE candidate_answers ADD COLUMN IF NOT EXISTS ai_explanation text;