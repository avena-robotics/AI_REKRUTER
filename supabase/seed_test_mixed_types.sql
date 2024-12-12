TRUNCATE TABLE candidate_answers CASCADE;
TRUNCATE TABLE candidates CASCADE;
TRUNCATE TABLE link_groups_campaigns CASCADE;
TRUNCATE TABLE link_groups_tests CASCADE;
TRUNCATE TABLE link_groups_users CASCADE;
TRUNCATE TABLE questions CASCADE;
TRUNCATE TABLE campaigns CASCADE;
TRUNCATE TABLE tests CASCADE;

-- Insert test
INSERT INTO tests (id, title, test_type, description, passing_threshold, time_limit_minutes, created_at, updated_at) VALUES
    (2, 'Test Kompetencji Mieszanych', 'SURVEY', 'Test sprawdzający różne umiejętności z wykorzystaniem różnych typów odpowiedzi', 70, 60, now(), now());

-- Insert questions with different answer types and algorithms
INSERT INTO questions (id, test_id, question_text, answer_type, points, order_number, is_required, algorithm_type, algorithm_params) VALUES
    -- BOOLEAN questions
    (21, 2, 'Czy w magazynie wysokiego składowania należy stosować zasadę FIFO?', 'BOOLEAN', 5, 1, true, 'EXACT_MATCH', '{"correct_answer": true}'),
    (22, 2, 'Czy pracownik może samodzielnie modyfikować procedury bezpieczeństwa?', 'BOOLEAN', 5, 2, true, 'EXACT_MATCH', '{"correct_answer": false}'),
    (23, 2, 'Czy każdy pracownik powinien przejść szkolenie BHP przed rozpoczęciem pracy?', 'BOOLEAN', 5, 3, true, 'EXACT_MATCH', '{"correct_answer": true}'),
    (24, 2, 'Czy można używać telefonu komórkowego w strefie zagrożenia wybuchem?', 'BOOLEAN', 5, 4, true, 'EXACT_MATCH', '{"correct_answer": false}'),

    -- SCALE questions (0-5)
    (25, 2, 'Jak oceniasz swoją znajomość obsługi wózków widłowych?', 'SCALE', 5, 5, true, 'RIGHT_SIDED', '{"target_value": 5}'),
    (26, 2, 'Oceń swoje umiejętności pracy zespołowej', 'SCALE', 5, 6, true, 'RIGHT_SIDED', '{"target_value": 5}'),
    (27, 2, 'Jak oceniasz swoją znajomość przepisów BHP?', 'SCALE', 5, 7, true, 'RIGHT_SIDED', '{"target_value": 5}'),
    (28, 2, 'Oceń swoją umiejętność zarządzania czasem', 'SCALE', 5, 8, true, 'RIGHT_SIDED', '{"target_value": 5}'),

    -- SALARY questions
    (29, 2, 'Jakie są twoje oczekiwania finansowe (miesięcznie brutto)?', 'SALARY', 5, 9, true, 'RANGE', '{"min": 4000, "max": 7000}'),
    (30, 2, 'Jaka jest minimalna kwota wynagrodzenia, przy której podejmiesz pracę?', 'SALARY', 5, 10, true, 'RANGE', '{"min": 3000, "max": 6000}'),
    (31, 2, 'Jakie wynagrodzenie uznałbyś za satysfakcjonujące po roku pracy?', 'SALARY', 5, 11, true, 'RANGE', '{"min": 5000, "max": 8000}'),
    (32, 2, 'Ile wynosi oczekiwana przez Ciebie stawka za nadgodziny?', 'SALARY', 5, 12, true, 'RANGE', '{"min": 30, "max": 50}'),

    -- DATE questions
    (33, 2, 'Od kiedy możesz rozpocząć pracę?', 'DATE', 5, 13, true, 'LEFT_SIDED', '{"target_date": "2024-03-01"}'),
    (34, 2, 'Kiedy kończy się Twoja aktualna umowa o pracę?', 'DATE', 5, 14, true, 'LEFT_SIDED', '{"target_date": "2024-02-29"}'),
    (35, 2, 'Do kiedy ważne jest Twoje szkolenie BHP?', 'DATE', 5, 15, true, 'RIGHT_SIDED', '{"target_date": "2025-12-31"}'),
    (36, 2, 'Kiedy uzyskałeś ostatnie uprawnienia zawodowe?', 'DATE', 5, 16, true, 'LEFT_SIDED', '{"target_date": "2023-01-01"}'),

    -- ABCDEF questions
    (37, 2, 'Wybierz najważniejszy aspekt bezpieczeństwa w magazynie:\nA) Przestrzeganie procedur\nB) Używanie ŚOI\nC) Szkolenia\nD) Oznakowanie stref\nE) Przeglądy techniczne\nF) Monitoring', 'ABCDEF', 5, 17, true, 'EXACT_MATCH', '{"correct_answer": "A"}'),
    (38, 2, 'Co jest kluczowe w zarządzaniu zespołem?\nA) Delegowanie zadań\nB) Kontrola\nC) Motywacja\nD) Komunikacja\nE) Planowanie\nF) Ocena wyników', 'ABCDEF', 5, 18, true, 'EXACT_MATCH', '{"correct_answer": "D"}'),
    (39, 2, 'Najważniejszy element w obsłudze klienta to:\nA) Szybkość\nB) Uprzejmość\nC) Profesjonalizm\nD) Wiedza\nE) Cierpliwość\nF) Elastyczność', 'ABCDEF', 5, 19, true, 'EXACT_MATCH', '{"correct_answer": "C"}'),
    (40, 2, 'Kluczowy czynnik sukcesu w logistyce:\nA) Planowanie\nB) Terminowość\nC) Optymalizacja\nD) Kontrola\nE) Elastyczność\nF) Technologia', 'ABCDEF', 5, 20, true, 'EXACT_MATCH', '{"correct_answer": "B"}');

