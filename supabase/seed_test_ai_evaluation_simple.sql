-- Insert test
INSERT INTO tests (id, title, test_type, description, passing_threshold, time_limit_minutes, created_at, updated_at) VALUES
    (9991, 'Test Kompetencji Zawodowych', 'SURVEY', 'Test sprawdzający wiedzę i umiejętności w zakresie pracy biurowej i magazynowej', 70, 60, now(), now());

-- Insert questions
INSERT INTO questions (id, test_id, question_text, answer_type, points, order_number, is_required, algorithm_type, algorithm_params) VALUES
    (9001, 9991, 'Opisz procedurę przyjęcia towaru do magazynu. Jakie są kluczowe etapy i na co należy zwrócić szczególną uwagę?', 'TEXT', 10, 1, true, 'EVALUATION_BY_AI', '{"evaluation_focus": "Sprawdź czy odpowiedź zawiera: kontrolę dokumentacji, sprawdzenie stanu towaru, weryfikację ilościową, oznaczenie lokalizacji, wprowadzenie do systemu WMS", "scoring_criteria": "10 punktów: Pełny opis wszystkich etapów z uwzględnieniem kontroli jakości\n7.5 punktów: Większość etapów opisana poprawnie\n5 punktów: Podstawowe etapy bez szczegółów\n2.5 punktów: Fragmentaryczny opis\n0 punktów: Brak istotnych elementów"}'),
    (9002, 9991, 'Jakie znasz systemy organizacji przestrzeni biurowej i który z nich uważasz za najbardziej efektywny? Uzasadnij swoją odpowiedź.', 'TEXT', 10, 2, true, 'EVALUATION_BY_AI', '{"evaluation_focus": "Ocena znajomości różnych layoutów biurowych (open space, cubicles, hot-desking, activity-based working) oraz umiejętność argumentacji", "scoring_criteria": "10 punktów: Szczegółowy opis minimum 3 systemów z trafnym uzasadnieniem wyboru\n7.5 punktów: Opis 2-3 systemów z dobrym uzasadnieniem\n5 punktów: Podstawowy opis z prostym uzasadnieniem\n2.5 punktów: Powierzchowna znajomość tematu\n0 punktów: Brak merytorycznej odpowiedzi"}'),
    (9003, 9991, 'Opisz, jak radzisz sobie z trudnym klientem wewnętrznym, który ma nierealne oczekiwania czasowe dotyczące realizacji zadania.', 'TEXT', 10, 3, true, 'EVALUATION_BY_AI', '{"evaluation_focus": "Ocena umiejętności komunikacji, rozwiązywania konfliktów i zarządzania oczekiwaniami", "scoring_criteria": "10 punktów: Kompleksowe podejście z przykładami technik komunikacji i negocjacji\n7.5 punktów: Dobre podejście z elementami profesjonalnej komunikacji\n5 punktów: Podstawowe techniki radzenia sobie\n2.5 punktów: Powierzchowne rozwiązanie\n0 punktów: Brak konstruktywnego podejścia"}'),
    -- (9004, 9991, 'Jakie znasz metody optymalizacji procesów biurowych i jak można je zastosować w praktyce?', 'TEXT', 10, 4, true, 'EVALUATION_BY_AI', '{"evaluation_focus": "Sprawdź znajomość lean management, automatyzacji, digitalizacji i innych metod optymalizacji", "scoring_criteria": "10 punktów: Szczegółowy opis kilku metod z przykładami zastosowania\n7.5 punktów: Dobra znajomość metod z podstawowymi przykładami\n5 punktów: Podstawowa wiedza o metodach\n2.5 punktów: Powierzchowna znajomość\n0 punktów: Brak znajomości metod"}'),
    -- (9005, 9991, 'Opisz, jak zorganizujesz pracę zespołu w sytuacji nagłego wzrostu liczby zamówień w magazynie.', 'TEXT', 10, 5, true, 'EVALUATION_BY_AI', '{"evaluation_focus": "Ocena umiejętności zarządzania kryzysowego, planowania i organizacji pracy zespołu", "scoring_criteria": "10 punktów: Kompleksowy plan z uwzględnieniem priorytetyzacji i zasobów\n7.5 punktów: Dobry plan z podstawowymi elementami zarządzania\n5 punktów: Podstawowe rozwiązania\n2.5 punktów: Chaotyczny plan\n0 punktów: Brak planu"}'),
    -- (9006, 9991, 'Jakie znasz systemy do zarządzania dokumentacją elektroniczną i jak wpływają one na efektywność pracy biurowej?', 'TEXT', 10, 6, true, 'EVALUATION_BY_AI', '{"evaluation_focus": "Sprawdź znajomość systemów DMS, ich funkcjonalności i korzyści z wdrożenia", "scoring_criteria": "10 punktów: Szczegółowa znajomość systemów z analizą korzyści\n7.5 punktów: Dobra znajomość z podstawową analizą\n5 punktów: Podstawowa wiedza\n2.5 punktów: Powierzchowna znajomość\n0 punktów: Brak wiedzy"}'),
    -- (9007, 9991, 'Opisz procedurę inwentaryzacji w magazynie. Jakie są kluczowe elementy i jak zapewnić jej dokładność?', 'TEXT', 10, 7, true, 'EVALUATION_BY_AI', '{"evaluation_focus": "Ocena znajomości procesu inwentaryzacji, metod liczenia i kontroli jakości", "scoring_criteria": "10 punktów: Pełna procedura z metodami kontroli i zapewnienia dokładności\n7.5 punktów: Dobry opis z podstawowymi elementami kontroli\n5 punktów: Podstawowy opis procesu\n2.5 punktów: Fragmentaryczny opis\n0 punktów: Brak znajomości procesu"}'),
    -- (9008, 9991, 'Jak zapewnisz bezpieczeństwo danych w środowisku biurowym? Opisz kluczowe procedury i narzędzia.', 'TEXT', 10, 8, true, 'EVALUATION_BY_AI', '{"evaluation_focus": "Sprawdź znajomość zasad cyberbezpieczeństwa, RODO i procedur ochrony danych", "scoring_criteria": "10 punktów: Kompleksowa wiedza o bezpieczeństwie z przykładami\n7.5 punktów: Dobra znajomość podstawowych zasad\n5 punktów: Podstawowa wiedza\n2.5 punktów: Powierzchowna znajomość\n0 punktów: Brak wiedzy o bezpieczeństwie"}'),
    -- (9009, 9991, 'Jakie znasz metody motywowania pracowników w środowisku magazynowym? Podaj przykłady ich skutecznego zastosowania.', 'TEXT', 10, 9, true, 'EVALUATION_BY_AI', '{"evaluation_focus": "Ocena znajomości technik motywacji i ich praktycznego zastosowania", "scoring_criteria": "10 punktów: Różnorodne metody z przykładami i analizą skuteczności\n7.5 punktów: Dobre metody z przykładami\n5 punktów: Podstawowe metody\n2.5 punktów: Powierzchowne podejście\n0 punktów: Brak znajomości metod"}'),
    -- (90010, 9991, 'Opisz, jak zorganizujesz szkolenie nowego pracownika w dziale obsługi klienta.', 'TEXT', 10, 10, true, 'EVALUATION_BY_AI', '{"evaluation_focus": "Sprawdź plan onboardingu, metody szkolenia i weryfikacji wiedzy", "scoring_criteria": "10 punktów: Kompleksowy plan szkolenia z etapami i weryfikacją\n7.5 punktów: Dobry plan z podstawowymi elementami\n5 punktów: Podstawowy plan\n2.5 punktów: Chaotyczny plan\n0 punktów: Brak planu"}'),
    -- (90011, 9991, 'Jakie znasz systemy zarządzania jakością i jak można je zastosować w pracy biurowej?', 'TEXT', 10, 11, true, 'EVALUATION_BY_AI', '{"evaluation_focus": "Ocena znajomości systemów jakości (ISO, TQM) i ich praktycznego zastosowania", "scoring_criteria": "10 punktów: Szczegółowa znajomość systemów z przykładami\n7.5 punktów: Dobra znajomość podstawowych systemów\n5 punktów: Podstawowa wiedza\n2.5 punktów: Powierzchowna znajomość\n0 punktów: Brak wiedzy"}'),
    -- (90012, 9991, 'Opisz, jak zorganizujesz proces reklamacji w magazynie. Jakie procedury wprowadzisz?', 'TEXT', 10, 12, true, 'EVALUATION_BY_AI', '{"evaluation_focus": "Sprawdź znajomość procesu reklamacji, dokumentacji i obsługi klienta", "scoring_criteria": "10 punktów: Kompleksowa procedura z uwzględnieniem wszystkich aspektów\n7.5 punktów: Dobra procedura z podstawowymi elementami\n5 punktów: Podstawowa procedura\n2.5 punktów: Fragmentaryczna procedura\n0 punktów: Brak procedury"}'),
    -- (90013, 9991, 'Jakie znasz metody zarządzania projektami i która jest najbardziej odpowiednia dla środowiska biurowego?', 'TEXT', 10, 13, true, 'EVALUATION_BY_AI', '{"evaluation_focus": "Ocena znajomości metodyk (Agile, Waterfall, Kanban) i umiejętności ich doboru", "scoring_criteria": "10 punktów: Szczegółowa analiza metodyk z uzasadnieniem wyboru\n7.5 punktów: Dobra znajomość z podstawowym uzasadnieniem\n5 punktów: Podstawowa wiedza\n2.5 punktów: Powierzchowna znajomość\n0 punktów: Brak wiedzy"}'),
    -- (90014, 9991, 'Opisz, jak zorganizujesz system rotacji stanowisk w magazynie. Jakie korzyści i wyzwania to przyniesie?', 'TEXT', 10, 14, true, 'EVALUATION_BY_AI', '{"evaluation_focus": "Sprawdź znajomość zarządzania zasobami ludzkimi i rozwoju pracowników", "scoring_criteria": "10 punktów: Kompleksowy plan z analizą korzyści i ryzyk\n7.5 punktów: Dobry plan z podstawową analizą\n5 punktów: Podstawowy plan\n2.5 punktów: Chaotyczny plan\n0 punktów: Brak planu"}'),
    -- (90015, 9991, 'Jakie znasz narzędzia do automatyzacji pracy biurowej i jak można je efektywnie wykorzystać?', 'TEXT', 10, 15, true, 'EVALUATION_BY_AI', '{"evaluation_focus": "Ocena znajomości narzędzi automatyzacji i ich praktycznego zastosowania", "scoring_criteria": "10 punktów: Szczegółowa znajomość narzędzi z przykładami zastosowania\n7.5 punktów: Dobra znajomość podstawowych narzędzi\n5 punktów: Podstawowa wiedza\n2.5 punktów: Powierzchowna znajomość\n0 punktów: Brak wiedzy"}'),
    -- (90016, 9991, 'Opisz, jak zapewnisz ergonomię stanowiska pracy w biurze. Jakie elementy są kluczowe?', 'TEXT', 10, 16, true, 'EVALUATION_BY_AI', '{"evaluation_focus": "Sprawdź znajomość zasad ergonomii i BHP w środowisku biurowym", "scoring_criteria": "10 punktów: Kompleksowa wiedza o ergonomii z praktycznymi rozwiązaniami\n7.5 punktów: Dobra znajomość podstawowych zasad\n5 punktów: Podstawowa wiedza\n2.5 punktów: Powierzchowna znajomość\n0 punktów: Brak wiedzy"}'),
    (90017, 9991, 'Jakie znasz metody optymalizacji kosztów w magazynie i jak można je wdrożyć?', 'TEXT', 10, 17, true, 'EVALUATION_BY_AI', '{"evaluation_focus": "Ocena znajomości metod redukcji kosztów i efektywności operacyjnej", "scoring_criteria": "10 punktów: Szczegółowa analiza metod z planem wdrożenia\n7.5 punktów: Dobre metody z podstawowym planem\n5 punktów: Podstawowe metody\n2.5 punktów: Powierzchowne podejście\n0 punktów: Brak wiedzy"}'),
    (90018, 9991, 'Opisz, jak zorganizujesz system obiegu dokumentów w firmie. Jakie narzędzia wykorzystasz?', 'TEXT', 10, 18, true, 'EVALUATION_BY_AI', '{"evaluation_focus": "Sprawdź znajomość systemów workflow i zarządzania dokumentacją", "scoring_criteria": "10 punktów: Kompleksowy system z wykorzystaniem nowoczesnych narzędzi\n7.5 punktów: Dobry system z podstawowymi narzędziami\n5 punktów: Podstawowy system\n2.5 punktów: Chaotyczny system\n0 punktów: Brak systemu"}'),
    (90019, 9991, 'Jakie znasz metody zarządzania czasem i jak można je zastosować w pracy biurowej?', 'TEXT', 10, 19, true, 'EVALUATION_BY_AI', '{"evaluation_focus": "Ocena znajomości technik time management i ich praktycznego zastosowania", "scoring_criteria": "10 punktów: Szczegółowa znajomość metod z przykładami zastosowania\n7.5 punktów: Dobra znajomość podstawowych metod\n5 punktów: Podstawowa wiedza\n2.5 punktów: Powierzchowna znajomość\n0 punktów: Brak wiedzy"}'),
    (90020, 9991, 'System kontroli jakości w magazynie: 1. Procedury kontroli na przyjęciu (AQL sampling), 2. Kontrola mi��dzyoperacyjna z check-listami, 3. Audyty 5S codzienne, 4. System raportowania niezgodności, 5. Analiza Pareto błędów, 6. Karty kontrolne dla kluczowych procesów, 7. Szkolenia jakościowe dla pracowników. Narzędzia: tablety z aplikacją QC, skanery, wagi kontrolne. Miesięczny przegląd KPI jakościowych.', 'TEXT', 10, 20, true, 'EVALUATION_BY_AI', '{"evaluation_focus": "Sprawdź znajomość systemów kontroli jakości i ich implementacji", "scoring_criteria": "10 punktów: Kompleksowy system z procedurami i narzędziami\n7.5 punktów: Dobry system z podstawowymi elementami\n5 punktów: Podstawowy system\n2.5 punktów: Chaotyczny system\n0 punktów: Brak systemu"}');

