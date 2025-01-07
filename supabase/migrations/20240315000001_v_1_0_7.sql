ALTER TABLE candidate_answers
ADD CONSTRAINT unique_candidate_question_stage 
UNIQUE (candidate_id, question_id, stage);

-- Add user_id column to candidate_notes
ALTER TABLE candidate_notes
    ADD COLUMN user_id bigint REFERENCES users(id),
    ADD COLUMN user_email text;
