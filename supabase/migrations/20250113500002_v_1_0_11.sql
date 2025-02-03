-- 1. Dodanie kolumny is_critical do tabeli questions
ALTER TABLE questions 
ADD COLUMN is_critical BOOLEAN NOT NULL DEFAULT false;

-- Dodanie nowego statusu do typu enum
ALTER TYPE recruitment_status ADD VALUE IF NOT EXISTS 'REJECTED_CRITICAL';

-- 2. Migracja dla istniejących pytań
UPDATE questions 
SET is_critical = false 
WHERE is_critical IS NULL; 