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
INSERT INTO tests (id, title, test_type, description, passing_threshold, time_limit_minutes, created_at, updated_at) VALUES
-- Testy dla Grupy Sebastian (grupa 2)
(1, 'Ankieta wstępna PO1', 'SURVEY', 'Test PO1 Grupa Sebastian - Ankieta', 70, 30, now(), now()),
(2, 'Test IQ - Etap PO1', 'IQ', 'Test PO1 Grupa Sebastian - IQ', 75, 45, now(), now()),
(3, 'Ankieta pogłębiona PO2', 'SURVEY', 'Test PO2 Grupa Sebastian - Ankieta', 70, 30, now(), now()),
(4, 'Test Belbin Team Roles', 'EQ', 'Test PO2 Grupa Sebastian - EQ', 80, 60, now(), now()),
(5, 'Test IQ zaawansowany PO3', 'IQ', 'Test PO3 Grupa Sebastian - IQ', 85, 45, now(), now()), 

-- Testy dla Grupy Maciej (grupa 4)
(7, 'Ankieta kwalifikacyjna PO1', 'SURVEY', 'Test PO1 Grupa Maciej - Ankieta', 70, 30, now(), now()),
(8, 'Test IQ podstawowy PO1', 'IQ', 'Test PO1 Grupa Maciej - IQ', 75, 45, now(), now()),
(9, 'Ankieta kompetencyjna PO2', 'SURVEY', 'Test PO2 Grupa Maciej - Ankieta', 70, 30, now(), now()),
(10, 'Test Belbin Team Roles', 'EQ', 'Test PO2 Grupa Maciej - EQ', 80, 60, now(), now()),
(11, 'Test IQ rozszerzony PO3', 'IQ', 'Test PO3 Grupa Maciej - IQ', 85, 45, now(), now()), 

-- Testy dla obu grup (Sebastian + Maciej)
(13, 'Ankieta wspólna PO1', 'SURVEY', 'Test PO1 Grupy Sebastian+Maciej - Ankieta', 70, 30, now(), now()),
(14, 'Test IQ wspólny PO1', 'IQ', 'Test PO1 Grupy Sebastian+Maciej - IQ', 75, 45, now(), now()),
(15, 'Ankieta wspólna PO2', 'SURVEY', 'Test PO2 Grupy Sebastian+Maciej - Ankieta', 70, 30, now(), now()), 
(17, 'Test IQ wspólny PO3', 'IQ', 'Test PO3 Grupy Sebastian+Maciej - IQ', 85, 45, now(), now()),
(18, 'Test EQ wspólny PO3', 'EQ', 'Test PO3 Grupy Sebastian+Maciej - EQ', 75, 60, now(), now()),

-- Testy bez przypisanej grupy
(19, 'Ankieta ogólna PO1', 'SURVEY', 'Test PO1 Bez Grupy - Ankieta', 70, 30, now(), now()),
(20, 'Test IQ ogólny PO1', 'IQ', 'Test PO1 Bez Grupy - IQ', 75, 45, now(), now()),
(21, 'Ankieta ogólna PO2', 'SURVEY', 'Test PO2 Bez Grupy - Ankieta', 70, 30, now(), now()), 
(23, 'Test IQ ogólny PO3', 'IQ', 'Test PO3 Bez Grupy - IQ', 85, 45, now(), now()), 

-- Testy dla pustej grupy
(25, 'Ankieta standardowa PO1', 'SURVEY', 'Test PO1 Grupa Pusta - Ankieta', 70, 30, now(), now()),
(26, 'Test IQ standardowy PO1', 'IQ', 'Test PO1 Grupa Pusta - IQ', 75, 45, now(), now()),
(27, 'Ankieta standardowa PO2', 'SURVEY', 'Test PO2 Grupa Pusta - Ankieta', 70, 30, now(), now()), 
(29, 'Test IQ standardowy PO3', 'IQ', 'Test PO3 Grupa Pusta - IQ', 85, 45, now(), now());

