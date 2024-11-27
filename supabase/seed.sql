-- Clear existing data (w odwrotnej kolejności niż zależności)
TRUNCATE TABLE candidate_answers CASCADE;
TRUNCATE TABLE candidates CASCADE;
TRUNCATE TABLE link_groups_tests CASCADE;
TRUNCATE TABLE link_groups_campaigns CASCADE;
TRUNCATE TABLE link_groups_users CASCADE;
TRUNCATE TABLE questions CASCADE;
TRUNCATE TABLE campaigns CASCADE;
TRUNCATE TABLE tests CASCADE;
TRUNCATE TABLE groups CASCADE;
TRUNCATE TABLE users CASCADE;

-- Wprowadzanie danych w kolejności zależności
-- 1. Najpierw users (brak zależności)
INSERT INTO users (id, first_name, last_name, email, phone, can_edit_tests) VALUES 
(2, 'Sebastian', 'Krajna', 'sebastian.krajna@pomagier.info', null, true),
(3, 'Maciej', 'Szulc', 'maciej.szulc@pomagier.info', null, true);

-- 2. Grupy (brak zależności)
INSERT INTO groups (id, name) VALUES
(1, 'Grupa Pusta'),                  
(2, 'Grupa Sebastian'),              
(3, 'Grupa Sebastian i Maciej'),     
(4, 'Grupa Maciej');                 

-- 3. Powiązania użytkowników z grupami
INSERT INTO link_groups_users (group_id, user_id) VALUES
(2, 2),                    
(3, 2), (3, 3),           
(4, 3);                    

-- 4. Testy (brak zależności)
INSERT INTO tests (id, title, test_type, description, passing_threshold, time_limit_minutes) VALUES
-- Testy dla Grupy Sebastian (grupa 2)
(1, 'Ankieta wstępna PO1', 'SURVEY', 'Test PO1 Grupa Sebastian - Ankieta', 70, 30),
(2, 'Test IQ - Etap PO1', 'IQ', 'Test PO1 Grupa Sebastian - IQ', 75, 45),
(3, 'Ankieta pogłębiona PO2', 'SURVEY', 'Test PO2 Grupa Sebastian - Ankieta', 70, 30),
(4, 'Test EQ - Etap PO2', 'EQ', 'Test PO2 Grupa Sebastian - EQ', 80, 60),
(5, 'Test IQ zaawansowany PO3', 'IQ', 'Test PO3 Grupa Sebastian - IQ', 85, 45),
(6, 'Test EQ zaawansowany PO3', 'EQ', 'Test PO3 Grupa Sebastian - EQ', 75, 60),

-- Testy dla Grupy Maciej (grupa 4)
(7, 'Ankieta kwalifikacyjna PO1', 'SURVEY', 'Test PO1 Grupa Maciej - Ankieta', 70, 30),
(8, 'Test IQ podstawowy PO1', 'IQ', 'Test PO1 Grupa Maciej - IQ', 75, 45),
(9, 'Ankieta kompetencyjna PO2', 'SURVEY', 'Test PO2 Grupa Maciej - Ankieta', 70, 30),
(10, 'Test EQ podstawowy PO2', 'EQ', 'Test PO2 Grupa Maciej - EQ', 80, 60),
(11, 'Test IQ rozszerzony PO3', 'IQ', 'Test PO3 Grupa Maciej - IQ', 85, 45),
(12, 'Test EQ rozszerzony PO3', 'EQ', 'Test PO3 Grupa Maciej - EQ', 75, 60),

-- Testy dla obu grup (Sebastian + Maciej)
(13, 'Ankieta wspólna PO1', 'SURVEY', 'Test PO1 Grupy Sebastian+Maciej - Ankieta', 70, 30),
(14, 'Test IQ wspólny PO1', 'IQ', 'Test PO1 Grupy Sebastian+Maciej - IQ', 75, 45),
(15, 'Ankieta wspólna PO2', 'SURVEY', 'Test PO2 Grupy Sebastian+Maciej - Ankieta', 70, 30),
(16, 'Test EQ wspólny PO2', 'EQ', 'Test PO2 Grupy Sebastian+Maciej - EQ', 80, 60),
(17, 'Test IQ wspólny PO3', 'IQ', 'Test PO3 Grupy Sebastian+Maciej - IQ', 85, 45),
(18, 'Test EQ wspólny PO3', 'EQ', 'Test PO3 Grupy Sebastian+Maciej - EQ', 75, 60),

