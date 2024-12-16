-- Add new answer type 'NUMERIC'
ALTER TYPE answer_type ADD VALUE IF NOT EXISTS 'NUMERIC';

-- Add new answer column
ALTER TABLE candidate_answers
    ADD COLUMN answer text;

-- Copy data from existing columns to the new answer column
UPDATE candidate_answers
SET answer = CASE
    WHEN text_answer IS NOT NULL THEN text_answer
    WHEN boolean_answer IS NOT NULL THEN boolean_answer::text
    WHEN salary_answer IS NOT NULL THEN salary_answer::text
    WHEN scale_answer IS NOT NULL THEN scale_answer::text
    WHEN date_answer IS NOT NULL THEN date_answer::text
    WHEN abcdef_answer IS NOT NULL THEN abcdef_answer
    ELSE NULL
END;

-- Drop old columns after data migration
ALTER TABLE candidate_answers
    DROP COLUMN IF EXISTS text_answer,
    DROP COLUMN IF EXISTS boolean_answer,
    DROP COLUMN IF EXISTS salary_answer,
    DROP COLUMN IF EXISTS scale_answer,
    DROP COLUMN IF EXISTS date_answer,
    DROP COLUMN IF EXISTS abcdef_answer;

DROP TABLE IF EXISTS candidate_notes;
create table candidate_notes (
    id bigserial primary key,
    candidate_id bigint not null references candidates(id) on delete cascade, -- Powiązanie z tabelą kandydatów
    note_type text not null, -- Typ notatki (np. "Rozmowa telefoniczna", "Ocena", "Uwagi")
    content text not null,   -- Treść notatki
    created_at timestamp with time zone default now(), -- Data utworzenia notatki
    updated_at timestamp with time zone default now()  -- Data ostatniej aktualizacji
);