-- 5. Pytania (zależne od tests)
INSERT INTO questions (
    id,  
    test_id, question_text, answer_type, options,
    points, order_number, 
    is_required, correct_answer_text, correct_answer_boolean, 
    correct_answer_salary, correct_answer_scale, correct_answer_date, 
    correct_answer_abcdef
) VALUES
-- Test 1 (PO1 Grupa Sebastian - Ankieta) - wszystkie typy pytań
(1, 1, 'Opisz swoje doświadczenie zawodowe', 'TEXT', null, 10, 1, true, 'Minimum 2 lata doświadczenia w zawodzie', null, null, null, null, null),
(2, 1, 'Czy posiadasz prawo jazdy?', 'BOOLEAN', null, 5, 2, true, null, true, null, null, null, null),
(3, 1, 'Oceń swoją znajomość języka angielskiego', 'SCALE', null, 15, 3, true, null, null, null, 4, null, null),
(4, 1, 'Jakie są twoje oczekiwania finansowe?', 'SALARY', null, 0, 4, true, null, null, 5000, null, null, null),
(5, 1, 'Od kiedy możesz rozpocząć pracę?', 'DATE', null, 0, 5, true, null, null, null, null, '2024-03-01', null),
(6, 1, 'Wybierz preferowany typ umowy: A) UoP, B) B2B, C) UZ, D) UoD', 'ABCDEF', null, 5, 6, true, null, null, null, null, null, 'A'),

-- Pozostałe testy Grupy Sebastian
(7, 2, 'Test IQ: Rozwiąż ciąg: 2,4,6,8,...', 'TEXT', null, 10, 1, true, '10', null, null, null, null, null),
(8, 3, 'Opisz swoje największe osiągnięcie zawodowe', 'TEXT', null, 15, 1, true, null, null, null, null, null, null),
(9, 4, 'Oceń swoją odporność na stres', 'SCALE', null, 10, 1, true, null, null, null, 4, null, null),
(10, 5, 'Rozwiąż zadanie logiczne...', 'TEXT', null, 20, 1, true, 'Odpowiedź C', null, null, null, null, null),

-- Testy Grupy Maciej
(12, 7, 'Jakie są twoje mocne strony?', 'TEXT', null, 10, 1, true, null, null, null, null, null, null),
(13, 8, 'Test IQ: Znajdź brakujący element', 'ABCDEF', null, 15, 1, true, null, null, null, null, null, 'C'),
(14, 9, 'Opisz swoją idealną kulturę organizacyjną', 'TEXT', null, 10, 1, true, null, null, null, null, null, null),
(15, 10, 'Jak radzisz sobie z krytyką?', 'SCALE', null, 10, 1, true, null, null, null, 3, null, null),
(16, 11, 'Rozwiąż zagadkę logiczną...', 'TEXT', null, 20, 1, true, 'Odpowiedź D', null, null, null, null, null),

-- Testy dla obu grup
(18, 13, 'Jakie są twoje cele zawodowe?', 'TEXT', null, 10, 1, true, null, null, null, null, null, null),
(19, 14, 'Test IQ: Uzupełnij analogię', 'ABCDEF', null, 15, 1, true, null, null, null, null, null, 'B'),
(20, 15, 'Opisz trudną sytuację zawodową', 'TEXT', null, 10, 1, true, null, null, null, null, null, null),
(22, 17, 'Rozwiąż problem matematyczny...', 'TEXT', null, 20, 1, true, '42', null, null, null, null, null),

-- Testy bez grupy
(24, 19, 'Co wiesz o naszej firmie?', 'TEXT', null, 10, 1, true, null, null, null, null, null, null),
(25, 20, 'Test IQ: Znajdź prawidłowość', 'ABCDEF', null, 15, 1, true, null, null, null, null, null, 'E'),
(26, 21, 'Opisz swój największy projekt', 'TEXT', null, 10, 1, true, null, null, null, null, null, null),
(28, 23, 'Rozwiąż zadanie logiczne...', 'TEXT', null, 20, 1, true, 'Odpowiedź A', null, null, null, null, null),

-- Testy grupy pustej
(30, 25, 'Jakie masz doświadczenie w zarządzaniu?', 'TEXT', null, 10, 1, true, null, null, null, null, null, null),
(31, 26, 'Test IQ: Wybierz następny element', 'ABCDEF', null, 15, 1, true, null, null, null, null, null, 'D'),
(32, 27, 'Opisz swój styl pracy', 'TEXT', null, 10, 1, true, null, null, null, null, null, null),
(34, 29, 'Rozwiąż problem logiczny...', 'TEXT', null, 20, 1, true, 'Odpowiedź B', null, null, null, null, null),

