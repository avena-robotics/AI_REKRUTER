ALTER TABLE candidate_answers
ADD CONSTRAINT unique_candidate_question_stage 
UNIQUE (candidate_id, question_id, stage);

-- Add user_id column to candidate_notes
ALTER TABLE candidate_notes
    ADD COLUMN user_id bigint REFERENCES users(id),
    ADD COLUMN user_email text;

-- Update existing notes with a default value if needed
-- UPDATE candidate_notes SET user_email = 'system@example.com' WHERE user_email IS NULL;

-- Make user_id required for new notes
ALTER TABLE candidate_notes
    ALTER COLUMN user_id SET NOT NULL;