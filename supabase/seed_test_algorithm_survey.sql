-- Insert Algorithm Test Survey
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
        'Algorithm Test Survey', 
        'SURVEY', 
        'Test sprawdzający wszystkie typy algorytmów z różnymi typami odpowiedzi.', 
        0, 
        30, 
        now(), 
        now()
    )
    RETURNING id
),

-- Insert test questions
questions_insert AS (
    INSERT INTO questions (
        test_id,
        question_text,
        answer_type,
        options,
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
        options::jsonb,
        points,
        order_number,
        is_required,
        algorithm_type::algorithm_type,
        algorithm_params::jsonb
    FROM (VALUES
        -- TEXT type tests
        ('TEXT - No Algorithm', 'TEXT', NULL, 0, 1, false, 'NO_ALGORITHM', NULL),
        ('TEXT - Exact Match', 'TEXT', NULL, 10, 2, false, 'EXACT_MATCH', '{"correct_answer": "dokładna odpowiedź"}'::jsonb),
        ('TEXT - AI Evaluation', 'TEXT', NULL, 10, 3, false, 'EVALUATION_BY_AI', '{
            "evaluation_focus": "Sprawdź czy odpowiedź zawiera kluczowe elementy: definicję, przykłady i zastosowanie.",
            "scoring_criteria": "10 punktów: Pełna odpowiedź zawierająca wszystkie elementy\n7.5 punktów: Dobra odpowiedź z drobnymi brakami\n5 punktów: Podstawowa odpowiedź\n2.5 punktów: Słaba odpowiedź\n0 punktów: Brak odpowiedzi lub całkowicie błędna"
        }'::jsonb),
        
        -- BOOLEAN type tests
        ('BOOLEAN - No Algorithm', 'BOOLEAN', NULL, 0, 4, false, 'NO_ALGORITHM', NULL),
        ('BOOLEAN - Exact Match', 'BOOLEAN', NULL, 10, 5, false, 'EXACT_MATCH', '{"correct_answer": true}'::jsonb),
        
        -- SCALE type tests (0-5)
        ('SCALE - No Algorithm', 'SCALE', NULL, 0, 6, false, 'NO_ALGORITHM', NULL),
        ('SCALE - Right Sided', 'SCALE', NULL, 10, 7, false, 'RIGHT_SIDED', '{"correct_answer": 4, "max_value": 5}'::jsonb),
        ('SCALE - Left Sided', 'SCALE', NULL, 10, 8, false, 'LEFT_SIDED', '{"min_value": 0, "correct_answer": 2}'::jsonb),
        ('SCALE - Center', 'SCALE', NULL, 10, 9, false, 'CENTER', '{"min_value": 0, "correct_answer": 3, "max_value": 5}'::jsonb),
        ('SCALE - Range', 'SCALE', NULL, 10, 10, false, 'RANGE', '{"min_value": 2, "max_value": 4}'::jsonb),
        ('SCALE - Exact Match', 'SCALE', NULL, 10, 11, false, 'EXACT_MATCH', '{"correct_answer": 3}'::jsonb),
        
        -- SALARY type tests
        ('SALARY - No Algorithm', 'SALARY', NULL, 0, 12, false, 'NO_ALGORITHM', NULL),
        ('SALARY - Right Sided', 'SALARY', NULL, 10, 13, false, 'RIGHT_SIDED', '{"correct_answer": 5000, "max_value": 10000}'::jsonb),
        ('SALARY - Left Sided', 'SALARY', NULL, 10, 14, false, 'LEFT_SIDED', '{"min_value": 3000, "correct_answer": 7000}'::jsonb),
        ('SALARY - Center', 'SALARY', NULL, 10, 15, false, 'CENTER', '{"min_value": 3000, "correct_answer": 5000, "max_value": 7000}'::jsonb),
        ('SALARY - Range', 'SALARY', NULL, 10, 16, false, 'RANGE', '{"min_value": 4000, "max_value": 6000}'::jsonb),
        ('SALARY - Exact Match', 'SALARY', NULL, 10, 17, false, 'EXACT_MATCH', '{"correct_answer": 5000}'::jsonb),
        
        -- DATE type tests
        ('DATE - No Algorithm', 'DATE', NULL, 0, 18, false, 'NO_ALGORITHM', NULL),
        ('DATE - Right Sided', 'DATE', NULL, 10, 19, false, 'RIGHT_SIDED', '{"correct_answer": "2024-06-01", "max_value": "2024-12-31"}'::jsonb),
        ('DATE - Left Sided', 'DATE', NULL, 10, 20, false, 'LEFT_SIDED', '{"min_value": "2024-01-01", "correct_answer": "2024-03-01"}'::jsonb),
        ('DATE - Center', 'DATE', NULL, 10, 21, false, 'CENTER', '{"min_value": "2024-01-01", "correct_answer": "2024-06-01", "max_value": "2024-12-31"}'::jsonb),
        ('DATE - Range', 'DATE', NULL, 10, 22, false, 'RANGE', '{"min_value": "2024-03-01", "max_value": "2024-09-01"}'::jsonb),
        ('DATE - Exact Match', 'DATE', NULL, 10, 23, false, 'EXACT_MATCH', '{"correct_answer": "2024-06-01"}'::jsonb),
        
        -- ABCDEF type tests
        ('ABCDEF - No Algorithm', 'ABCDEF', '{"A": "Opcja A", "B": "Opcja B", "C": "Opcja C", "D": "Opcja D", "E": "Opcja E", "F": "Opcja F"}'::jsonb, 0, 24, false, 'NO_ALGORITHM', NULL),
        ('ABCDEF - Exact Match', 'ABCDEF', '{"A": "Opcja A", "B": "Opcja B", "C": "Opcja C", "D": "Opcja D", "E": "Opcja E", "F": "Opcja F"}'::jsonb, 10, 25, false, 'EXACT_MATCH', '{"correct_answer": "C"}'::jsonb)
        
    ) AS t(question_text, answer_type, options, points, order_number, is_required, algorithm_type, algorithm_params)
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
SELECT 'Algorithm Test Survey, questions and group links inserted successfully' as result; 