-- Test EQ
(36, 18, 'I. Oto co mogę wnieść w pracę zespołu:', 'AH_POINTS',
    '{"a": "Mam umiejętności szybkiego dostrzegania i wykorzystywania nadarzających się okazji.",
      "b": "Potrafię pracować z bardzo różnymi ludźmi",
      "c": "Bardzo łatwo przychodzi mi wymyślanie nowych rozwiązań",
      "d": "Potrafię umiejętnie zachęcać ludzi do aktywnego udziału kiedy widzę, że mogą wnieść coś wartościowego do pracy zespołu",
      "e": "Potrafię doprowadzić realizację zadania do końca",
      "f": "Potrafię znieść chwilową krytykę, jeśli ostatecznie prowadzi to do osiągnięcia celu",
      "g": "Jestem w stanie błyskawicznie ocenić jakie działanie będzie skuteczne w sytuacji, z którą zetknąłem się już w przeszłości",
      "h": "Potrafię podać rozsądne i obiektywne uzasadnienie różnych kierunków działania"}',
    0, 1, true, null, null, null, null, null, null),

(37, 18, 'II. Moje problemy w pracy zespołu, to przede wszystkim:', 'AH_POINTS',
    '{"a": "Jestem niespokojny, jeśli spotkanie nie jest właściwie zorganizowane, kontrolowane i prowadzone",
      "b": "Poświęcam zbyt wiele uwagi opiniom, które mimo iż są interesujące nie zostały do końca przedyskutowane",
      "c": "Często mówię zbyt dużo, gdy grupa rozważa nowe propozycje",
      "d": "Moje obiektywne spojrzenie sprawia, iż trudno jest mi spontanicznie i entuzjastycznie przyłączyć się do grupy",
      "e": "Kiedy dążę do realizacji zadania jestem czasami oceniany jako bezwzględny i autokratyczny",
      "f": "Trudno mi kierować zespołem \"twardą ręką\", prawdopodobnie dlatego, że jestem wyczulony na atmosferę panującą w grupie",
      "g": "Często zbytnio koncentruje się na nowych pomysłach tracę kontrolę nad rozwojem sytuacji",
      "h": "Moi koledzy uważają, że często przejmuje się drobiazgami i martwię się na zapas"}',
    0, 2, true, null, null, null, null, null, null),

(38, 18, 'III. W trakcie pracy w zespole:', 'AH_POINTS',
    '{"a": "Mam umiejętność przekonywania ludzi bez wywierania presji",
      "b": "Moja czujność pozwala uniknąć pomyłek i przeoczeń",
      "c": "Jestem gotów wywrzeć nacisk na zebranych kiedy widzę, że marnujemy czas lub tracimy z pola widzenia zasadnicze kwestie",
      "d": "Można być pewnym, że zaproponuję coś oryginalnego",
      "e": "Zawsze jestem gotów poprzeć wartościową sugestię jeśli służy to wspólnemu interesowi",
      "f": "Chętnie poszukuję nowych pomysłów i rozwiązań",
      "g": "Wierzę, że wysoko oceniana jest moja umiejętność chłodnej oceny",
      "h": "Potrafię dopilnować tego, aby wszystkie najważniejsze działania były właściwie zorganizowane"}',
    0, 3, true, null, null, null, null, null, null),

(39, 18, 'IV. Charakterystyczną cechą mojej pracy w zespole jest to, że:', 'AH_POINTS',
    '{"a": "Jestem zainteresowany bliższym poznaniem kolegów",
      "b": "Nie waham się krytykować opinii innych i wyrażać sądów nie podzielanych przez większość",
      "c": "Zwykle potrafię znaleźć argumenty przeciwko nierozsądnym propozycjom",
      "d": "Sądzę, że mam umiejętność wprowadzania przyjętych planów w życie",
      "e": "Często odrzucam to, co oczywiste i proponuję zaskakujące rozwiązania",
      "f": "Wprowadzam perfekcjonizm do każdej pracy zespołowej",
      "g": "Potrafię wykorzystać kontakty poza grupą",
      "h": "Chociaż pragnę poznać wszystkie opinie, w momencie podejmowania decyzji polegam głównie na własnym zdaniu"}',
    0, 4, true, null, null, null, null, null, null),

(40, 18, 'V. Czerpię satysfakcję z pracy w zespole, ponieważ:', 'AH_POINTS',
    '{"a": "Lubię analizować sytuacje i rozważać możliwe rozwiązania",
      "b": "Interesuje mnie wypracowywanie praktycznych rozwiązań",
      "c": "Lubię mieć świadomość, że mam wpływ na dobre stosunki w grupie",
      "d": "Wywieram znaczny wpływ na podejmowane decyzje",
      "e": "Spotykam ludzi, którzy mają coś nowego do zaoferowania",
      "f": "Potrafię przekonać ludzi do przyjęcia danego kierunku działań",
      "g": "Czuję się znakomicie, kiedy mogę jednemu zadaniu poświęcić całkowitą uwagę",
      "h": "Lubię dziedziny, które pobudzają moją wyobraźnię"}',
    0, 5, true, null, null, null, null, null, null),