-- Insert campaign
INSERT INTO campaigns (
    id, code, title, workplace_location, contract_type, employment_type, 
    work_start_date, duties, requirements, employer_offerings, job_description, 
    salary_range_min, salary_range_max, is_active, po1_test_id, po1_test_weight,
    created_at, updated_at
) VALUES (
    2, 'LOGISTICS_SPECIALIST_2024', 'Specjalista ds. Logistyki', 'Kraków', 
    'Umowa o pracę', 'Pełny etat', '2024-04-01', 
    'Zarządzanie procesami logistycznymi, koordynacja dostaw, optymalizacja procesów magazynowych', 
    'Min. 2 lata doświadczenia w logistyce, znajomość systemów WMS, uprawnienia na wózki widłowe', 
    'Atrakcyjne wynagrodzenie, pakiet benefitów, szkolenia specjalistyczne', 
    'Poszukujemy osoby do zarządzania procesami logistycznymi w nowoczesnym centrum dystrybucyjnym', 
    4500, 7500, true, 2, 100,
    now(), now()
);

-- Link groups with campaign and test
INSERT INTO link_groups_campaigns (group_id, campaign_id) VALUES
    (1, 2), -- Avena
    (2, 2), -- Robotics
    (3, 2), -- Liceum
    (4, 2), -- SPJ5A
    (5, 2), -- PJ5A
    (6, 2), -- SPKG74
    (7, 2), -- P74
    (8, 2), -- P27
    (9, 2); -- Munchies

INSERT INTO link_groups_tests (group_id, test_id) VALUES
    (1, 2), -- Avena
    (2, 2), -- Robotics
    (3, 2), -- Liceum
    (4, 2), -- SPJ5A
    (5, 2), -- PJ5A
    (6, 2), -- SPKG74
    (7, 2), -- P74
    (8, 2), -- P27
    (9, 2); -- Munchies

-- Insert candidates
INSERT INTO candidates (id, campaign_id, first_name, last_name, email, phone, recruitment_status, created_at, updated_at, po1_started_at, po1_completed_at) VALUES
    (4, 2, 'Piotr', 'Nowicki', 'piotr.nowicki@example.com', '+48111222333', 'PO1', now(), now(), now() - interval '2 hours', now() - interval '1 hour'),
    (5, 2, 'Katarzyna', 'Lewandowska', 'katarzyna.lewandowska@example.com', '+48444555666', 'PO1', now(), now(), now() - interval '2 hours', now() - interval '1 hour'),
    (6, 2, 'Tomasz', 'Kowalczyk', 'tomasz.kowalczyk@example.com', '+48777888999', 'PO1', now(), now(), now() - interval '2 hours', now() - interval '1 hour');

