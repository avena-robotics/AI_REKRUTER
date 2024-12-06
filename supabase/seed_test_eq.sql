-- Insert EQ test
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
        'Kwestionariusz samooceny', 
        'EQ', 
        'W każdej sekcji (od I do VII) masz do dyspozycji 10 punktów. Rozdziel je pomiędzy zdania, które najlepiej opisują Twoje zachowanie. Jest możliwe rozłożenie punktów na wszystkie zdania, jak również przyznanie wszystkich punktów tylko jednemu zdaniu', 
        75, 
        60, 
        now(), 
        now()
    )
    RETURNING id
),

-- Insert EQ questions
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
        'NO_ALGORITHM'::algorithm_type,
        NULL
    FROM (VALUES
        ('I. Oto co mogę wnieść w pracę zespołu:', 'AH_POINTS', '{"a": "Potrafię szybko dostrzegać i wykorzystywać nowe możliwości", "b": "Potrafię dobrze współpracować z bardzo różnymi ludźmi", "c": "Generowanie pomysłów to mój naturalny talent", "d": "Potrafię wydobyć z ludzi wszystko, co mogą wnieść do realizacji celów grupowych", "e": "Moja zdolność doprowadzania spraw do końca w dużej mierze wynika z mojej efektywności osobistej", "f": "Jestem gotów stawić czoła czasowej niepopularności, jeśli prowadzi to do wartościowych wyników", "g": "Zwykle potrafię wyczuć, co jest realistyczne i może zadziałać", "h": "Potrafię przedstawić różne alternatywne działania i możliwości"}', 0, 1, true),
        
        ('II. Moje słabości w pracy zespołowej:', 'AH_POINTS', '{"a": "Nie jestem spokojny, dopóki spotkania nie są dobrze ustrukturyzowane i kontrolowane", "b": "Mam skłonność do poświęcania zbyt dużej uwagi osobom, których punkt widzenia nie został właściwie uwzględniony", "c": "Mam tendencję do mówienia zbyt dużo, gdy grupa zajmuje się nowymi pomysłami", "d": "Mój obiektywny ogląd utrudnia mi łatwe i entuzjastyczne przyłączanie się do kolegów", "e": "Czasami jestem postrzegany jako wywierający zbyt silny nacisk i autorytatywny, gdy trzeba coś zrobić", "f": "Trudno mi przewodzić z pozycji lidera, być może dlatego, że jestem zbyt wrażliwy na atmosferę w grupie", "g": "Mam skłonność do zbytniego angażowania się w pomysły, które przychodzą mi do głowy, i tracenia orientacji w tym, co się dzieje", "h": "Moi koledzy mają tendencję do postrzegania mnie jako niepotrzebnie martwiącego się szczegółami i możliwością, że sprawy mogą pójść źle"}', 0, 2, true),
        
        ('III. Kiedy angażuję się w projekt z innymi ludźmi:', 'AH_POINTS', '{"a": "Mam zdolność wpływania na ludzi bez wywierania na nich presji", "b": "Moja czujność pozwala zapobiegać wielu pomyłkom i błędom", "c": "Jestem gotów naciskać na działanie, aby upewnić się, że zebranie nie marnuje czasu ani nie traci z oczu głównego celu", "d": "Można na mnie polegać, jeśli chodzi o wnoszenie oryginalnych pomysłów", "e": "Zawsze jestem gotów poprzeć dobre sugestie służące wspólnym interesom", "f": "Lubię szukać najnowszych pomysłów i wydarzeń", "g": "Wierzę, że moja zdolność osądu może pomóc w podjęciu właściwych decyzji", "h": "Można na mnie polegać, jeśli chodzi o dopilnowanie, aby cała istotna praca została zorganizowana"}', 0, 3, true),
        
        ('IV. Moje charakterystyczne podejście do pracy grupowej:', 'AH_POINTS', '{"a": "Mam spokojne zainteresowanie lepszym poznaniem kolegów", "b": "Nie waham się przeciwstawiać poglądom innych ani podtrzymywać swojego stanowiska, nawet wobec opozycji", "c": "Zwykle potrafię znaleźć argumenty na odrzucenie niesłusznych propozycji", "d": "Sądzę, że mam talent do wprowadzania rzeczy w życie, gdy trzeba realizować plan", "e": "Mam tendencję do unikania oczywistego i wychodzenia z czymś nieoczekiwanym", "f": "Wnoszę perfekcjonizm do każdego zespołowego zadania", "g": "Jestem gotów wykorzystywać kontakty poza grupą", "h": "Interesują mnie wszystkie punkty widzenia, ale nie waham się podjąć decyzji, gdy trzeba"}', 0, 4, true),
        
        ('V. Czerpię satysfakcję z pracy, ponieważ:', 'AH_POINTS', '{"a": "Lubię analizować sytuacje i rozważać wszystkie możliwości", "b": "Interesuje mnie znajdowanie praktycznych rozwiązań problemów", "c": "Lubię czuć, że wspieram dobre relacje w pracy", "d": "Mogę mieć silny wpływ na decyzje", "e": "Mogę spotykać ludzi, którzy mają coś nowego do zaoferowania", "f": "Potrafię doprowadzać ludzi do zgody co do koniecznego trybu działania", "g": "Czuję się w swoim żywiole, gdy mogę poświęcić zadaniu pełną uwagę", "h": "Lubię znajdować obszary, które poszerzają moją wyobraźnię"}', 0, 5, true),
        
        ('VI. Gdy otrzymuję trudne zadanie do wykonania w ograniczonym czasie:', 'AH_POINTS', '{"a": "Chciałbym się wycofać i opracować rozwiązanie, zanim rozwinę plan działania", "b": "Byłbym gotów pracować z osobą wykazującą najbardziej pozytywne podejście", "c": "Znalazłbym sposób na zmniejszenie złożoności zadania, ustalając, co mogą wnieść różne osoby", "d": "Moje naturalne poczucie pilności pomogłoby zapewnić, że nie przekroczymy harmonogramu", "e": "Wierzę, że zachowałbym spokój i zdolność do jasnego myślenia", "f": "Utrzymałbym stałość celu mimo presji", "g": "Byłbym gotów przejąć konstruktywne przywództwo, gdybym czuł, że grupa nie robi postępów", "h": "Otworzyłbym dyskusję, aby stymulować nowe myśli i uruchomić coś"}', 0, 6, true),
        
        ('VII. Problemy, jakim podlegam, pracując w grupach:', 'AH_POINTS', '{"a": "Mam skłonność do okazywania niecierpliwości wobec tych, którzy hamują postęp", "b": "Inni mogą mnie krytykować za zbytnią analityczność i niewystarczającą intuicyjność", "c": "Moje dążenie do zapewnienia właściwego wykonania pracy może wstrzymywać postęp", "d": "Mam tendencję do znudzenia i liczenia na jedną lub dwie stymulujące osoby, które rozpalą mój zapał", "e": "Trudno mi zacząć, jeśli cele nie są jasne", "f": "Czasami nie udaje mi się wyjaśnić złożonych spraw, które przychodzą mi do głowy", "g": "Mam świadomość, że wymagam od innych rzeczy, których sam nie potrafię zrobić", "h": "Waham się, gdy powinienem forsować swoje punkty widzenia wobec prawdziwej opozycji"}', 0, 7, true)
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
SELECT 'EQ test, questions and group links inserted successfully' as result;