(41, 18, 'VI. Gdybym nagle otrzymał do wykonania zadanie w znacznie ograniczonym czasie i we współpracy z nieznanymi ludźmi:', 'AH_POINTS',
    '{"a": "Zanim przystąpilibyśmy do wspólnej pracy miałbym ochotę wycofać się w cień, aby znaleźć optymalny sposób działania",
      "b": "Chętnie pracowałbym z kimś, kto wykazywałby pozytywne nastawienie, nawet gdyby był trudny we współpracy",
      "c": "Znalazłbym sposób łatwiejszej realizacji zadania poprzez ustalenie jaki optymalny wkład mogą wnieść poszczególni członkowie zespołu",
      "d": "Moje poczucie obowiązku pomogłoby dotrzymać wyznaczone terminy",
      "e": "Wierzę, że zachowałbym zimną krew i zdolność jasnego myślenia",
      "f": "Konsekwentnie realizowałbym zadanie pomimo odczuwanej presji",
      "g": "Byłbym gotów przejąć kierownictwo gdybym dostrzegł, że grupa stoi w miejscu",
      "h": "Rozpocząłbym dyskusję, aby wprowadzić nowe pomysły i ruszyć do przodu"}',
    0, 6, true, null, null, null, null, null, null),

(42, 18, 'VII. Problemy jakie mogę mieć w pracy w grupie, to przede wszystkim to, że:', 'AH_POINTS',
    '{"a": "Okazuję zniecierpliwienie w stosunku do tych, którzy opóźniają pracę",
      "b": "Można mi zarzucić, że myślę w sposób zbyt analityczny i rzadko kieruję się intuicją",
      "c": "Moje pragnienie, aby zadanie zostało wykonane jak najlepiej może zwalniać tempo pracy",
      "d": "Szybko się nudzę i liczę na to, że bardziej dynamiczni członkowie grupy pobudzą mnie do działania",
      "e": "Trudno mi rozpocząć pracę dopóki cele nie są całkowicie jasne",
      "f": "Czasami mam trudności z wyjaśnianiem skomplikowanych kwestii",
      "g": "Zdaję sobie sprawę, że wymagam od innych tego, czego sam nie potrafię zrobić",
      "h": "Waham się przedstawić moje poglądy w sytuacji, gdy inni mają odmienne zdanie"}',
    0, 7, true, null, null, null, null, null, null);


-- 6. Powiązania testów z grupami
INSERT INTO link_groups_tests (group_id, test_id) VALUES
-- Przypisanie testów do Grupy Sebastian
(2, 1), (2, 2), (2, 3), (2, 4), (2, 5),

-- Przypisanie testów do Grupy Maciej
(4, 7), (4, 8), (4, 9), (4, 10), (4, 11),

-- Przypisanie testów do grupy wspólnej (Sebastian i Maciej)
(3, 13), (3, 14), (3, 15), (3, 17), (3, 18),

-- Przypisanie testów do pustej grupy
(1, 25), (1, 26), (1, 27), (1, 29);

-- 7. Kampanie (zależne od tests)
INSERT INTO campaigns (
    id, code, title, workplace_location, contract_type, employment_type,
    work_start_date, duties, requirements, employer_offerings, job_description,
    salary_range_min, salary_range_max, po1_test_id, po2_test_id, po3_test_id,
    po1_test_weight, po2_test_weight, po3_test_weight, universal_access_token,
    is_active, created_at, updated_at
) VALUES
(1, 'KAM_SEB_2024', 'Kampania Grupa Sebastian', 'Warszawa', 'Umowa o pracę', 'Pełny etat',
    '2024-06-01', 'Prowadzenie terapii logopedycznej', 'Wykształcenie kierunkowe', 
    'Konkurencyjne wynagrodzenie', 'Poszukujemy doświadczonego logopedy',
    5000, 7000, 1, 3, 5,
    30, 30, 40, 'univ_token_KAM_SEB_2024', true, now(), now()),

