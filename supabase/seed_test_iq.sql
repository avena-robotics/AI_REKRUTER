-- Insert IQ test
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
        'Test kompetencji logicznych', 
        'IQ', 
        'Prezentowany test składa się z 20 zadań.  W każdym zadaniu należy odkryć logiczną zasadę i wybrać właściwą spośród podanych sześciu odpowiedzi.', 
        75, 
        45, 
        now(), 
        now()
    )
    RETURNING id
),

-- Insert IQ questions placeholder (20 questions)
questions_insert AS (
    INSERT INTO questions (
        test_id,
        question_text,
        answer_type,
        options,
        points,
        order_number,
        is_required,
        image,
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
        image,
        algorithm_type::algorithm_type,
        algorithm_params::jsonb
    FROM (VALUES
        ('Pytanie 1', 'ABCDEF', null, 10, 1, false, null, 'EXACT_MATCH', '{"correct_answer": "f"}'::jsonb),
        ('Pytanie 2', 'ABCDEF', null, 10, 2, false, null, 'EXACT_MATCH', '{"correct_answer": "c"}'::jsonb),
        ('Pytanie 3', 'ABCDEF', null, 10, 3, false, null, 'EXACT_MATCH', {'correct_answer': 'b'}),
        ('Pytanie 4', 'ABCDEF', null, 10, 4, false, null, 'EXACT_MATCH', {'correct_answer': 'c'}),
        ('Pytanie 5', 'ABCDEF', null, 10, 5, false, null, 'EXACT_MATCH', {'correct_answer': 'a'}),
        ('Pytanie 6', 'ABCDEF', null, 10, 6, false, null, 'EXACT_MATCH', {'correct_answer': 'd'}),
        ('Pytanie 7', 'ABCDEF', null, 10, 7, false, null, 'EXACT_MATCH', {'correct_answer': 'a'}),
        ('Pytanie 8', 'ABCDEF', null, 10, 8, false, null, 'EXACT_MATCH', {'correct_answer': 'd'}),
        ('Pytanie 9', 'ABCDEF', null, 10, 9, false, null, 'EXACT_MATCH', {'correct_answer': 'd'}),
        ('Pytanie 10', 'ABCDEF', null, 10, 10, false, null, 'EXACT_MATCH', {'correct_answer': 'e'}),
        ('Pytanie 11', 'ABCDEF', null, 10, 11, false, null, 'EXACT_MATCH', {'correct_answer': 'f'}),
        ('Pytanie 12', 'ABCDEF', null, 10, 12, false, null, 'EXACT_MATCH', {'correct_answer': 'f'}),
        ('Pytanie 13', 'ABCDEF', null, 10, 13, false, null, 'EXACT_MATCH', {'correct_answer': 'c'}),
        ('Pytanie 14', 'ABCDEF', null, 10, 14, false, null, 'EXACT_MATCH', {'correct_answer': 'b'}),
        ('Pytanie 15', 'ABCDEF', null, 10, 15, false, null, 'EXACT_MATCH', {'correct_answer': 'c'}),
        ('Pytanie 16', 'ABCDEF', null, 10, 16, false, null, 'EXACT_MATCH', {'correct_answer': 'd'}),
        ('Pytanie 17', 'ABCDEF', null, 10, 17, false, null, 'EXACT_MATCH', {'correct_answer': 'a'}),
        ('Pytanie 18', 'ABCDEF', null, 10, 18, false, null, 'EXACT_MATCH', {'correct_answer': 'c'}),
        ('Pytanie 19', 'ABCDEF', null, 10, 19, false, null, 'EXACT_MATCH', {'correct_answer': 'c'}),
        ('Pytanie 20', 'ABCDEF', null, 10, 20, false, null, 'EXACT_MATCH', {'correct_answer': 'a'})
    ) AS t(
        question_text, 
        answer_type, 
        options, 
        points, 
        order_number, 
        is_required, 
        image,
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
SELECT 'IQ test, questions, images and group links inserted successfully' as result;