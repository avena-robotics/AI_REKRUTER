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
        is_required
    )
    SELECT 
        (SELECT id FROM inserted_test),
        question_text,
        answer_type::answer_type,
        options::jsonb,
        points,
        order_number,
        is_required
    FROM (VALUES
        ('Jakie jest Twoje oczekiwane wynagrodzenie miesięczne netto (PLN)?', 'SALARY', NULL, 0, 1, true),
        
        ('Od kiedy możesz rozpocząć pracę?', 'DATE', NULL, 0, 2, true),
        
        ('Preferowany model pracy:', 'TEXT', NULL, 0, 3, true),
        
        ('Czy jesteś gotów/gotowa do relokacji w przypadku takiej potrzeby?', 'BOOLEAN', NULL, 0, 4, true),
        
        ('Czy wyrażasz zgodę na odbywanie podróży służbowych?', 'BOOLEAN', NULL, 0, 5, true),
        
        ('Opisz swoje dotychczasowe doświadczenie zawodowe:', 'TEXT', NULL, 0, 6, true),
        
        ('Jakie jest Twoje wykształcenie i kierunek studiów?', 'TEXT', NULL, 0, 7, true),
        
        ('Wymień swoje umiejętności i kompetencje związane ze stanowiskiem:', 'TEXT', NULL, 0, 8, true),
        
        ('Oceń swoją znajomość języka angielskiego (0 - brak, 5 - biegły):', 'SCALE', NULL, 0, 9, true),
        
        ('Jakie są Twoje główne oczekiwania wobec nowego miejsca pracy?', 'TEXT', NULL, 0, 10, true),
        
        ('Wymień swoje największe osiągnięcia zawodowe:', 'TEXT', NULL, 0, 11, false),
        
        ('Jakie certyfikaty i szkolenia zawodowe posiadasz?', 'TEXT', NULL, 0, 12, false),
        
        ('Ile godzin tygodniowo możesz pracować?', 'TEXT', NULL, 0, 13, true),
        
        ('Czy posiadasz prawo jazdy?', 'BOOLEAN', NULL, 0, 14, true),
        
        ('Jakie są Twoje zainteresowania zawodowe?', 'TEXT', NULL, 0, 15, false)
    ) AS t(question_text, answer_type, options, points, order_number, is_required)
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