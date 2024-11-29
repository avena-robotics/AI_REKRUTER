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
(1, 'Ankieta wstępna', 'SURVEY', 'Test Grupa Sebastian - Ankieta', 70, 30, now(), now()),
(2, 'Test IQ', 'IQ', 'Test Grupa Sebastian - IQ', 75, 45, now(), now()),
(3, 'Ankieta pogłębiona', 'SURVEY', 'Test Grupa Sebastian - Ankieta', 70, 30, now(), now()),
(4, 'Test IQ zaawansowany', 'IQ', 'Test Grupa Sebastian - IQ', 85, 45, now(), now()),

-- Testy dla Grupy Maciej (grupa 4)
(5, 'Ankieta kwalifikacyjna', 'SURVEY', 'Test Grupa Maciej - Ankieta', 70, 30, now(), now()),
(6, 'Test IQ podstawowy', 'IQ', 'Test Grupa Maciej - IQ', 75, 45, now(), now()),
(7, 'Ankieta kompetencyjna', 'SURVEY', 'Test Grupa Maciej - Ankieta', 70, 30, now(), now()),
(8, 'Test IQ rozszerzony', 'IQ', 'Test Grupa Maciej - IQ', 85, 45, now(), now()),

-- Testy dla obu grup (Sebastian + Maciej)
(9, 'Ankieta wspólna', 'SURVEY', 'Test Grupy Sebastian+Maciej - Ankieta', 70, 30, now(), now()),
(10, 'Test IQ wspólny', 'IQ', 'Test Grupy Sebastian+Maciej - IQ', 75, 45, now(), now()),
(11, 'Ankieta wspólna', 'SURVEY', 'Test Grupy Sebastian+Maciej - Ankieta', 70, 30, now(), now()),
(12, 'Test IQ wspólny', 'IQ', 'Test Grupy Sebastian+Maciej - IQ', 85, 45, now(), now()),
(13, 'Test EQ wspólny', 'EQ', 'Test Grupy Sebastian+Maciej - EQ', 75, 60, now(), now());

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

-- Test 2 (PO1 Grupa Sebastian - IQ)
(7, 2, 'Test IQ: Rozwiąż ciąg: 2,4,6,8,...', 'TEXT', null, 10, 1, true, '10', null, null, null, null, null),
(8, 2, 'Test IQ: Znajdź brakujący element w sekwencji', 'ABCDEF', null, 15, 2, true, null, null, null, null, null, 'C'),

-- Test 3 (PO2 Grupa Sebastian - Ankieta)
(9, 3, 'Opisz swoje największe osiągnięcie zawodowe', 'TEXT', null, 15, 1, true, null, null, null, null, null, null),
(10, 3, 'Jakie są twoje cele zawodowe?', 'TEXT', null, 10, 2, true, null, null, null, null, null, null),

-- Test 4 (PO3 Grupa Sebastian - IQ)
(11, 4, 'Rozwiąż zadanie logiczne...', 'TEXT', null, 20, 1, true, 'Odpowiedź C', null, null, null, null, null),
(12, 4, 'Wybierz prawidłową odpowiedź', 'ABCDEF', null, 15, 2, true, null, null, null, null, null, 'B'),

-- Test 13 (PO3 Grupy Sebastian+Maciej - EQ) - Test Belbina
(13, 13, 'I. Oto co mogę wnieść w pracę zespołu:', 'AH_POINTS', '{"a": "Potrafię szybko dostrzegać i wykorzystywać nowe możliwości", "b": "Potrafię dobrze współpracować z bardzo różnymi ludźmi", "c": "Generowanie pomysłów to mój naturalny talent", "d": "Potrafię wydobyć z ludzi wszystko, co mogą wnieść do realizacji celów grupowych", "e": "Moja zdolność doprowadzania spraw do końca w dużej mierze wynika z mojej efektywności osobistej", "f": "Jestem gotów stawić czoła czasowej niepopularności, jeśli prowadzi to do wartościowych wyników", "g": "Zwykle potrafię wyczuć, co jest realistyczne i może zadziałać", "h": "Potrafię przedstawić różne alternatywne działania i możliwości"}', 0, 1, true, null, null, null, null, null, null),

(14, 13, 'II. Moje słabości w pracy zespołowej:', 'AH_POINTS', '{"a": "Nie jestem spokojny, dopóki spotkania nie są dobrze ustrukturyzowane i kontrolowane", "b": "Mam skłonność do poświęcania zbyt dużej uwagi osobom, których punkt widzenia nie został właściwie uwzględniony", "c": "Mam tendencję do mówienia zbyt dużo, gdy grupa zajmuje się nowymi pomysłami", "d": "Mój obiektywny ogląd utrudnia mi łatwe i entuzjastyczne przyłączanie się do kolegów", "e": "Czasami jestem postrzegany jako wywierający zbyt silny nacisk i autorytatywny, gdy trzeba coś zrobić", "f": "Trudno mi przewodzić z pozycji lidera, być może dlatego, że jestem zbyt wrażliwy na atmosferę w grupie", "g": "Mam skłonność do zbytniego angażowania się w pomysły, które przychodzą mi do głowy, i tracenia orientacji w tym, co się dzieje", "h": "Moi koledzy mają tendencję do postrzegania mnie jako niepotrzebnie martwiącego się szczegółami i możliwością, że sprawy mogą pójść źle"}', 0, 2, true, null, null, null, null, null, null),