-- Testy bez przypisanej grupy
(19, 'Ankieta ogólna PO1', 'SURVEY', 'Test PO1 Bez Grupy - Ankieta', 70, 30),
(20, 'Test IQ ogólny PO1', 'IQ', 'Test PO1 Bez Grupy - IQ', 75, 45),
(21, 'Ankieta ogólna PO2', 'SURVEY', 'Test PO2 Bez Grupy - Ankieta', 70, 30),
(22, 'Test EQ ogólny PO2', 'EQ', 'Test PO2 Bez Grupy - EQ', 80, 60),
(23, 'Test IQ ogólny PO3', 'IQ', 'Test PO3 Bez Grupy - IQ', 85, 45),
(24, 'Test EQ ogólny PO3', 'EQ', 'Test PO3 Bez Grupy - EQ', 75, 60),

-- Testy dla pustej grupy
(25, 'Ankieta standardowa PO1', 'SURVEY', 'Test PO1 Grupa Pusta - Ankieta', 70, 30),
(26, 'Test IQ standardowy PO1', 'IQ', 'Test PO1 Grupa Pusta - IQ', 75, 45),
(27, 'Ankieta standardowa PO2', 'SURVEY', 'Test PO2 Grupa Pusta - Ankieta', 70, 30),
(28, 'Test EQ standardowy PO2', 'EQ', 'Test PO2 Grupa Pusta - EQ', 80, 60),
(29, 'Test IQ standardowy PO3', 'IQ', 'Test PO3 Grupa Pusta - IQ', 85, 45),
(30, 'Test EQ standardowy PO3', 'EQ', 'Test PO3 Grupa Pusta - EQ', 75, 60);

-- 5. Pytania (zależne od tests)
INSERT INTO questions (
    id,  -- Dodajemy explicit id
    test_id, question_text, answer_type, points, order_number, 
    is_required, correct_answer_text, correct_answer_boolean, 
    correct_answer_numeric, correct_answer_scale, correct_answer_date, 
    correct_answer_abcdef
) VALUES
-- Test 1 (PO1 Grupa Sebastian - Ankieta) - wszystkie typy pytań
(1, 1, 'Opisz swoje doświadczenie zawodowe', 'TEXT', 10, 1, true, 'Minimum 2 lata doświadczenia w zawodzie', null, null, null, null, null),
(2, 1, 'Czy posiadasz prawo jazdy?', 'BOOLEAN', 5, 2, true, null, true, null, null, null, null),
(3, 1, 'Oceń swoją znajomość języka angielskiego', 'SCALE', 15, 3, true, null, null, null, 4, null, null),
(4, 1, 'Jakie są twoje oczekiwania finansowe?', 'SALARY', 0, 4, true, null, null, 5000, null, null, null),
(5, 1, 'Od kiedy możesz rozpocząć pracę?', 'DATE', 0, 5, true, null, null, null, null, '2024-03-01', null),
(6, 1, 'Wybierz preferowany typ umowy: A) UoP, B) B2B, C) UZ, D) UoD', 'ABCDEF', 5, 6, true, null, null, null, null, null, 'A'),

-- Pozostałe testy Grupy Sebastian
(7, 2, 'Test IQ: Rozwiąż ciąg: 2,4,6,8,...', 'TEXT', 10, 1, true, '10', null, null, null, null, null),
(8, 3, 'Opisz swoje największe osiągnięcie zawodowe', 'TEXT', 15, 1, true, null, null, null, null, null, null),
(9, 4, 'Oceń swoją odporność na stres', 'SCALE', 10, 1, true, null, null, null, 4, null, null),
(10, 5, 'Rozwiąż zadanie logiczne...', 'TEXT', 20, 1, true, 'Odpowiedź C', null, null, null, null, null),
(11, 6, 'Jak reagujesz w sytuacjach konfliktowych?', 'TEXT', 15, 1, true, null, null, null, null, null, null),

-- Testy Grupy Maciej
(12, 7, 'Jakie są twoje mocne strony?', 'TEXT', 10, 1, true, null, null, null, null, null, null),
(13, 8, 'Test IQ: Znajdź brakujący element', 'ABCDEF', 15, 1, true, null, null, null, null, null, 'C'),
(14, 9, 'Opisz swoją idealną kulturę organizacyjną', 'TEXT', 10, 1, true, null, null, null, null, null, null),
(15, 10, 'Jak radzisz sobie z krytyką?', 'SCALE', 10, 1, true, null, null, null, 3, null, null),
(16, 11, 'Rozwiąż zagadkę logiczną...', 'TEXT', 20, 1, true, 'Odpowiedź D', null, null, null, null, null),
(17, 12, 'Oceń swoje umiejętności przywódcze', 'SCALE', 15, 1, true, null, null, null, 4, null, null),