-- Insert campaign
INSERT INTO campaigns (id, code, title, workplace_location, contract_type, employment_type, work_start_date, duties, requirements, employer_offerings, job_description, salary_range_min, salary_range_max, is_active, po1_test_id, po1_test_weight) VALUES
    (9001, 'OFFICE_SPECIALIST_2024', 'Specjalista ds. Administracyjno-Magazynowych', 'Warszawa', 'Umowa o pracę', 'Pełny etat', '2024-05-01', 'Zarządzanie dokumentacją, obsługa systemów magazynowych, koordynacja procesów biurowych', 'Min. 2 lata doświadczenia, znajomość systemów WMS, umiejętności organizacyjne', 'Konkurencyjne wynagrodzenie, pakiet benefitów, szkolenia', 'Poszukujemy osoby do zarządzania procesami administracyjnymi i magazynowymi', 5000, 8000, true, 9991, 100); 

-- Link groups with campaign and test
INSERT INTO link_groups_campaigns (group_id, campaign_id) VALUES
    (1, 9001), -- Avena
    (2, 9001), -- Robotics
    (3, 9001), -- Liceum
    (4, 9001), -- SPJ5A
    (5, 9001), -- PJ5A
    (6, 9001), -- SPKG74
    (7, 9001), -- P74
    (8, 9001), -- P27
    (9, 9001); -- Munchies