(15, 13, 'III. Kiedy angażuję się w projekt z innymi ludźmi:', 'AH_POINTS', '{"a": "Mam zdolność wpływania na ludzi bez wywierania na nich presji", "b": "Moja czujność pozwala zapobiegać wielu pomyłkom i błędom", "c": "Jestem gotów naciskać na działanie, aby upewnić się, że zebranie nie marnuje czasu ani nie traci z oczu głównego celu", "d": "Można na mnie polegać, jeśli chodzi o wnoszenie oryginalnych pomysłów", "e": "Zawsze jestem gotów poprzeć dobre sugestie służące wspólnym interesom", "f": "Lubię szukać najnowszych pomysłów i wydarzeń", "g": "Wierzę, że moja zdolność osądu może pomóc w podjęciu właściwych decyzji", "h": "Można na mnie polegać, jeśli chodzi o dopilnowanie, aby cała istotna praca została zorganizowana"}', 0, 3, true, null, null, null, null, null, null),

(16, 13, 'IV. Moje charakterystyczne podejście do pracy grupowej:', 'AH_POINTS', '{"a": "Mam spokojne zainteresowanie lepszym poznaniem kolegów", "b": "Nie waham się przeciwstawiać poglądom innych ani podtrzymywać swojego stanowiska, nawet wobec opozycji", "c": "Zwykle potrafię znaleźć argumenty na odrzucenie niesłusznych propozycji", "d": "Sądzę, że mam talent do wprowadzania rzeczy w życie, gdy trzeba realizować plan", "e": "Mam tendencję do unikania oczywistego i wychodzenia z czymś nieoczekiwanym", "f": "Wnoszę perfekcjonizm do każdego zespołowego zadania", "g": "Jestem gotów wykorzystywać kontakty poza grupą", "h": "Interesują mnie wszystkie punkty widzenia, ale nie waham się podjąć decyzji, gdy trzeba"}', 0, 4, true, null, null, null, null, null, null),

(17, 13, 'V. Czerpię satysfakcję z pracy, ponieważ:', 'AH_POINTS', '{"a": "Lubię analizować sytuacje i rozważać wszystkie możliwości", "b": "Interesuje mnie znajdowanie praktycznych rozwiązań problemów", "c": "Lubię czuć, że wspieram dobre relacje w pracy", "d": "Mogę mieć silny wpływ na decyzje", "e": "Mogę spotykać ludzi, którzy mają coś nowego do zaoferowania", "f": "Potrafię doprowadzać ludzi do zgody co do koniecznego trybu działania", "g": "Czuję się w swoim żywiole, gdy mogę poświęcić zadaniu pełną uwagę", "h": "Lubię znajdować obszary, które poszerzają moją wyobraźnię"}', 0, 5, true, null, null, null, null, null, null),

(18, 13, 'VI. Gdy otrzymuję trudne zadanie do wykonania w ograniczonym czasie:', 'AH_POINTS', '{"a": "Chciałbym się wycofać i opracować rozwiązanie, zanim rozwinę plan działania", "b": "Byłbym gotów pracować z osobą wykazującą najbardziej pozytywne podejście", "c": "Znalazłbym sposób na zmniejszenie złożoności zadania, ustalając, co mogą wnieść różne osoby", "d": "Moje naturalne poczucie pilności pomogłoby zapewnić, że nie przekroczymy harmonogramu", "e": "Wierzę, że zachowałbym spokój i zdolność do jasnego myślenia", "f": "Utrzymałbym stałość celu mimo presji", "g": "Byłbym gotów przejąć konstruktywne przywództwo, gdybym czuł, że grupa nie robi postępów", "h": "Otworzyłbym dyskusję, aby stymulować nowe myśli i uruchomić coś"}', 0, 6, true, null, null, null, null, null, null),

(19, 13, 'VII. Problemy, jakim podlegam, pracując w grupach:', 'AH_POINTS', '{"a": "Mam skłonność do okazywania niecierpliwości wobec tych, którzy hamują postęp", "b": "Inni mogą mnie krytykować za zbytnią analityczność i niewystarczającą intuicyjność", "c": "Moje dążenie do zapewnienia właściwego wykonania pracy może wstrzymywać postęp", "d": "Mam tendencję do znudzenia i liczenia na jedną lub dwie stymulujące osoby, które rozpalą mój zapał", "e": "Trudno mi zacząć, jeśli cele nie są jasne", "f": "Czasami nie udaje mi się wyjaśnić złożonych spraw, które przychodzą mi do głowy", "g": "Mam świadomość, że wymagam od innych rzeczy, których sam nie potrafię zrobić", "h": "Waham się, gdy powinienem forsować swoje punkty widzenia wobec prawdziwej opozycji"}', 0, 7, true, null, null, null, null, null, null),