-- Testy dla obu grup
(18, 13, 'Jakie są twoje cele zawodowe?', 'TEXT', 10, 1, true, null, null, null, null, null, null),
(19, 14, 'Test IQ: Uzupełnij analogię', 'ABCDEF', 15, 1, true, null, null, null, null, null, 'B'),
(20, 15, 'Opisz trudną sytuację zawodową', 'TEXT', 10, 1, true, null, null, null, null, null, null),
(21, 16, 'Jak reagujesz na zmiany?', 'SCALE', 10, 1, true, null, null, null, 4, null, null),
(22, 17, 'Rozwiąż problem matematyczny...', 'TEXT', 20, 1, true, '42', null, null, null, null, null),
(23, 18, 'Oceń swoją kreatywność', 'SCALE', 15, 1, true, null, null, null, 5, null, null),

-- Testy bez grupy
(24, 19, 'Co wiesz o naszej firmie?', 'TEXT', 10, 1, true, null, null, null, null, null, null),
(25, 20, 'Test IQ: Znajdź prawidłowość', 'ABCDEF', 15, 1, true, null, null, null, null, null, 'E'),
(26, 21, 'Opisz swój największy projekt', 'TEXT', 10, 1, true, null, null, null, null, null, null),
(27, 22, 'Jak pracujesz pod presją czasu?', 'SCALE', 10, 1, true, null, null, null, 4, null, null),
(28, 23, 'Rozwiąż zadanie logiczne...', 'TEXT', 20, 1, true, 'Odpowiedź A', null, null, null, null, null),
(29, 24, 'Oceń swoje umiejętności komunikacyjne', 'SCALE', 15, 1, true, null, null, null, 4, null, null),

-- Testy grupy pustej
(30, 25, 'Jakie masz doświadczenie w zarządzaniu?', 'TEXT', 10, 1, true, null, null, null, null, null, null),
(31, 26, 'Test IQ: Wybierz następny element', 'ABCDEF', 15, 1, true, null, null, null, null, null, 'D'),
(32, 27, 'Opisz swój styl pracy', 'TEXT', 10, 1, true, null, null, null, null, null, null),
(33, 28, 'Jak radzisz sobie z konfliktami?', 'SCALE', 10, 1, true, null, null, null, 4, null, null),
(34, 29, 'Rozwiąż problem logiczny...', 'TEXT', 20, 1, true, 'Odpowiedź B', null, null, null, null, null),
(35, 30, 'Oceń swoją elastyczność', 'SCALE', 15, 1, true, null, null, null, 4, null, null);

-- 6. Powiązania testów z grupami
INSERT INTO link_groups_tests (group_id, test_id) VALUES
-- Przypisanie testów do Grupy Sebastian
(2, 1), (2, 2), (2, 3), (2, 4), (2, 5), (2, 6),

-- Przypisanie testów do Grupy Maciej
(4, 7), (4, 8), (4, 9), (4, 10), (4, 11), (4, 12),

-- Przypisanie testów do grupy wspólnej (Sebastian i Maciej)
(3, 13), (3, 14), (3, 15), (3, 16), (3, 17), (3, 18),

-- Przypisanie testów do pustej grupy
(1, 25), (1, 26), (1, 27), (1, 28), (1, 29), (1, 30);

-- 7. Kampanie (zależne od tests)
INSERT INTO campaigns (
    id, code, title, workplace_location, contract_type, employment_type,
    work_start_date, duties, requirements, employer_offerings, job_description,
    salary_range_min, salary_range_max, po1_test_id, po2_test_id, po3_test_id,
    po1_test_weight, po2_test_weight, po3_test_weight, universal_access_token
) VALUES
(1, 'KAM_SEB_2024', 'Kampania Grupa Sebastian', 'Warszawa', 'Umowa o pracę', 'Pełny etat',
    '2024-06-01', 'Prowadzenie terapii logopedycznej', 'Wykształcenie kierunkowe', 
    'Konkurencyjne wynagrodzenie', 'Poszukujemy doświadczonego logopedy',
    5000, 7000, 1, 3, 5,
    30, 30, 40, 'univ_token_KAM_SEB_2024'),                          -- Testy tylko z grupy Sebastian

(2, 'KAM_MAC_2024', 'Kampania Grupa Maciej', 'Kraków', 'B2B', 'Pełny etat',
    '2024-07-01', 'Wsparcie psychologiczne', 'Doświadczenie w terapii', 
    'Elastyczne godziny pracy', 'Zatrudnimy psychologa',
    6000, 9000, 7, 9, 11,
    30, 30, 40, 'univ_token_KAM_MAC_2024'),                         -- Testy tylko z grupy Maciej