-- Insert answers for the first candidate (all correct)
INSERT INTO candidate_answers (
    id, candidate_id, question_id, stage, answer, score, created_at
) VALUES
    -- BOOLEAN answers
    (61, 4, 21, 'PO1', 'true', 5, now()),
    (62, 4, 22, 'PO1', 'false', 5, now()),
    (63, 4, 23, 'PO1', 'true', 5, now()),
    (64, 4, 24, 'PO1', 'false', 5, now()),
    -- SCALE answers
    (65, 4, 25, 'PO1', '5', 5, now()),
    (66, 4, 26, 'PO1', '5', 5, now()),
    (67, 4, 27, 'PO1', '5', 5, now()),
    (68, 4, 28, 'PO1', '5', 5, now()),
    -- SALARY answers
    (69, 4, 29, 'PO1', '5500', 5, now()),
    (70, 4, 30, 'PO1', '4500', 5, now()),
    (71, 4, 31, 'PO1', '6500', 5, now()),
    (72, 4, 32, 'PO1', '40', 5, now()),
    -- DATE answers
    (73, 4, 33, 'PO1', '2024-02-15', 5, now()),
    (74, 4, 34, 'PO1', '2024-02-20', 5, now()),
    (75, 4, 35, 'PO1', '2026-01-01', 5, now()),
    (76, 4, 36, 'PO1', '2022-12-01', 5, now()),
    -- ABCDEF answers
    (77, 4, 37, 'PO1', 'A', 5, now()),
    (78, 4, 38, 'PO1', 'D', 5, now()),
    (79, 4, 39, 'PO1', 'C', 5, now()),
    (80, 4, 40, 'PO1', 'B', 5, now());

-- Insert answers for the second candidate (all wrong)
INSERT INTO candidate_answers (
    id, candidate_id, question_id, stage, answer, score, created_at
) VALUES
    -- BOOLEAN answers
    (81, 5, 21, 'PO1', 'false', 0, now()),
    (82, 5, 22, 'PO1', 'true', 0, now()),
    (83, 5, 23, 'PO1', 'false', 0, now()),
    (84, 5, 24, 'PO1', 'true', 0, now()),
    -- SCALE answers
    (85, 5, 25, 'PO1', '1', 0, now()),
    (86, 5, 26, 'PO1', '1', 0, now()),
    (87, 5, 27, 'PO1', '1', 0, now()),
    (88, 5, 28, 'PO1', '0', 0, now()),
    -- SALARY answers
    (89, 5, 29, 'PO1', '8000', 0, now()),
    (90, 5, 30, 'PO1', '7000', 0, now()),
    (91, 5, 31, 'PO1', '9000', 0, now()),
    (92, 5, 32, 'PO1', '60', 0, now()),
    -- DATE answers
    (93, 5, 33, 'PO1', '2024-06-01', 0, now()),
    (94, 5, 34, 'PO1', '2024-05-01', 0, now()),
    (95, 5, 35, 'PO1', '2024-12-31', 0, now()),
    (96, 5, 36, 'PO1', '2023-12-31', 0, now()),
    -- ABCDEF answers
    (97, 5, 37, 'PO1', 'F', 0, now()),
    (98, 5, 38, 'PO1', 'B', 0, now()),
    (99, 5, 39, 'PO1', 'E', 0, now()),
    (100, 5, 40, 'PO1', 'F', 0, now());

-- Insert answers for the third candidate (mixed results - approximately 50% correct)
INSERT INTO candidate_answers (
    id, candidate_id, question_id, stage, answer, score, created_at
) VALUES
    -- BOOLEAN answers (2/4 correct)
    (101, 6, 21, 'PO1', 'true', 5, now()),
    (102, 6, 22, 'PO1', 'true', 0, now()),
    (103, 6, 23, 'PO1', 'true', 5, now()),
    (104, 6, 24, 'PO1', 'true', 0, now()),
    -- SCALE answers (2/4 correct)
    (105, 6, 25, 'PO1', '5', 5, now()),
    (106, 6, 26, 'PO1', '3', 0, now()),
    (107, 6, 27, 'PO1', '5', 5, now()),
    (108, 6, 28, 'PO1', '2', 0, now()),
    -- SALARY answers (2/4 correct)
    (109, 6, 29, 'PO1', '5500', 5, now()),
    (110, 6, 30, 'PO1', '4500', 5, now()),
    (111, 6, 31, 'PO1', '9000', 0, now()),
    (112, 6, 32, 'PO1', '60', 0, now()),
    -- DATE answers (2/4 correct)
    (113, 6, 33, 'PO1', '2024-02-15', 5, now()),
    (114, 6, 34, 'PO1', '2024-02-20', 5, now()),
    (115, 6, 35, 'PO1', '2024-12-31', 0, now()),
    (116, 6, 36, 'PO1', '2023-12-31', 0, now()),
    -- ABCDEF answers (2/4 correct)
    (117, 6, 37, 'PO1', 'A', 5, now()),
    (118, 6, 38, 'PO1', 'D', 5, now()),
    (119, 6, 39, 'PO1', 'E', 0, now()),
    (120, 6, 40, 'PO1', 'F', 0, now());

