Provide a Chain-Of-Thought analysis before answering.
Review the project files thoroughly. If there is anything you need referenced that’s missing, ask for it.
If you’re unsure about any aspect of the task, ask for clarification. Don’t guess. Don’t make assumptions.
Don’t do anything unless explicitly instructed to do so. Nothing “extra”.
Always preserve everything from the original files, except for what is being updated.
Write all code in full with no placeholders. If you get cut off, I’ll say “continue”

# AI_REKRUTER

Kampanie i kandydaci to sa dwie oddzielne aplikacje.
Wspolna baza danych.

## Technologia: Supabase, Python, Flask, HMTL, JSS, Bootstrap

## Architektura:

- KAMPANIE:
    - Przycisk "Dodaj kampanię":
        * pole text 'Kod kampanii'
        * pole text 'Tytuł kampanii'
        * pole text 'Miejsce pracy'
        * pole text 'Rodzaj umowy'
        * pole text 'Rodzaj etatu'
        * pole date 'Rozpoczęcie pracy'
        * pole text 'Opis obowiązków'
        * pole text 'Wymagania'
        * pole text 'Co oferuje pracodawca'
        * pole text 'Opis czego potrzebujemy'
        * pole integer 'Dolna granica zakresu wynagrodzenia' (PLN)
        * pole integer 'Górna granica zakresu wynagrodzenia' (PLN) 
        * przycisk "Dodaj test":
            * pole enum 'Typ testu' (SURVEY, EQ, IQ)
            * pole varchar 'Etap' (PO1, PO2, PO3)
            * pole integer 'Waga testu' 
            ** ANKIETA:
                TODO: narysowac na drawio jak to by sie odbywalo
                * pole text 'Opis testu'
                * pole integer 'Próg zaliczenia'   
                * przycisk "Dodaj pytanie":
                    * pole text 'Treść pytania'
                    * pole obrazka (opcjonalnie) 
                    * pole enum 'Typ odpowiedzi' (TEXT, BOOLEAN, SCALE, SALARY, DATE, ABCDEF)
                        * jeśli Typ odpowiedzi = ABCDEF:
                            * pole text lub obrazek 'Odpowiedź A'
                            * pole text lub obrazek 'Odpowiedź B' 
                            * pole text lub obrazek 'Odpowiedź C'
                            * pole text lub obrazek 'Odpowiedź D'
                    * pole integer 'Ilość punktów za pytanie'
                    * pole integer 'Numer pytania'
                    * ocena pytania przez AI
                    * pole boolean 'Czy pytanie jest obowiązkowe'
                    * przycisk "Dodaj poprawną odpowiedź": 
                        * pole text 'Odpowiedź'
            ** EQ/IQ:
                * pole text 'Opis testu'
                * pole integer 'Próg zaliczenia'
                * przycisk "Generuj test"
        * przycisk "Generuj link uniwersalny"
        * przycisk "Zapisz"
                
    - Lista kampanii:
        * kod kampanii
        * tytuł kampanii
        * data utworzenia
        * status kampanii (aktywna/nieaktywna) 
        * przycisk "Edytuj" 
        * przycisk "Usuń"
        * przycisk "Generuj link uniwersalny" lub przycisk "Skopiuj link" jeśli już wygenerowany

- KANDYDACI:
    - Filtry:
        * kod kampanii
        * status rekrutacji
    - Sortowanie:
        * status rekrutacji
        * wynik PO1
        * wynik PO2
        * wynik PO3
        * wynik ogólny
    - Lista kandydatów:
        * imię i nazwisko
        * kod kampanii
        * email
        * status rekrutacji
        * wynik PO1
        * wynik PO2
        * wynik PO3
        * wynik ogólny
        * data utworzenia
        * Przycisk Akcje:
            * Przepchnij do kolejnego etapu
            * Odrzuć
            * Zaakceptuj
        * Przycisk "Pogląd Kandydata" otwiera modal:
            * Przycisk Zamknij
            * Wyświetla pytania, odpowiedzi i wyniki kandydata w poszczególnych etapach
            * Wyświetla pytania, odpowiedzi i wyniki kandydata w poszczególnych testach
            * Wyświetla pytania, odpowiedzi i wyniki kandydata w poszczególnych pytaniach


Wygenerowany link przenosi do strony z pytaniami dla danego testu do wypełnienia przez kandydata.
Za pomocą tokenu w access_tokens sprawdzamy, czy kandydat ma dostęp do testu, wyświetlamy pytania zgodnie z testem.
Jeśli w pytanie jest answer_type:
    - text,    to pole odpowiedzi ma być wyświetlana w formie pola input
    - boolean, to pole odpowiedzi ma być wyświetlana w formie 2 checkboxów (Tak/Nie)
    - scale,   to pole odpowiedzi ma być wyświetlana w formie suwaka (0-5)
    - salary,  to pole odpowiedzi ma być wyświetlana w formie 2 pól input (min. i max.)
    - date,    to pole odpowiedzi ma być wyświetlana w formie pola input
    - ABCDEF,    to pole odpowiedzi ma być wyświetlana w formie 4 radiobuttonów (A, B, C, D, E, F)
Na końcu testu powinien być przycisk "Zakończ test". 
Po kliknięciu powinien być widoczny komunikat "Dziękujemy za wypełnienie testu".
Zakończenie testu powinno zapisać wynik do tabeli candidate_answers, obliczyć wynik testu, sprawdzić czy przekroczył próg zaliczenia.

