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
    created_at timestamp default now(), -- Data utworzenia notatki
    updated_at timestamp default now()  -- Data ostatniej aktualizacji
);

DROP FUNCTION IF EXISTS get_candidate_with_tests(bigint);
-- Update get_candidate_with_tests function to include notes
CREATE OR REPLACE FUNCTION get_candidate_with_tests(p_candidate_id bigint)
RETURNS TABLE (
    candidate_data jsonb,
    tests_data jsonb,
    notes_data jsonb
) LANGUAGE plpgsql AS $$
BEGIN
    RETURN QUERY
    WITH candidate_info AS (
        SELECT 
            jsonb_build_object(
                'id', c.id,
                'first_name', c.first_name,
                'last_name', c.last_name,
                'email', c.email,
                'phone', c.phone,
                'recruitment_status', c.recruitment_status,
                'created_at', c.created_at,
                'updated_at', c.updated_at,
                'po1_score', ROUND(CAST(c.po1_score AS NUMERIC), 1),
                'po2_score', ROUND(CAST(c.po2_score AS NUMERIC), 1),
                'po2_5_score', ROUND(CAST(c.po2_5_score AS NUMERIC), 1),
                'po3_score', ROUND(CAST(c.po3_score AS NUMERIC), 1),
                'po4_score', ROUND(CAST(c.po4_score AS NUMERIC), 1),
                'total_score', ROUND(CAST(c.total_score AS NUMERIC), 1),
                'po1_started_at', c.po1_started_at,
                'po2_started_at', c.po2_started_at,
                'po3_started_at', c.po3_started_at,
                'po1_completed_at', c.po1_completed_at,
                'po2_completed_at', c.po2_completed_at,
                'po3_completed_at', c.po3_completed_at,
                'score_ko', c.score_ko,
                'score_re', c.score_re,
                'score_w', c.score_w,
                'score_in', c.score_in,
                'score_pz', c.score_pz,
                'score_kz', c.score_kz,
                'score_dz', c.score_dz,
                'score_sw', c.score_sw,
                'access_token_po2', c.access_token_po2,
                'access_token_po3', c.access_token_po3,
                'access_token_po2_is_used', c.access_token_po2_is_used,
                'access_token_po3_is_used', c.access_token_po3_is_used,
                'access_token_po2_expires_at', c.access_token_po2_expires_at,
                'access_token_po3_expires_at', c.access_token_po3_expires_at,
                'campaign', jsonb_build_object(
                    'id', camp.id,
                    'code', camp.code,
                    'title', camp.title,
                    'workplace_location', camp.workplace_location,
                    'contract_type', camp.contract_type,
                    'employment_type', camp.employment_type,
                    'work_start_date', camp.work_start_date,
                    'salary_range_min', camp.salary_range_min,
                    'salary_range_max', camp.salary_range_max,
                    'po1_test_id', camp.po1_test_id,
                    'po2_test_id', camp.po2_test_id,
                    'po2_5_test_id', camp.po2_5_test_id,
                    'po3_test_id', camp.po3_test_id,
                    'po1_test_weight', camp.po1_test_weight,
                    'po2_test_weight', camp.po2_test_weight,
                    'po2_5_test_weight', camp.po2_5_test_weight,
                    'po3_test_weight', camp.po3_test_weight
                )
            ) as cand_data
        FROM candidates c
        JOIN campaigns camp ON c.campaign_id = camp.id
        WHERE c.id = p_candidate_id
    ),
    notes_info AS (
        SELECT jsonb_agg(
            jsonb_build_object(
                'id', n.id,
                'note_type', n.note_type,
                'content', n.content,
                'created_at', n.created_at,
                'updated_at', n.updated_at
            ) ORDER BY n.created_at DESC
        ) as notes
        FROM candidate_notes n
        WHERE n.candidate_id = p_candidate_id
    ),
    questions_with_answers AS (
        SELECT 
            t.id as test_id,
            stages.stage,
            jsonb_agg(
                jsonb_build_object(
                    'id', q.id,
                    'question_text', q.question_text,
                    'answer_type', q.answer_type,
                    'options', q.options,
                    'points', q.points,
                    'order_number', q.order_number,
                    'is_required', q.is_required,
                    'image', q.image,
                    'algorithm_type', q.algorithm_type,
                    'algorithm_params', q.algorithm_params,
                    'answer', (
                        SELECT COALESCE(jsonb_build_object(
                            'id', ca.id,
                            'answer', ca.answer,
                            'points_per_option', ca.points_per_option,
                            'score', ROUND(CAST(ca.score AS NUMERIC), 1),
                            'ai_explanation', ca.ai_explanation
                        ), NULL)
                        FROM candidate_answers ca
                        WHERE ca.question_id = q.id 
                        AND ca.candidate_id = p_candidate_id
                        AND ca.stage = stages.stage
                        LIMIT 1
                    )
                ) ORDER BY q.order_number
            ) as questions
        FROM (
            SELECT 'PO1' as stage, po1_test_id as test_id 
            FROM campaigns 
            WHERE id = (SELECT campaign_id FROM candidates WHERE id = p_candidate_id)
            UNION ALL
            SELECT 'PO2', po2_test_id 
            FROM campaigns 
            WHERE id = (SELECT campaign_id FROM candidates WHERE id = p_candidate_id)
            UNION ALL
            SELECT 'PO2_5', po2_5_test_id 
            FROM campaigns 
            WHERE id = (SELECT campaign_id FROM candidates WHERE id = p_candidate_id)
            UNION ALL
            SELECT 'PO3', po3_test_id 
            FROM campaigns 
            WHERE id = (SELECT campaign_id FROM candidates WHERE id = p_candidate_id)
        ) stages
        JOIN tests t ON stages.test_id = t.id
        JOIN questions q ON q.test_id = t.id
        GROUP BY t.id, stages.stage
    ),
    test_data AS (
        SELECT 
            stages.stage,
            jsonb_build_object(
                'test', jsonb_build_object(
                    'id', t.id,
                    'title', t.title,
                    'test_type', t.test_type,
                    'description', t.description,
                    'passing_threshold', t.passing_threshold,
                    'time_limit_minutes', t.time_limit_minutes
                ),
                'questions', qa.questions
            ) as test_data
        FROM (
            SELECT stage, test_id FROM questions_with_answers
        ) stages
        JOIN tests t ON stages.test_id = t.id
        LEFT JOIN questions_with_answers qa ON qa.test_id = t.id AND qa.stage = stages.stage
    )
    SELECT 
        (SELECT cand_data FROM candidate_info) as candidate_data,
        jsonb_object_agg(stages.stage, test_data) as tests_data,
        (SELECT notes FROM notes_info) as notes_data
    FROM test_data stages
    GROUP BY 1;
END;
$$;