(2, 'KAM_MAC_2024', 'Kampania Grupa Maciej', 'Kraków', 'B2B', 'Pełny etat',
    '2024-07-01', 'Wsparcie psychologiczne', 'Doświadczenie w terapii', 
    'Elastyczne godziny pracy', 'Zatrudnimy psychologa',
    6000, 9000, 7, 9, 11,
    30, 30, 40, 'univ_token_KAM_MAC_2024', true, now(), now()),

(3, 'KAM_OBA_2024', 'Kampania Obu Grup', 'Gdańsk', 'B2B', 'Pełny etat',
    '2024-08-01', 'Rozwój oprogramowania', 'JavaScript, Python', 
    'Praca zdalna', 'Poszukujemy programisty',
    10000, 15000, 13, 15, 17,
    30, 30, 40, 'univ_token_KAM_OBA_2024', true, now(), now()),

(4, 'KAM_BEZ_2024', 'Kampania Bez Grupy', 'Poznań', 'Umowa o pracę', 'Pełny etat',
    '2024-09-01', 'Administracja biura', 'Doświadczenie w administracji', 
    'Przyjazna atmosfera', 'Szukamy administratora',
    4000, 6000, 19, 21, 23,
    30, 30, 40, 'univ_token_KAM_BEZ_2024', true, now(), now()),

(5, 'KAM_PUS_2024', 'Kampania Grupa Pusta', 'Wrocław', 'Umowa o pracę', 'Pełny etat',
    '2024-10-01', 'Rekrutacja pracowników', 'Doświadczenie w HR', 
    'Szkolenia', 'Rekruter',
    7000, 9000, 25, 27, 29,
    30, 30, 40, 'univ_token_KAM_PUS_2024', true, now(), now());

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
    score_ko, score_re, score_w, score_in, score_pz, score_kz, score_dz, score_sw,
    created_at, updated_at
) VALUES
-- Kandydat dla Kampanii Sebastian (wszystkie etapy)
(1, 1, 'Anna', 'Nowak', 'anna.nowak@example.com', '+48123456789', 
    'PO3', 85, 78, 92, null, 255,
    '2024-01-15 10:00:00', '2024-01-16 14:30:00', '2024-01-17 11:15:00',
    'token_po2_anna', 'token_po3_anna', 
    true, true,
    '2024-02-15 10:00:00', '2024-03-15 10:00:00',
    null, null, null, null, null, null, null, null,
    '2024-01-15 10:00:00', '2024-01-17 11:15:00'),

-- Kandydat dla Kampanii Maciej (etap PO2)
(2, 2, 'Jan', 'Kowalski', 'jan.kowalski@example.com', '+48987654321', 
    'PO2', 90, 85, null, null, 175,
    '2024-01-16 09:00:00', '2024-01-17 13:45:00', null,
    'token_po2_jan', 'token_po3_jan', 
    true, false,
    '2024-02-16 09:00:00', '2024-03-16 09:00:00',
    null, null, null, null, null, null, null, null,
    '2024-01-16 09:00:00', '2024-01-17 13:45:00'),

-- Kandydat dla Kampanii Obu Grup (etap PO1)
(3, 3, 'Maria', 'Wiśniewska', 'maria.wisniewska@example.com', '+48111222333', 
    'PO1', 75, null, null, null, 75,
    '2024-01-17 11:30:00', null, null,
    'token_po2_maria', null, 
    false, false,
    '2024-02-17 11:30:00', null,
    null, null, null, null, null, null, null, null,
    '2024-01-17 11:30:00', '2024-01-17 11:30:00'),

-- Kandydat REJECTED na etapie PO2
(4, 1, 'Tomasz', 'Rejected', 'tomasz.rejected@example.com', '+48333444555',
    'REJECTED', 75, 45, null, null, 120,
    '2024-01-18 10:00:00', '2024-01-19 14:30:00', null,
    'token_po2_tomasz', null,
    true, false,
    '2024-02-18 10:00:00', null,
    null, null, null, null, null, null, null, null,
    '2024-01-18 10:00:00', '2024-01-19 14:30:00'),

-- Kandydat ACCEPTED po wszystkich etapach
(5, 1, 'Alicja', 'Accepted', 'alicja.accepted@example.com', '+48444555666',
    'ACCEPTED', 90, 85, 95, 90, 360,
    '2024-01-18 11:00:00', '2024-01-19 15:30:00', '2024-01-20 12:00:00',
    'token_po2_alicja', 'token_po3_alicja',
    true, true,
    '2024-02-18 11:00:00', '2024-03-18 11:00:00',
    null, null, null, null, null, null, null, null,
    '2024-01-18 11:00:00', '2024-01-20 12:00:00'),