INSERT INTO link_groups_tests (group_id, test_id) VALUES
    (1, 9991), -- Avena
    (2, 9991), -- Robotics
    (3, 9991), -- Liceum
    (4, 9991), -- SPJ5A
    (5, 9991), -- PJ5A
    (6, 9991), -- SPKG74
    (7, 9991), -- P74
    (8, 9991), -- P27
    (9, 9991); -- Munchies

-- Insert candidates
INSERT INTO candidates (id, campaign_id, first_name, last_name, email, phone, recruitment_status, created_at, updated_at, po1_started_at, po1_completed_at) VALUES
    (9001, 9001, 'Anna', 'Kowalska', 'anna.kowalska@example.com', '+48123456789', 'PO1', now(), now(), now() - interval '2 hours', now() - interval '1 hour'),
    (9002, 9001, 'Jan', 'Nowak', 'jan.nowak@example.com', '+48987654321', 'PO1', now(), now(), now() - interval '2 hours', now() - interval '1 hour'),
    (9003, 9001, 'Maria', 'Wiśniewska', 'maria.wisniewska@example.com', '+48555666777', 'PO1', now(), now(), now() - interval '2 hours', now() - interval '1 hour');

-- Insert answers for the first candidate (excellent answers)
INSERT INTO candidate_answers (id, candidate_id, question_id, stage, text_answer, score, created_at) VALUES
    (1, 9001, 9001, 'PO1', 'Procedura przyjęcia towaru do magazynu składa się z następujących etapów: 1. Kontrola dokumentacji dostawy (list przewozowy, faktura), 2. Wstępna inspekcja stanu towaru i opakowań, 3. Szczegółowa weryfikacja ilościowa z dokumentami, 4. Kontrola jakościowa towaru, 5. Oznaczenie lokalizacji magazynowej zgodnie z systemem, 6. Wprowadzenie danych do systemu WMS, 7. Generowanie i drukowanie etykiet lokalizacyjnych, 8. Fizyczne rozmieszczenie towaru, 9. Potwierdzenie przyjęcia w systemie.', 10, now()),
    (2, 9001, 9002, 'PO1', 'Główne systemy organizacji przestrzeni biurowej to: 1. Open space - wspólna przestrzeń sprzyjająca komunikacji i współpracy, 2. Cubicles - wydzielone boksy zapewniające prywatność, 3. Hot-desking - elastyczny system bez przypisanych miejsc, 4. Activity-based working - przestrzenie dostosowane do rodzaju wykonywanej pracy. Najbardziej efektywny jest system activity-based working, ponieważ pozwala na optymalne wykorzystanie przestrzeni, wspiera różne style pracy i zwiększa produktywność poprzez dostosowanie środowiska do konkretnych zadań.', 10, now()),
    (3, 9001, 9003, 'PO1', 'W przypadku trudnego klienta wewnętrznego stosuję następujące podejście: 1. Aktywne słuchanie i zrozumienie potrzeb, 2. Spokojne wyjaśnienie realistycznych ram czasowych, 3. Przedstawienie szczegółowego planu realizacji z uwzględnieniem innych zobowiązań, 4. Zaproponowanie alternatywnych rozwiązań (np. realizacja częściowa), 5. Dokumentacja ustaleń mailem, 6. Regularna komunikacja o postępach. Kluczowe jest zachowanie profesjonalizmu i znalezienie kompromisu.', 10, now()),
    -- (4, 1, 9004, 'PO1', 'Główne metody optymalizacji procesów biurowych: 1. Lean Office - eliminacja marnotrawstwa, standaryzacja procesów, 2. Automatyzacja rutynowych zadań poprzez RPA (Robotic Process Automation), 3. Digitalizacja dokumentów i workflow elektroniczny, 4. Metodologia Kaizen - ciągłe usprawnienia, 5. Six Sigma dla redukcji błędów. Przykład: wdrożenie automatycznego systemu obiegu faktur skróciło proces akceptacji z 5 dni do 1 dnia.', 10, now()),
    -- (5, 1, 9005, 'PO1', 'Plan organizacji pracy w sytuacji wzrostu zamówień: 1. Natychmiastowa analiza wolumenów i dostępnych zasobów, 2. Priorytetyzacja zamówień według pilności i wartości, 3. Reorganizacja zmian i optymalizacja procesów pickingu, 4. Wdrożenie systemu motywacyjnego za zwiększoną wydajność, 5. Tymczasowe wsparcie z innych działów, 6. Monitoring KPI w czasie rzeczywistym, 7. Komunikacja z klientami o możliwych opóźnieniach.', 10, now()),
    -- (6, 1, 9006, 'PO1', 'Systemy DMS (Document Management System) kluczowe dla efektywności: 1. SharePoint - integracja z Office 365, wspólna praca na dokumentach, 2. OpenText - zaawansowane workflow i archiwizacja, 3. M-Files - inteligentne kategoryzowanie dokumentów, 4. Alfresco - open-source z szeroką funkcjonalnością. Korzyści: redukcja czasu wyszukiwania o 50%, eliminacja dokumentów papierowych, bezpieczeństwo danych, automatyczna archiwizacja.', 10, now()),
    -- (7, 1, 9007, 'PO1', 'Kompleksowa procedura inwentaryzacji: 1. Przygotowanie - zamknięcie przyjęć/wydań, aktualizacja systemu WMS, 2. Zespoły liczące z cross-checkiem, 3. Wykorzystanie skanerów kodów kreskowych, 4. Metoda ABC - najpierw towary wysokowartościowe, 5. Podwójne liczenie dla dokładności, 6. Analiza rozbieżności na bieżąco, 7. Dokumentacja fotograficzna problemów, 8. Raport końcowy z analizą przyczyn różnic.', 10, now()),
    -- (8, 1, 9008, 'PO1', 'Bezpieczeństwo danych w biurze: 1. Polityka haseł (min. 12 znaków, zmiana co 30 dni), 2. Dwuskładnikowe uwierzytelnianie, 3. Szyfrowanie dysków i komunikacji, 4. Regularne szkolenia RODO, 5. Procedura clean desk, 6. Backup przyrostowy codzienny i pełny tygodniowy, 7. Monitoring dostępu do danych, 8. Procedury na wypadek wycieku danych, 9. Regularne audyty bezpieczeństwa.', 10, now()),
    -- (9, 1, 9009, 'PO1', 'System motywacyjny w magazynie: 1. Finansowy - premie za wydajność i bezbłędność, 2. Rozwojowy - szkolenia i ścieżka awansu, 3. Integracyjny - konkursy zespołowe, 4. Recognition program - pracownik miesiąca z benefitami, 5. Elastyczny grafik dla najlepszych, 6. Jasne KPI i regularne feedback, 7. Program sugestii pracowniczych z nagrodami. Przykład: wdrożenie systemu premii za bezbłędność zmniejszyło ilość reklamacji o 40%.', 10, now()),
    -- (10, 1, 90010, 'PO1', 'Plan szkolenia w obsłudze klienta: 1. Wprowadzenie teoretyczne - standardy i procedury, 2. Szkolenie z systemów i narzędzi, 3. Shadowing doświadczonego pracownika, 4. Symulacje trudnych sytuacji, 5. Samodzielna praca pod nadzorem, 6. Regularne sesje feedback, 7. Testy wiedzy i umiejętności, 8. Certyfikacja wewnętrzna. Plan rozłożony na 2 tygodnie z codzienną weryfikacją postępów.', 10, now()),
    -- (11, 1,90011, 'PO1', 'Systemy zarządzania jakością w biurze: 1. ISO 9001:2015 - dokumentacja i procesy, 2. TQM - kompleksowe zarządzanie jakością, 3. Six Sigma - redukcja błędów, 4. Lean Office - optymalizacja procesów. Praktyczne zastosowanie: mapowanie procesów, standaryzacja procedur, audyty wewnętrzne, zarządzanie niezgodnościami, ciągłe doskonalenie. Przykład: wdrożenie ISO zredukowało ilość błędów w dokumentacji o 75%.', 10, now()),
    -- (12, 1, 90012, 'PO1', 'Proces reklamacji w magazynie: 1. Rejestracja w systemie z dokumentacją foto, 2. Kategoryzacja według pilności i typu, 3. Analiza przyczyny przez zespół ekspercki, 4. Kwarantanna towaru, 5. Komunikacja z klientem w ciągu 24h, 6. Plan naprawczy z terminami, 7. Monitoring realizacji, 8. Raport zamknięcia z wnioskami, 9. Aktualizacja procedur prewencyjnych. System raportowania trendów reklamacyjnych miesięcznie.', 10, now()),
    -- (13, 1, 90013, 'PO1', 'Metodyki zarządzania projektami: 1. Agile Scrum - elastyczne reagowanie na zmiany, daily standupy, 2. Kanban - wizualizacja workflow i limitów WIP, 3. Waterfall - dla projektów o jasno zdefiniowanym zakresie. Dla biura najlepsza Kanban ze względu na: wizualną kontrolę obciążenia, elastyczne zarządzanie priorytetami, łatwą identyfikację wąskich gardeł. Przykład: wdrożenie Kanban zwiększyło przepustowość działu o 30%.', 10, now()),
    -- (14, 1, 90014, 'PO1', 'System rotacji stanowisk w magazynie: 1. Matryca kompetencji pracowników, 2. Plan rotacji kwartalny, 3. Szkolenia cross-funkcyjne, 4. Mentoring przez ekspertów, 5. Ocena efektywności na nowych stanowiskach. Korzyści: wszechstronność pracowników, redukcja monotonii, zastępowalność, rozwój kompetencji. Wyzwania: czasowy spadek wydajności, opór pracowników, koszty szkoleń. Rozwiązanie: pilotaż i stopniowe wdrażanie.', 10, now()),
    -- (15, 1, 90015, 'PO1', 'Narzędzia automatyzacji biurowej: 1. RPA (UiPath, Blue Prism) - automatyzacja powtarzalnych zadań, 2. Power Automate - integracja systemów Microsoft, 3. Zapier - automatyzacja między aplikacjami, 4. OCR z AI - digitalizacja dokumentów. Przykłady: automatyczne księgowanie faktur (oszczędność 4h dziennie), automatyczna kategoryzacja maili (wzrost responsywności o 60%), automatyczne raportowanie (redukcja czasu o 80%).', 10, now()),
    -- (16, 1, 90016, 'PO1', 'Ergonomia stanowiska biurowego: 1. Regulowane krzesło z podparciem lędźwiowym, 2. Biurko z regulacją wysokości (praca stojąca/siedząca), 3. Monitor na wysokości oczu z filtrem światła niebieskiego, 4. Ergonomiczna klawiatura i mysz, 5. Oświetlenie dostosowane do pory dnia, 6. Mata pod nadgarstek, 7. Podnóżek ergonomiczny. Regularne szkolenia z ergonomii i przerwy na ćwiczenia co 2 godziny.', 10, now()),
    (17, 9001, 90017, 'PO1', 'Optymalizacja kosztów magazynu: 1. ABC/XYZ - optymalizacja rozmieszczenia towaru, 2. Lean Warehouse - eliminacja marnotrawstwa, 3. Automatyzacja procesów powtarzalnych, 4. Optymalizacja tras wózków, 5. Zarządzanie energią (LED, czujniki ruchu), 6. Współdzielenie zasobów między zmianami, 7. Predykcyjne utrzymanie sprzętu. KPI: redukcja kosztów operacyjnych o 15% rocznie.', 10, now()),
    (18, 9001, 90018, 'PO1', 'System obiegu dokumentów: 1. Microsoft SharePoint jako centralne repozytorium, 2. Power Automate dla workflow akceptacji, 3. Teams dla komunikacji i współpracy, 4. OneDrive dla dokumentów roboczych, 5. Adobe Sign dla podpisów elektronicznych. Procedury: nazewnictwo plików, struktura folderów, uprawnienia dostępu, wersjonowanie, archiwizacja. Szkolenia i dokumentacja dla użytkowników.', 10, now()),
    (19, 9001, 90019, 'PO1', 'Zarządzanie czasem w biurze: 1. Metoda Pomodoro (25 min pracy, 5 min przerwy), 2. Matryca Eisenhowera dla priorytetyzacji, 3. Zasada 2 minut dla małych zadań, 4. Time-blocking w kalendarzu, 5. Zasada 80/20 (Pareto), 6. Zero Inbox dla maili. Narzędzia: Microsoft To-Do, Focus@Will, RescueTime. Przykład: wdrożenie time-blockingu zwiększyło produktywność o 40%.', 10, now()),
    (20, 9001, 90020, 'PO1', 'System kontroli jakości w magazynie: 1. Procedury kontroli na przyjęciu (AQL sampling), 2. Kontrola międzyoperacyjna z check-listami, 3. Audyty 5S codzienne, 4. System raportowania niezgodności, 5. Analiza Pareto błędów, 6. Karty kontrolne dla kluczowych procesów, 7. Szkolenia jakościowe dla pracowników. Narzędzia: tablety z aplikacją QC, skanery, wagi kontrolne. Miesięczny przegląd KPI jakościowych.', 10, now());

