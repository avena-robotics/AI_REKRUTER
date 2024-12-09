-- Insert EQ_EVALUATION test
WITH inserted_test AS (
    INSERT INTO tests (
        title, 
        test_type, 
        description, 
        passing_threshold, 
        time_limit_minutes, 
        created_at, 
        updated_at
    ) 
    VALUES (
        'Kwestionariusz oceny kompetencji EQ', 
        'EQ_EVALUATION', 
        'Oceń poziom kompetencji kandydata w skali od 10 do 20, gdzie 10 oznacza bardzo niski poziom, a 20 bardzo wysoki poziom.', 
        75, 
        30, 
        now(), 
        now()
    )
    RETURNING id
),

-- Insert EQ_EVALUATION questions
questions_insert AS (
    INSERT INTO questions (
        test_id,
        question_text,
        answer_type,
        points,
        order_number,
        is_required,
        algorithm_type,
        algorithm_params
    )
    SELECT 
        (SELECT id FROM inserted_test),
        question_text,
        answer_type::answer_type,
        points,
        order_number,
        is_required,
        algorithm_type::algorithm_type,
        algorithm_params::jsonb
    FROM (VALUES
        (
            'KO',
            'SALARY',
            10,
            1,
            true,
            'RANGE',
            '{"min_value": 10, "max_value": 20}'::jsonb
        ),
        (
            'RE',
            'SALARY',
            10,
            2,
            true,
            'RANGE',
            '{"min_value": 10, "max_value": 20}'::jsonb
        ),
        (
            'W',
            'SALARY',
            10,
            3,
            true,
            'RANGE',
            '{"min_value": 10, "max_value": 20}'::jsonb
        ),
        (
            'IN',
            'SALARY',
            10,
            4,
            true,
            'RANGE',
            '{"min_value": 10, "max_value": 20}'::jsonb
        ),
        (
            'PZ',
            'SALARY',
            10,
            5,
            true,
            'RANGE',
            '{"min_value": 10, "max_value": 20}'::jsonb
        ),
        (
            'KZ',
            'SALARY',
            10,
            6,
            true,
            'RANGE',
            '{"min_value": 10, "max_value": 20}'::jsonb
        ),
        (
            'DZ',
            'SALARY',
            10,
            7,
            true,
            'RANGE',
            '{"min_value": 10, "max_value": 20}'::jsonb
        ),
        (
            'SW',
            'SALARY',
            10,
            8,
            true,
            'RANGE',
            '{"min_value": 10, "max_value": 20}'::jsonb
        )
    ) AS t(
        question_text,
        answer_type,
        points,
        order_number,
        is_required,
        algorithm_type,
        algorithm_params
    )
),

-- Link test with groups
groups_link AS (
    INSERT INTO link_groups_tests (group_id, test_id)
    SELECT group_id, (SELECT id FROM inserted_test)
    FROM (VALUES 
        (1), -- Avena
        (2), -- Robotics
        (3), -- Liceum
        (4), -- SPJ5A
        (5), -- PJ5A
        (6), -- SPKG74
        (7), -- P74
        (8), -- P27
        (9)  -- Munchies
    ) AS t(group_id)
)
SELECT 'EQ_EVALUATION test, questions and group links inserted successfully' as result; 