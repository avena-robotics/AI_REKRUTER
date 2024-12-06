-- First drop existing constraints
ALTER TABLE candidates 
DROP CONSTRAINT IF EXISTS candidates_recruitment_status_check;

-- Drop and recreate the type
DROP TYPE IF EXISTS recruitment_status CASCADE;
CREATE TYPE recruitment_status AS ENUM (
    'PO1',
    'PO2',
    'PO2_5',
    'PO3',
    'PO4',
    'REJECTED',
    'ACCEPTED'
);

-- Add constraint back
ALTER TABLE candidates
ADD CONSTRAINT candidates_recruitment_status_check 
CHECK (recruitment_status::text = ANY (ARRAY[
    'PO1'::text,
    'PO2'::text,
    'PO2_5'::text,
    'PO3'::text,
    'PO4'::text,
    'REJECTED'::text,
    'ACCEPTED'::text
])); 