(3, 'KAM_OBA_2024', 'Kampania Obu Grup', 'Gdańsk', 'B2B', 'Pełny etat',
    '2024-08-01', 'Rozwój oprogramowania', 'JavaScript, Python', 
    'Praca zdalna', 'Poszukujemy programisty',
    10000, 15000, 13, 15, 17,
    30, 30, 40, 'univ_token_KAM_OBA_2024'),                     -- Testy wspólne dla obu grup

(4, 'KAM_BEZ_2024', 'Kampania Bez Grupy', 'Poznań', 'Umowa o pracę', 'Pełny etat',
    '2024-09-01', 'Administracja biura', 'Doświadczenie w administracji', 
    'Przyjazna atmosfera', 'Szukamy administratora',
    4000, 6000, 19, 21, 23,
    30, 30, 40, 'univ_token_KAM_BEZ_2024'),                       -- Testy bez przypisanej grupy

(5, 'KAM_PUS_2024', 'Kampania Grupa Pusta', 'Wrocław', 'Umowa o pracę', 'Pełny etat',
    '2024-10-01', 'Rekrutacja pracowników', 'Doświadczenie w HR', 
    'Szkolenia', 'Rekruter',
    7000, 9000, 25, 27, 29,
    30, 30, 40, 'univ_token_KAM_PUS_2024');                       -- Testy z pustej grupy

-- 8. Powiązania kampanii z grupami
INSERT INTO link_groups_campaigns (group_id, campaign_id) VALUES
(2, 1),        -- Kampania Grupa Sebastian -> Grupa Sebastian
(4, 2),        -- Kampania Grupa Maciej -> Grupa Maciej
(2, 3),        -- Kampania Obu Grup -> Grupa Sebastian
(4, 3),        -- Kampania Obu Grup -> Grupa Maciej
(1, 5);        -- Kampania Grupa Pusta -> Grupa Pusta
-- Kampania 4 (Bez Grupy) nie jest przypisana do żadnej grupy

-- 9. Kandydaci (zależni od campaigns)
INSERT INTO candidates (
    id, campaign_id, first_name, last_name, email, phone, 
    recruitment_status, po1_score, po2_score, po3_score, po4_score, total_score,
    po1_completed_at, po2_completed_at, po3_completed_at,
    access_token_po2, access_token_po3,
    access_token_po2_is_used, access_token_po3_is_used,
    access_token_po2_expires_at, access_token_po3_expires_at,
    created_at, updated_at
) VALUES
-- Kandydat dla Kampanii Sebastian (wszystkie etapy)
(1, 1, 'Anna', 'Nowak', 'anna.nowak@example.com', '+48123456789', 
    'PO3', 85, 78, 92, null, 255,
    '2024-01-15 10:00:00', '2024-01-16 14:30:00', '2024-01-17 11:15:00',
    'token_po2_anna', 'token_po3_anna', 
    true, true,
    '2024-02-15 10:00:00', '2024-03-15 10:00:00',
    '2024-01-15 10:00:00', '2024-01-17 11:15:00'),

-- Kandydat dla Kampanii Maciej (etap PO2)
(2, 2, 'Jan', 'Kowalski', 'jan.kowalski@example.com', '+48987654321', 
    'PO2', 90, 85, null, null, 175,
    '2024-01-16 09:00:00', '2024-01-17 13:45:00', null,
    'token_po2_jan', 'token_po3_jan', 
    true, false,
    '2024-02-16 09:00:00', '2024-03-16 09:00:00',
    '2024-01-16 09:00:00', '2024-01-17 13:45:00'),

-- Kandydat dla Kampanii Obu Grup (etap PO1)
(3, 3, 'Maria', 'Wiśniewska', 'maria.wisniewska@example.com', '+48111222333', 
    'PO1', 75, null, null, null, 75,
    '2024-01-17 11:30:00', null, null,
    'token_po2_maria', null, 
    false, false,
    '2024-02-17 11:30:00', null,
    '2024-01-17 11:30:00', '2024-01-17 11:30:00'),

-- Kandydat REJECTED na etapie PO2
(4, 1, 'Tomasz', 'Rejected', 'tomasz.rejected@example.com', '+48333444555',
    'REJECTED', 75, 45, null, null, 120,
    '2024-01-18 10:00:00', '2024-01-19 14:30:00', null,
    'token_po2_tomasz', null,
    true, false,
    '2024-02-18 10:00:00', null,
    '2024-01-18 10:00:00', '2024-01-19 14:30:00'),