-- Test 5 (PO1 Grupa Maciej - Ankieta)
(20, 5, 'Opisz swoje doświadczenie w branży', 'TEXT', null, 10, 1, true, null, null, null, null, null, null),
(21, 5, 'Czy masz doświadczenie w zarządzaniu zespołem?', 'BOOLEAN', null, 5, 2, true, null, true, null, null, null, null),
(22, 5, 'Oceń swoją znajomość metodyk zwinnych', 'SCALE', null, 15, 3, true, null, null, null, 4, null, null),

-- Test 6 (PO1 Grupa Maciej - IQ)
(23, 6, 'Rozwiąż zagadkę logiczną...', 'TEXT', null, 15, 1, true, 'Odpowiedź A', null, null, null, null, null),
(24, 6, 'Wybierz prawidłową sekwencję', 'ABCDEF', null, 15, 2, true, null, null, null, null, null, 'D'),

-- Test 7 (PO2 Grupa Maciej - Ankieta)
(25, 7, 'Jakie są twoje mocne strony?', 'TEXT', null, 10, 1, true, null, null, null, null, null, null),
(26, 7, 'Opisz swoją idealną kulturę organizacyjną', 'TEXT', null, 10, 2, true, null, null, null, null, null, null),

-- Test 8 (PO3 Grupa Maciej - IQ)
(27, 8, 'Rozwiąż problem matematyczny...', 'TEXT', null, 20, 1, true, '42', null, null, null, null, null),
(28, 8, 'Wybierz prawidłowe rozwiązanie', 'ABCDEF', null, 15, 2, true, null, null, null, null, null, 'E'),

-- Test 9 (PO1 Grupy Sebastian+Maciej - Ankieta)
(29, 9, 'Opisz swoje największe wyzwanie zawodowe', 'TEXT', null, 15, 1, true, null, null, null, null, null, null),
(30, 9, 'Jakie są twoje oczekiwania wobec pracodawcy?', 'TEXT', null, 10, 2, true, null, null, null, null, null, null),

-- Test 10 (PO1 Grupy Sebastian+Maciej - IQ)
(31, 10, 'Rozwiąż ciąg logiczny...', 'TEXT', null, 15, 1, true, '15', null, null, null, null, null),
(32, 10, 'Wybierz prawidłową odpowiedź', 'ABCDEF', null, 15, 2, true, null, null, null, null, null, 'A'),

-- Test 11 (PO2 Grupy Sebastian+Maciej - Ankieta)
(33, 11, 'Jak radzisz sobie ze stresem?', 'TEXT', null, 10, 1, true, null, null, null, null, null, null),
(34, 11, 'Opisz sytuację konfliktową i jak ją rozwiązałeś', 'TEXT', null, 15, 2, true, null, null, null, null, null, null),

-- Test 12 (PO3 Grupy Sebastian+Maciej - IQ)
(35, 12, 'Rozwiąż złożone zadanie logiczne...', 'TEXT', null, 20, 1, true, 'Odpowiedź B', null, null, null, null, null),
(36, 12, 'Wybierz prawidłową sekwencję', 'ABCDEF', null, 15, 2, true, null, null, null, null, null, 'C');

-- 6. Powiązania testów z grupami
INSERT INTO link_groups_tests (group_id, test_id) VALUES
-- Przypisanie testów do Grupy Sebastian
(2, 1), (2, 2), (2, 3), (2, 4),

-- Przypisanie testów do Grupy Maciej
(4, 5), (4, 6), (4, 7), (4, 8),

-- Przypisanie testów do grupy wspólnej (Sebastian i Maciej)
(3, 9), (3, 10), (3, 11), (3, 12), (3, 13);

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
    5000, 7000, 1, 3, 4,
    30, 30, 40, 'univ_token_KAM_SEB_2024', true, now(), now()),

(2, 'KAM_MAC_2024', 'Kampania Grupa Maciej', 'Kraków', 'B2B', 'Pełny etat',
    '2024-07-01', 'Wsparcie psychologiczne', 'Doświadczenie w terapii', 
    'Elastyczne godziny pracy', 'Zatrudnimy psychologa',
    6000, 9000, 5, 7, 8,
    30, 30, 40, 'univ_token_KAM_MAC_2024', true, now(), now()),

(3, 'KAM_OBA_2024', 'Kampania Obu Grup', 'Gdańsk', 'B2B', 'Pełny etat',
    '2024-08-01', 'Rozwój oprogramowania', 'JavaScript, Python', 
    'Praca zdalna', 'Poszukujemy programisty',
    10000, 15000, 9, 11, 12,
    30, 30, 40, 'univ_token_KAM_OBA_2024', true, now(), now());

-- 8. Powiązania kampanii z grupami
INSERT INTO link_groups_campaigns (group_id, campaign_id) VALUES
(2, 1),        -- Kampania Grupa Sebastian -> Grupa Sebastian
(4, 2),        -- Kampania Grupa Maciej -> Grupa Maciej
(2, 3),        -- Kampania Obu Grup -> Grupa Sebastian
(4, 3);        -- Kampania Obu Grup -> Grupa Maciej