-- Insert answers for the second candidate (poor answers)
INSERT INTO candidate_answers (id, candidate_id, question_id, stage, text_answer, score, created_at) VALUES
    (21, 9002, 9001, 'PO1', 'Trzeba sprawdzić towar i położyć go na półkę.', 0, now()),
    (22, 9002, 9002, 'PO1', 'Biurka i krzesła, najlepiej żeby każdy miał swoje.', 0, now()),
    (23, 9002, 9003, 'PO1', 'Powiem mu żeby poczekał.', 0, now()),
    -- (24, 2, 4, 'PO1', 'Excel chyba jest dobry.', 0, now()),
    -- (25, 2, 5, 'PO1', 'Trzeba więcej pracować.', 0, now()),
    -- (26, 2, 6, 'PO1', 'Jakiś program do plików.', 0, now()),
    -- (27, 2, 7, 'PO1', 'Liczymy wszystko co jest.', 0, now()),
    -- (28, 2, 8, 'PO1', 'Hasła do komputerów.', 0, now()),
    -- (29, 2, 9, 'PO1', 'Premia za dobrą pracę.', 0, now()),
    -- (30, 2, 10, 'PO1', 'Pokazać co ma robić.', 0, now()),
    -- (31, 2, 11, 'PO1', 'Nie znam systemów jakości.', 0, now()),
    -- (32, 2, 12, 'PO1', 'Przyjąć reklamację i naprawić.', 0, now()),
    -- (33, 2, 13, 'PO1', 'Excel do zarządzania.', 0, now()),
    -- (34, 2, 14, 'PO1', 'Zmiana stanowisk czasami.', 0, now()),
    -- (35, 2, 15, 'PO1', 'Jakieś programy komputerowe.', 0, now()),
    -- (36, 2, 16, 'PO1', 'Wygodne krzesło.', 0, now()),
    (37, 9002, 90017, 'PO1', 'Oszczędzać na wszystkim.', 0, now()),
    (38, 9002, 90018, 'PO1', 'Wysyłać maile.', 0, now()),
    (39, 9002, 90019, 'PO1', 'Robić wszystko na czas.', 0, now()),
    (40, 9002, 90020, 'PO1', 'Sprawdzać czy nie ma błędów.', 0, now());