-- Dodaj nowy test IQ
INSERT INTO tests (id, title, test_type, description, passing_threshold, time_limit_minutes, created_at, updated_at) VALUES
    (3, 'Test IQ', 'IQ', 'Test sprawdzający zdolności analityczne i logiczne myślenie', 60, 30, now(), now());

-- Dodaj pytania do testu IQ
INSERT INTO questions (id, test_id, question_text, answer_type, points, order_number, is_required, algorithm_type, algorithm_params) VALUES
    -- ABCDEF questions dla testu IQ
    (41, 3, 'Która liczba jest następna w sekwencji: 2, 4, 8, 16, ...?\nA) 32\nB) 24\nC) 28\nD) 30\nE) 20\nF) 22', 'ABCDEF', 10, 1, true, 'EXACT_MATCH', '{"correct_answer": "A"}'),
    (42, 3, 'Które słowo nie pasuje do pozostałych?\nA) Jabłko\nB) Gruszka\nC) Marchewka\nD) Śliwka\nE) Brzoskwinia\nF) Morela', 'ABCDEF', 10, 2, true, 'EXACT_MATCH', '{"correct_answer": "C"}'),
    (43, 3, 'Uzupełnij analogię: Książka : Strona :: Album : ?\nA) Okładka\nB) Zdjęcie\nC) Muzyka\nD) Artysta\nE) Płyta\nF) Tekst', 'ABCDEF', 10, 3, true, 'EXACT_MATCH', '{"correct_answer": "B"}'),
    (44, 3, 'Która figura jest następna w sekwencji?\nA) Kwadrat\nB) Koło\nC) Trójkąt\nD) Romb\nE) Prostokąt\nF) Trapez', 'ABCDEF', 10, 4, true, 'EXACT_MATCH', '{"correct_answer": "C"}'),
    (45, 3, 'Znajdź wzór: 1, 3, 6, 10, ...?\nA) 15\nB) 14\nC) 16\nD) 13\nE) 12\nF) 18', 'ABCDEF', 10, 5, true, 'EXACT_MATCH', '{"correct_answer": "A"}'),
    (46, 3, 'Które słowo jest synonimem "efemeryczny"?\nA) Trwały\nB) Ulotny\nC) Masywny\nD) Stabilny\nE) Solidny\nF) Ciężki', 'ABCDEF', 10, 6, true, 'EXACT_MATCH', '{"correct_answer": "B"}'),
    (47, 3, 'Rozwiąż równanie: 2x + 5 = 13\nA) x = 4\nB) x = 3\nC) x = 5\nD) x = 6\nE) x = 2\nF) x = 8', 'ABCDEF', 10, 7, true, 'EXACT_MATCH', '{"correct_answer": "A"}'),
    (48, 3, 'Wskaż przeciwieństwo słowa "lakoniczny"?\nA) Krótki\nB) Zwięzły\nC) Rozwlekły\nD) Prosty\nE) Jasny\nF) Szybki', 'ABCDEF', 10, 8, true, 'EXACT_MATCH', '{"correct_answer": "C"}'),
    (49, 3, 'Która liczba nie pasuje do pozostałych?\nA) 16\nB) 25\nC) 36\nD) 49\nE) 52\nF) 64', 'ABCDEF', 10, 9, true, 'EXACT_MATCH', '{"correct_answer": "E"}'),
    (50, 3, 'Dokończ sekwencję liter: A, C, F, J, ...?\nA) M\nB) N\nC) O\nD) P\nE) Q\nF) R', 'ABCDEF', 10, 10, true, 'EXACT_MATCH', '{"correct_answer": "C"}');

-- Aktualizuj kampanię, dodając test IQ jako PO2
UPDATE campaigns 
SET 
    po1_test_weight = 60,
    po2_test_id = 3,
    po2_test_weight = 40,
    updated_at = now()
WHERE id = 2;

-- Dodaj odpowiedzi Piotra (wszystkie poprawne)
INSERT INTO candidate_answers (id, candidate_id, question_id, stage, answer, score, created_at) VALUES
    (121, 4, 41, 'PO2', 'A', 10, now()),
    (122, 4, 42, 'PO2', 'C', 10, now()),
    (123, 4, 43, 'PO2', 'B', 10, now()),
    (124, 4, 44, 'PO2', 'C', 10, now()),
    (125, 4, 45, 'PO2', 'A', 10, now()),
    (126, 4, 46, 'PO2', 'B', 10, now()),
    (127, 4, 47, 'PO2', 'A', 10, now()),
    (128, 4, 48, 'PO2', 'C', 10, now()),
    (129, 4, 49, 'PO2', 'E', 10, now()),
    (130, 4, 50, 'PO2', 'C', 10, now());

