-- Insert Survey test
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
        'Ankieta kwalifikacyjna', 
        'SURVEY', 
        'Prosimy o wypełnienie poniższej ankiety, która pomoże nam lepiej poznać Twoje doświadczenie i oczekiwania zawodowe.', 
        0, 
        30, 
        now(), 
        now()
    )
    RETURNING id
),

-- Insert Survey questions
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
        ('Jakie jest Twoje oczekiwane wynagrodzenie miesięczne netto (PLN)?', 'SALARY', NULL, 10, 1, true, 'RANGE', '{"min_value": 1000, "max_value": 10000}'::jsonb),
        
        ('Od kiedy możesz rozpocząć pracę?', 'DATE', NULL, 10, 2, true, 'RIGHT_SIDED', '{"correct_answer": "2025-01-01", "max_value": "2025-02-01"}'::jsonb),
        
        ('Preferowany model pracy:', 'TEXT', NULL, 0, 3, true, 'NO_ALGORITHM', NULL),
        
        ('Czy jesteś gotów/gotowa do relokacji w przypadku takiej potrzeby?', 'BOOLEAN', NULL, 10, 4, true, 'EXACT_MATCH', '{"correct_answer": true}'::jsonb),
        
        ('Czy wyrażasz zgodę na odbywanie podróży służbowych?', 'BOOLEAN', NULL, 10, 5, true, 'EXACT_MATCH', '{"correct_answer": true}'::jsonb),
        
        ('Opisz swoje dotychczasowe doświadczenie zawodowe:', 'TEXT', NULL, 0, 6, false, 'NO_ALGORITHM', NULL),
        
        ('Jakie jest Twoje wykształcenie i kierunek studiów?', 'TEXT', NULL, 0, 7, false, 'NO_ALGORITHM', NULL),
        
        ('Wymień swoje umiejętności i kompetencje związane ze stanowiskiem:', 'TEXT', NULL, 0, 8, false, 'NO_ALGORITHM', NULL),
        
        ('Oceń swoją znajomość języka angielskiego (0 - brak, 5 - biegły):', 'SCALE', NULL, 10, 9, true, 'LEFT_SIDED', '{"min_value": 0, "correct_answer": 4}'::jsonb),
        
        ('Jakie są Twoje główne oczekiwania wobec nowego miejsca pracy?', 'TEXT', NULL, 0, 10, false, 'NO_ALGORITHM', NULL),
        
        ('Wymień swoje największe osiągnięcia zawodowe:', 'TEXT', NULL, 0, 11, false, 'NO_ALGORITHM', NULL),
        
        ('Jakie certyfikaty i szkolenia zawodowe posiadasz?', 'TEXT', NULL, 0, 12, false, 'NO_ALGORITHM', NULL),
        
        ('Ile godzin tygodniowo możesz pracować?', 'NUMERIC', NULL, 10, 13, true, 'RANGE', '{"min_value": 20, "max_value": 0}'::jsonb),
        
        ('Czy posiadasz prawo jazdy?', 'BOOLEAN', NULL, 10, 14, true, 'EXACT_MATCH', '{"correct_answer": true}'::jsonb),

        ('Ile lat doświadczenia zawodowego posiadasz?', 'NUMERIC', NULL, 10, 15, true, 'RANGE', '{"min_value": 0, "max_value": 50}'::jsonb),
        
        ('Jakie są Twoje zainteresowania zawodowe?', 'TEXT', NULL, 0, 16, false, 'NO_ALGORITHM', NULL)
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
SELECT 'Survey test, questions and group links inserted successfully' as result; 