-- Insert answers for the third candidate (mixed quality answers)
INSERT INTO candidate_answers (id, candidate_id, question_id, stage, text_answer, score, created_at) VALUES
    (41, 9003, 9001, 'PO1', 'Przyjęcie towaru wymaga sprawdzenia dokumentów, przeliczenia ilości i wprowadzenia do systemu. Należy też oznaczyć miejsce składowania.', 5, now()),
    (42, 9003, 9002, 'PO1', 'Znam open space i system gabinetowy. Open space jest lepszy do współpracy, ale może być głośno. Gabinetowy zapewnia spokój, ale utrudnia komunikację.', 7.5, now()),
    (43, 9003, 9003, 'PO1', 'Staram się wysłuchać klienta i wytłumaczyć mu sytuację. Czasem trzeba poszukać kompromisu.', 5, now()),
    -- (44, 3, 4, 'PO1', 'Można wykorzystać Excel do automatyzacji, wprowadzić elektroniczny obieg dokumentów. Pomaga to zaoszczędzić czas.', 7.5, now()),
    -- (45, 3, 5, 'PO1', 'Trzeba podzielić pracowników na grupy i przydzielić zadania. Można też wprowadzić nadgodziny.', 5, now()),
    -- (46, 3, 6, 'PO1', 'SharePoint jest dobry do przechowywania dokumentów. Ułatwia pracę i wszyscy mają dostęp do plików.', 7.5, now()),
    -- (47, 3, 7, 'PO1', 'Inwentaryzacja wymaga dokładnego liczenia towaru i sprawdzania z systemem. Najlepiej robić to w zespołach.', 5, now()),
    -- (48, 3, 8, 'PO1', 'Trzeba mieć dobre hasła i antywirusa. Ważne też żeby robić kopie zapasowe.', 7.5, now()),
    -- (49, 3, 9, 'PO1', 'Premie finansowe i pochwały są najlepsze. Ludzie lubią też elastyczny grafik.', 5, now()),
    -- (50, 3, 10, 'PO1', 'Najpierw teoria, potem praktyka z kimś doświadczonym. Na koniec samodzielna praca.', 7.5, now()),
    -- (51, 3, 11, 'PO1', 'ISO jest najpopularniejsze. Wymaga dokumentacji i procedur.', 5, now()),
    -- (52, 3, 12, 'PO1', 'Zapisać reklamację, sprawdzić towar, skontaktować się z klientem. Trzeba działać szybko.', 7.5, now()),
    -- (53, 3, 13, 'PO1', 'Agile jest dobry bo elastyczny. Waterfall lepszy do prostych projektów.', 5, now()),
    -- (54, 3, 14, 'PO1', 'Rotacja pomaga poznać różne stanowiska. Trzeba tylko dobrze przeszkolić pracowników.', 7.5, now()),
    -- (55, 3, 15, 'PO1', 'Makra w Excelu, automatyczne maile. Czasem własne skrypty.', 5, now()),
    -- (56, 3, 16, 'PO1', 'Dobre krzesło i monitor na odpowiedniej wysokości. Przerwy na odpoczynek.', 7.5, now()),
    (57, 9003, 90017, 'PO1', 'Optymalizacja tras w magazynie, lepsze wykorzystanie przestrzeni. Szkolenia pracowników.', 5, now()),
    (58, 9003, 90018, 'PO1', 'Foldery na serwerze, maile do akceptacji. Każdy wie gdzie co jest.', 7.5, now()),
    (59, 9003, 90019, 'PO1', 'Lista zadań i priorytety. Trudne sprawy rano kiedy jest się wypoczętym.', 5, now()),
    (60, 9003, 90020, 'PO1', 'Kontrola przy przyjęciu i wydaniu towaru. Raporty błędów i szkolenia.', 7.5, now());