-- Kandydat ACCEPTED po wszystkich etapach
(5, 1, 'Alicja', 'Accepted', 'alicja.accepted@example.com', '+48444555666',
    'ACCEPTED', 90, 85, 95, 90, 360,
    '2024-01-18 11:00:00', '2024-01-19 15:30:00', '2024-01-20 12:00:00',
    'token_po2_alicja', 'token_po3_alicja',
    true, true,
    '2024-02-18 11:00:00', '2024-03-18 11:00:00',
    '2024-01-18 11:00:00', '2024-01-20 12:00:00'),

-- Kandydat na etapie PO4
(6, 2, 'Piotr', 'Final', 'piotr.final@example.com', '+48555666777',
    'PO4', 85, 80, 90, null, 255,
    '2024-01-18 12:00:00', '2024-01-19 16:30:00', '2024-01-20 13:00:00',
    'token_po2_piotr', 'token_po3_piotr',
    true, true,
    '2024-02-18 12:00:00', '2024-03-18 12:00:00',
    '2024-01-18 12:00:00', '2024-01-20 13:00:00'),

-- Kandydat dla kampanii bez grupy
(7, 4, 'Adam', 'Bezgrupowy', 'adam.bezgrupowy@example.com', '+48666777888',
    'PO1', 70, null, null, null, 70,
    '2024-01-19 10:00:00', null, null,
    'token_po2_adam', null,
    false, false,
    '2024-02-19 10:00:00', null,
    '2024-01-19 10:00:00', '2024-01-19 10:00:00'),

-- Kandydat dla kampanii z pustej grupy
(8, 5, 'Ewa', 'Pusta', 'ewa.pusta@example.com', '+48777888999',
    'PO2', 80, 75, null, null, 155,
    '2024-01-19 11:00:00', '2024-01-20 15:30:00', null,
    'token_po2_ewa', 'token_po3_ewa',
    true, false,
    '2024-02-19 11:00:00', '2024-03-19 11:00:00',
    '2024-01-19 11:00:00', '2024-01-20 15:30:00');

-- 10. Odpowiedzi kandydatów (zależne od candidates i questions)
INSERT INTO candidate_answers (
    candidate_id, question_id, text_answer, boolean_answer, numeric_answer,
    scale_answer, date_answer, abcdef_answer, score, score_ai
) VALUES
-- Odpowiedzi Anny na Test 1 (wszystkie typy odpowiedzi)
(1, 1, '5 lat doświadczenia jako logopeda', null, null, null, null, null, 10, 9),
(1, 2, null, true, null, null, null, null, 5, 5),
(1, 3, null, null, null, 4, null, null, 15, 15),
(1, 4, null, null, 6000, null, null, null, 0, 0),
(1, 5, null, null, null, null, '2024-04-01', null, 0, 0),
(1, 6, null, null, null, null, null, 'A', 5, 5),

-- Odpowiedzi Jana na Test 7 (PO1 Grupa Maciej)
(2, 7, 'Empatia, komunikatywność, cierpliwość', null, null, null, null, null, 9, 8),
(2, 8, null, null, null, null, null, 'C', 15, 15),

-- Odpowiedzi Marii na Test 13 (PO1 Grupy Sebastian+Maciej)
(3, 13, 'Rozwój w obszarze programowania, awans na senior developera', null, null, null, null, null, 8, 7),
(3, 14, null, null, null, null, null, 'B', 15, 15),

-- Odpowiedzi odrzuconego kandydata
(4, 1, '2 lata doświadczenia jako stażysta', null, null, null, null, null, 5, 4),
(4, 2, null, false, null, null, null, null, 0, 0),

-- Odpowiedzi zaakceptowanego kandydata
(5, 1, '8 lat doświadczenia jako senior', null, null, null, null, null, 10, 10),
(5, 2, null, true, null, null, null, null, 5, 5),

-- Odpowiedzi kandydata na PO4
(6, 7, 'Doskonała organizacja, zarządzanie zespołem', null, null, null, null, null, 10, 9),
(6, 8, null, null, null, null, null, 'C', 15, 15),

-- Odpowiedzi Adama na test bez grupy
(7, 24, 'Firma zajmuje się rozwojem oprogramowania', null, null, null, null, null, 8, 7),
(7, 25, null, null, null, null, null, 'E', 15, 15),

-- Odpowiedzi Ewy na test z pustej grupy
(8, 30, 'Zarządzanie zespołem 10-osobowym', null, null, null, null, null, 9, 8),
(8, 31, null, null, null, null, null, 'D', 15, 15);