-- Kandydat na etapie PO4
(6, 2, 'Piotr', 'Final', 'piotr.final@example.com', '+48555666777',
    'PO4', 85, 80, 90, null, 255,
    '2024-01-18 12:00:00', '2024-01-19 16:30:00', '2024-01-20 13:00:00',
    'token_po2_piotr', 'token_po3_piotr',
    true, true,
    '2024-02-18 12:00:00', '2024-03-18 12:00:00',
    null, null, null, null, null, null, null, null,
    '2024-01-18 12:00:00', '2024-01-20 13:00:00'),

-- Kandydat dla kampanii bez grupy
(7, 4, 'Adam', 'Bezgrupowy', 'adam.bezgrupowy@example.com', '+48666777888',
    'PO1', 70, null, null, null, 70,
    '2024-01-19 10:00:00', null, null,
    'token_po2_adam', null,
    false, false,
    '2024-02-19 10:00:00', null,
    null, null, null, null, null, null, null, null,
    '2024-01-19 10:00:00', '2024-01-19 10:00:00'),

-- Kandydat dla kampanii z pustej grupy
(8, 5, 'Ewa', 'Pusta', 'ewa.pusta@example.com', '+48777888999',
    'PO2', 80, 75, null, null, 155,
    '2024-01-19 11:00:00', '2024-01-20 15:30:00', null,
    'token_po2_ewa', 'token_po3_ewa',
    true, false,
    '2024-02-19 11:00:00', '2024-03-19 11:00:00',
    null, null, null, null, null, null, null, null,
    '2024-01-19 11:00:00', '2024-01-20 15:30:00');

-- 10. Odpowiedzi kandydatów (zależne od candidates i questions)
INSERT INTO candidate_answers (
    id, candidate_id, question_id, 
    text_answer, boolean_answer, salary_answer,
    scale_answer, date_answer, abcdef_answer, 
    points_per_option,
    score, score_ai,
    created_at
) VALUES
(1, 1, 1, '5 lat doświadczenia jako logopeda', null, null, null, null, null, 
    null, 10, 9, now()),
(2, 1, 36, null, null, null, null, null, null,
    '{"a": 3, "b": 2, "c": 1, "d": 0, "e": 2, "f": 1, "g": 0, "h": 3}',
    10, 9, now()),
(3, 1, 2, null, true, null, null, null, null, 
    null, 5, 5, now()),
(4, 1, 3, null, null, null, 4, null, null, 
    null, 15, 15, now()),
(5, 1, 4, null, null, 6000, null, null, null, 
    null, 0, 0, now()),
(6, 1, 5, null, null, null, null, '2024-04-01', null, 
    null, 5, 5, now()),
(7, 2, 7, 'Empatia, komunikatywność, cierpliwość', null, null, null, null, null, 
    null, 9, 8, now()),
(8, 2, 8, null, null, null, null, null, 'C', 
    null, 15, 15, now()),
(9, 3, 13, 'Rozwój w obszarze programowania, awans na senior developera', null, null, null, null, null, 
    null, 8, 7, now()),
(10, 3, 14, null, null, null, null, null, 'B', 
    null, 15, 15, now()),
(11, 4, 1, '2 lata doświadczenia jako stażysta', null, null, null, null, null, 
    null, 5, 4, now()),
(12, 4, 2, null, false, null, null, null, null, 
    null, 0, 0, now()),
(13, 5, 1, '8 lat doświadczenia jako senior', null, null, null, null, null, 
    null, 10, 10, now()),
(14, 5, 2, null, true, null, null, null, null, 
    null, 5, 5, now()),
(15, 6, 7, 'Doskonała organizacja, zarządzanie zespołem', null, null, null, null, null, 
    null, 10, 9, now()),
(16, 6, 8, null, null, null, null, null, 'C', 
    null, 15, 15, now()),
(17, 7, 24, 'Firma zajmuje się rozwojem oprogramowania', null, null, null, null, null, 
    null, 8, 7, now()),
(18, 7, 25, null, null, null, null, null, 'E', 
    null, 15, 15, now()),
(19, 8, 30, 'Zarządzanie zespołem 10-osobowym', null, null, null, null, null, 
    null, 9, 8, now()),
(20, 8, 31, null, null, null, null, null, 'D', 
    null, 15, 15, now());

 