-- Dodaj odpowiedzi Katarzyny (wszystkie błędne)
INSERT INTO candidate_answers (id, candidate_id, question_id, stage, answer, score, created_at) VALUES
    (131, 5, 41, 'PO2', 'B', 0, now()),
    (132, 5, 42, 'PO2', 'A', 0, now()),
    (133, 5, 43, 'PO2', 'C', 0, now()),
    (134, 5, 44, 'PO2', 'A', 0, now()),
    (135, 5, 45, 'PO2', 'B', 0, now()),
    (136, 5, 46, 'PO2', 'A', 0, now()),
    (137, 5, 47, 'PO2', 'B', 0, now()),
    (138, 5, 48, 'PO2', 'A', 0, now()),
    (139, 5, 49, 'PO2', 'A', 0, now()),
    (140, 5, 50, 'PO2', 'A', 0, now());

-- Dodaj odpowiedzi Tomasza (60% poprawnych)
INSERT INTO candidate_answers (id, candidate_id, question_id, stage, answer, score, created_at) VALUES
    (141, 6, 41, 'PO2', 'A', 10, now()), -- poprawna
    (142, 6, 42, 'PO2', 'C', 10, now()), -- poprawna
    (143, 6, 43, 'PO2', 'B', 10, now()), -- poprawna
    (144, 6, 44, 'PO2', 'A', 0, now()),  -- błędna
    (145, 6, 45, 'PO2', 'B', 0, now()),  -- błędna
    (146, 6, 46, 'PO2', 'B', 10, now()), -- poprawna
    (147, 6, 47, 'PO2', 'B', 0, now()),  -- błędna
    (148, 6, 48, 'PO2', 'C', 10, now()), -- poprawna
    (149, 6, 49, 'PO2', 'A', 0, now()),  -- błędna
    (150, 6, 50, 'PO2', 'C', 10, now()); -- poprawna

-- Zmiana odpowiedzi Tomasza na więcej poprawnych (75% poprawnych = 75 punktów)
UPDATE candidate_answers 
SET 
    answer = true,
    score = 5
WHERE id = 102 AND candidate_id = 6;  -- pytanie 22

UPDATE candidate_answers 
SET 
    answer = false,
    score = 5
WHERE id = 104 AND candidate_id = 6;  -- pytanie 24

UPDATE candidate_answers 
SET 
    answer = 5,
    score = 5
WHERE id = 106 AND candidate_id = 6;  -- pytanie 26

UPDATE candidate_answers 
SET 
    answer = 5,
    score = 5
WHERE id = 108 AND candidate_id = 6;  -- pytanie 28

UPDATE candidate_answers 
SET 
    answer = 6000,
    score = 5
WHERE id = 111 AND candidate_id = 6;  -- pytanie 31

UPDATE candidate_answers 
SET 
    answer = 45,
    score = 5
WHERE id = 112 AND candidate_id = 6;  -- pytanie 32

UPDATE candidate_answers 
SET 
    answer = '2025-12-31',
    score = 5
WHERE id = 115 AND candidate_id = 6;  -- pytanie 35

UPDATE candidate_answers 
SET 
    answer = '2022-12-01',
    score = 5
WHERE id = 116 AND candidate_id = 6;  -- pytanie 36

UPDATE candidate_answers 
SET 
    answer = 'C',
    score = 5
WHERE id = 119 AND candidate_id = 6;  -- pytanie 39

UPDATE candidate_answers 
SET 
    answer = 'B',
    score = 5
WHERE id = 120 AND candidate_id = 6;  -- pytanie 40;

-- Popraw odpowiedzi Piotra na SCALE
UPDATE candidate_answers 
SET answer = 5, score = 5
WHERE candidate_id = 4 AND question_id IN (25, 26, 27, 28);

-- Popraw odpowiedzi Piotra na SALARY
UPDATE candidate_answers 
SET 
    answer = CASE 
        WHEN question_id = 29 THEN 5500
        WHEN question_id = 30 THEN 4500
        WHEN question_id = 31 THEN 6500
        WHEN question_id = 32 THEN 40
    END,
    score = 5
WHERE candidate_id = 4 AND question_id IN (29, 30, 31, 32);

-- Popraw odpowiedzi Piotra na DATE
UPDATE candidate_answers 
SET 
    answer = CASE 
        WHEN question_id = 33 THEN '2024-02-15'::date
        WHEN question_id = 34 THEN '2024-02-20'::date
        WHEN question_id = 35 THEN '2026-01-01'::date
        WHEN question_id = 36 THEN '2022-12-01'::date
    END,
    score = 5
WHERE candidate_id = 4 AND question_id IN (33, 34, 35, 36);