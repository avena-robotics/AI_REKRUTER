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

-- Update get_candidate_with_tests function to handle float scores
CREATE OR REPLACE FUNCTION get_candidate_with_tests(p_candidate_id bigint)
RETURNS TABLE (
    candidate_data jsonb,
    tests_data jsonb
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
                'po1_score', CAST(ROUND(CAST(c.po1_score AS NUMERIC), 1) AS FLOAT),
                'po2_score', CAST(ROUND(CAST(c.po2_score AS NUMERIC), 1) AS FLOAT),
                'po2_5_score', CAST(ROUND(CAST(c.po2_5_score AS NUMERIC), 1) AS FLOAT),
                'po3_score', CAST(ROUND(CAST(c.po3_score AS NUMERIC), 1) AS FLOAT),
                'po4_score', CAST(ROUND(CAST(c.po4_score AS NUMERIC), 1) AS FLOAT),
                'total_score', CAST(ROUND(CAST(c.total_score AS NUMERIC), 1) AS FLOAT),
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
                            'text_answer', ca.text_answer,
                            'boolean_answer', ca.boolean_answer,
                            'salary_answer', ca.salary_answer,
                            'scale_answer', ca.scale_answer,
                            'date_answer', ca.date_answer,
                            'abcdef_answer', ca.abcdef_answer,
                            'points_per_option', ca.points_per_option,
                            'score', ROUND(CAST(ca.score AS NUMERIC), 1)
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
        jsonb_object_agg(stages.stage, test_data) as tests_data
    FROM test_data stages
    GROUP BY 1;
END;
$$;