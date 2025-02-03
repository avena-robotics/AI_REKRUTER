# Uruchomienie aplikacji

Utwórz nową sesję `screen` i uruchom następujące polecenie:
```bash
screen -S flask_app
```

W sesji `flask_app` przejdź do katalogu głównego projektu i uruchom następujące polecenie:
```bash
cd ~/AI_REKRUTER/app

# w środowisku produkcyjnym
gunicorn -c gunicorn.conf.py app:app
# w środowisku developerskim
gunicorn --reload -c gunicorn.conf.py app:app
```

# Konfiguracja środowiska

## Plik .env

Plik `.env` powinien zostać utworzony w głównym katalogu projektu (na tym samym poziomie co folder `app/`).

Struktura pliku `.env`:

```env
# Supabase Configuration
SUPABASE_URL="your_supabase_url"             # URL do lokalnej instancji Supabase
SUPABASE_KEY="your_supabase_key"             # Klucz dostępu do Supabase (service_role key)

# SMTP Configuration
SMTP_SERVER="smtp.office365.com"             # Adres serwera SMTP
SMTP_PORT="587"                              # Port SMTP (domyślnie 587 dla TLS)
SMTP_USERNAME="your_smtp_username"           # Nazwa użytkownika SMTP
SMTP_PASSWORD="your_smtp_password"           # Hasło SMTP
SENDER_EMAIL="your_sender_email"             # Adres email nadawcy
BASE_URL="https://your.domain.com"           # Bazowy URL aplikacji

# Flask Configuration
FLASK_DEBUG=True                             # Tryb debugowania (True/False)

# LDAP Configuration
LDAP_SERVER="ldaps://your.ldap.server"       # Adres serwera LDAP (z protokołem ldaps://)
LDAP_SERVICE_USER="CN=user,DC=domain"        # Pełna ścieżka DN użytkownika serwisowego
LDAP_SERVICE_PASSWORD="your_ldap_password"    # Hasło użytkownika serwisowego
LDAP_BASE_DN="DC=domain,DC=local"            # Bazowy DN dla wyszukiwania

# Session Configuration
# Wygeneruj używając: python -c "import secrets; print(secrets.token_hex(32))"
SECRET_KEY="your_generated_secret_key"        # Klucz szyfrowania sesji
SESSION_TYPE="filesystem"                     # Typ przechowywania sesji
SESSION_PERMANENT=True                        # Czy sesja ma być permanentna
PERMANENT_SESSION_LIFETIME=86400              # Czas życia sesji w sekundach (24h)

# Logging Configuration
LOG_DIR="/path/to/logs"                      # Ścieżka do katalogu z logami
LOG_RETENTION_DAYS=7                         # Liczba dni przechowywania logów

# OpenAI Configuration
OPENAI_API_KEY="your_openai_api_key"
```

## Uruchamianie crona z użyciem venv

Aby uruchomić skrypt cron z użyciem środowiska wirtualnego (venv), wykonaj następujące kroki:

1. Upewnij się, że masz utworzone środowisko wirtualne w projekcie:
   ```bash
   python3 -m venv /home/avena/AI_REKRUTER/venv
   ```

2. Dodaj wpis do crontab, aby uruchamiać skrypt z użyciem Pythona z venv:
   ```bash
   crontab -e
   ```

3. Dodaj następujący wpis, aby uruchamiać skrypt co minutę:
   ```cron
   * * * * * /home/avena/AI_REKRUTER/venv/bin/python /home/avena/AI_REKRUTER/cron/main.py
   ```

4. Upewnij się, że wszystkie wymagane pakiety są zainstalowane w venv:
   ```bash
   source /home/avena/AI_REKRUTER/venv/bin/activate
   pip install -r /home/avena/AI_REKRUTER/requirements.txt
   ```

5. Sprawdź logi, aby upewnić się, że cron działa poprawnie:
   ```bash
   tail -f /home/avena/AI_REKRUTER/logs/cron/log_cron.log
   ```

# Komendy `screen`

1. **Uruchomienie nowej sesji:**
   ```bash
   screen
   ```
2. **Tworzenie nowej sesji z nazwą:**
   ```bash
   screen -S <nazwa>
   ```

3. **Wyświetlenie listy aktywnych sesji:**
   ```bash
   screen -ls
   ```

4. **Dołączenie do sesji:**
   ```bash
   screen -r <nazwa>
   ```

5. **Rozłączenie od sesji:**
   ```bash
   Ctrl + A + D
   ```

6. **Zabicie bieżącego okna:**
   ```bash
   Ctrl + A + K
   ```

7. **Uruchomienie sesji w tle:**
   ```bash
   screen -S <nazwa> -d -m
   ```

8. **Zakończenie sesji:**
   ```bash
   exit
   ```

9. **Usuwanie sesji screen:**
   ```bash
   # Najpierw wyświetl listę sesji
   screen -ls
   
   # Usuń konkretną sesję (zastąp [numer_sesji] numerem z listy)
   screen -X -S [numer_sesji] quit
   
   # Lub usuń wszystkie martwe sesje
   screen -wipe
   ```

# Backup i przywracanie bazy danych Supabase

## Wykonywanie kopii zapasowej

Aby wykonać pełną kopię zapasową struktury i danych bazy:

```bash
pg_dump -U postgres -h 127.0.0.1 -p 54322 -F c -b -v -f backup.dump postgres
```

Parametry:
- `-F c`: Tworzy kopię w formacie zarchiwizowanym
- `-b`: Zawiera obiekty binarne (np. dane w formacie bytea)
- `-v`: Włącza tryb szczegółowy (verbose)
- `-f backup.dump`: Ścieżka do pliku wyjściowego

### Automatyczne kopie zapasowe (cron)

Aby skonfigurować automatyczne wykonywanie kopii zapasowych:

1. Otwórz edytor crontab:
```bash
crontab -e
```

2. Dodaj następującą linię, aby wykonywać backup codziennie o 3:00 rano:
```bash
0 3 * * * PGPASSWORD='postgres' pg_dump -U postgres -h 127.0.0.1 -p 54322 postgres > /sciezka/do/backupow/backup_$(date +\%F_\%H-\%M-\%S).sql
```

Format nazwy pliku `backup_$(date +\%F_\%H-\%M-\%S).sql` zawiera datę i godzinę wykonania kopii, np. `backup_2024-03-20_03-00-00.sql`.

Parametry crona `0 3 * * *` oznaczają:
- `0` - minuta (0-59)
- `3` - godzina (0-23)
- `*` - dzień miesiąca (1-31)
- `*` - miesiąc (1-12)
- `*` - dzień tygodnia (0-6, gdzie 0 to niedziela)

Logi crona można sprawdzić w pliku `/var/log/syslog`.

Parametry:
- `-F c`: Tworzy kopię w formacie zarchiwizowanym
- `-b`: Zawiera obiekty binarne (np. dane w formacie bytea)
- `-v`: Włącza tryb szczegółowy (verbose)
- `-f backup.dump`: Ścieżka do pliku wyjściowego

## Przywracanie bazy danych

### Standardowe przywracanie

```bash
pg_restore -U postgres -h 127.0.0.1 -p 54322 -d postgres --disable-triggers -v backup.dump
```

### Pełne przywrócenie z nadpisaniem

1. Usuń starą bazę i utwórz nową:
```bash
dropdb -U postgres -h 127.0.0.1 -p 54322 postgres
createdb -U postgres -h 127.0.0.1 -p 54322 postgres
```

2. Przywróć bazę z opcją nadpisania:
```bash
pg_restore -U postgres -h 127.0.0.1 -p 54322 -d postgres --clean --disable-triggers -v backup.dump
```

Parametry:
- `--clean`: Usuwa istniejące obiekty przed przywróceniem
- `--disable-triggers`: Wyłącza wyzwalacze na czas przywracania
- `-v`: Tryb szczegółowy dla lepszego debugowania

"""
Wchodzac pierwszy raz opjawi sie nam ekran logowania, w ktorym wykorzystujemy logowanie jak do emaila firmowoge (LDAP) lub dowolone email dodany przez adminstratora z haslem przez niego nadanym. W celu pomocy trzeba odezwac sie do ai_rekruter@pomagier.info lub sebastian.krajna@pomagier.info. 

Po poprawnym logowaniu widzimy w panelu bocznym 3 sekcje. 
Kampanie rekrutacyjne
Zarządzaj kampaniami rekrutacyjnymi, twórz testy i ankiety.

Kandydaci
Przeglądaj i zarządzaj kandydatami w procesie rekrutacji.

Szablony testów
Zarządzaj bazą szablonów testów i pytań dla kampanii rekrutacyjnych.

Widzimy rowniez przycisk wylogowania oraz grup do ktorych nalezymy. Kazdy uzytkownik musi zostac przypisane przez administratora do grupy, w ktorej moze tworzyc odpowiednie testy i kampanie. Nie bedzie on mial mozliwosci podgladu oraz edycji testow ktore przypisane sa do grupy do ktorej on nie nalezy. 

Przechodzac do testow mamy opcje takie jak 'dodaj szablon testu' panel filtracji w ktorej mozemy wybrac jaki typ testu bedzie widoczny w liscie oraz z jakiej grupy testy maja byc widoczne. 

W liscie wyswietlaja sie nam takie kolumny:
#(numer w liscie)	Tytuł	"Typ testu"	"Limit czasu"	"Liczba pytań"	"Suma punktów"	"Próg zaliczenia"	"Grupy"	"Data utworzenia"	"Akcje(edycja, usuwanie, duplikacja)"

Przy tworzeniu szablonu musimy uzupelnc pola takie jak:
Tytuł testu* (Wewnętrzna identyfikacja testu)
Typ testu*
Ankieta
Opis testu (Opis wyświetlany na stronie testu dla kandydata)
Próg zaliczenia* (Ustaw wartość 0, aby test był traktowany jako bez progu)
Limit czasu (minuty, Ustaw wartość 0, aby test był traktowany jako bez limitu czasu)
Grupy*

oraz dodać pytania do testu.

Mamy 4 typy testow:
1. Ankieta - Pytania o imie, naziwsko, numer telefonu, email sa zawsze odgrodnie dodawane do ankiety. Mozna dodac dodatkowe pytania ogolne do kandydata np. wynagrodzenie, dosiwadczenie, wyksztalcenie, prawo jazdy, etc.
2. Test EQ - polega na tym, ze jest 7 sekcji po 8 stwierdzen w kazdej. Kandydat ma 10 punktow do rozdysponowania w kazdej sekcji. Punkty te sa zliczane wg tabeli 
            'Sekcja': ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII']
            'KO': ['d', 'b', 'a', 'h', 'f', 'c', 'g'],
            'RE': ['g', 'a', 'h', 'd', 'b', 'f', 'e'],
            'W':  ['f', 'e', 'c', 'b', 'd', 'g', 'a'],
            'IN': ['c', 'g', 'd', 'e', 'h', 'a', 'f'],
            'PZ': ['a', 'c', 'f', 'g', 'e', 'h', 'd'],
            'KZ': ['h', 'd', 'g', 'c', 'a', 'e', 'b'],
            'DZ': ['b', 'f', 'e', 'a', 'c', 'b', 'h'],
            'SW': ['e', 'h', 'b', 'f', 'g', 'd', 'c']
        
3. Ocena EQ - Jest to specjalny test przygotowany po to, aby wydobyc kandydata o opowiednich dla naszych potrzeb cechach. Np mozemy ograniczyc ze kandydat ma miec KO pomiedzy 10 a 15.
4. TEST IQ - Jest to test z pytaniami w ktorym trzeba wybrac odpowiedni obrazek z 6 mozliwosci, ktory pasuje do schematu.


Do kazdego pytania musimy dodac tresc oraz zaznaczyc czy jest wymagane pytanie czy nie.
Opcjonalnie mozemy dodac obrazek do pytania.
Ustawiamy maksymalna liczbe punktów jakie mozna uzyskac za pytanie.
Wybieramy typ odpowiedzi dla pytania.
W tworzonych pytaniach mamy 8 mozliwosci typow odpowiedzi:
- tekst
- tak/nie
- skala (0-5)
- wynagrodzenie 
- data
- abcdef 
- liczba 
- punkty a-h (typ dostepny tylko dla testu EQ)

W zaleznosci od typu odpowiedzi mamy różne opcje algorytmu punktacji.
- tekst (brak algorytmu, dokładne dopasowanie odpowiedzi, ocena odpowiedzi przez AI)
- tak/nie (brak algorytmu, dokładne dopasowanie odpowiedzi)
- skala (brak algorytmu, lewostronny, prawstronny, srodkowy, przedzial)
- wynagrodzenie (brak algorytmu, lewostronny, prawstronny, srodkowy, przedzial)
- data (brak algorytmu, lewostronny, prawstronny, srodkowy, przedzial)
- abcdef (brak algorytmu, dokładne dopasowanie odpowiedzi)
- liczba (brak algorytmu, lewostronny, prawstronny, srodkowy, przedzial)
- punkty a-h (domyślnie brak algorytmu, bo ocenia te odpowiedzi test 'OCENA EQ' a nie algorytm. Dlatego wybierajac ten typ odpowiedi trzeba do a,b,c,d,e,f,g,h wpisac tresc)

Jak dzalaja algorytmu:
- Brak algorytmu - Odpowiedź nie jest oceniana.
- Dokładne dopasowanie odpowiedzi - Punkty przyznawane tylko za dokładnie poprawną odpowiedź.
- Ocena odpowiedzi przez AI - Ocena przez sztuczną inteligencję na podstawie zdefiniowanych kryteriów. Musimy uzupelnic Na co zwrócić uwagę w odpowiedzi (Opisz algorytm oceny odpowiedzi) oraz Kryteria przyznawania punktów (Opisz, jak powinny być przyznawane punkty za poszczególne elementy odpowiedzi)
- Przedzial - Punkty przyznawane, jeśli odpowiedź mieści się w określonym przedziale (musimy uzupelnic wartosc miniamlna i wartosc maksymalna. Krance sa wliczane jako prawidlowa odpowiedz)
- Lewostronny - Im bliżej minimalnej wartości, tym mniej punktów. Wartości większe lub równe poprawnej odpowiedzi to maksymalna liczba punktów. (musimy uzupelnic wartosc minimalna i poprawna odpowiedz)
- Prawostronny - Im bliżej maksymalnej wartości, tym mniej punktów. Wartości mniejsze lub równe poprawnej odpowiedzi to maksymalna liczba punktów. (musimy uzupelnic wartosc maksymalna i poprawna odpowiedz)
- Srodkowy - Maksymalna liczba punktów za dokładne dopasowanie odpowiedzi, punkty maleją proporcjonalnie wraz oddaleniem od poprawnej odpowiedzi. (musimy uzupelnic wartosc minimalna i maksymalna, poprawna odpowiedz)




Przechodzac do kampanii widzimy liste kampanii.

W liscie wyswietlaja sie nam takie kolumny:
#(numer kampani w liscie)	Kod	Tytuł	Lokalizacja	Status	Testy	"Data utworzenia"	Akcje(edycja, duplikacja, usuwanie)

Mozemy dodac kampanie rekrutacyjna za pomoca przycisku 'dodaj kampanie'
Mozemy ustawic status kampanii rekrutacyjnej na 'aktywna' lub 'nieaktywna', tak aby kandydaci nie mogli sie do niej dolaczyc.

Ustawiamy kod kampanii do wewnetrznej identyfikacji kampanii.
Ustawiamy tytul kampanii rekrutacyjnej.
Ustawiamy lokalizacje kampanii rekrutacyjnej, miejsce gdzie kandydaci beda rekrutowani. 
Ustawiamy porzadana przez nas date rozpoczecia pracy.

Ustawiamy typ umowy, wymiar pracy, wynagrodzenie od, do (netto pln)

Uzupełniamy szczegoly stanowiska(obowiazki, wymagnaia, co oferujemy, opis stanowiska) - jest to sekcja ktora bedzie przekopiowana do pracuj.pl 

Uzuppelniamy szablon zaproszenia na rozmowe kwalifikacyjna. Przy wyslaniu zaproszenia bedzie mozliwosc modyfikacji szablonu. UStawiamy tytul i tresc.

Wybieramy odpowiednia grupe do ktorej przypisujemy kampanie rekrutacyjna oraz z ktorej grupy beda brane testy. 
Uzupelniamy odpowiedni ankiete, test eq, ocene eq, test iq. Ustawiamy w odpowiednia miejsca wage. Waga jest potrzebna po to, aby zaznaczyc jak bardzo wynik danego testu ma wplywac na wynik ogolny kandydata. Mozemy rowniez ustawic przy tescie eq i tescie iq jak dlugo ma byc dostepny link wygenerowany dla kandydata. 

Po stworzeniu kampanii rekrutacyjnej mozemy wygenerowac link do kampanii rekrutacyjnej. Link ten bedzie mozliwosc udostepnienia kandydatom i jest on uniwersalny, ze kazdy moze miec do niego dostep. Nastepne linki do dalszych testow beda generowane unikalnie dla kazdego kandydata.



Przechodzac do kandydatow widzimy panel filtrcji w ktorym mozemy wyszukac kandydatow po imieniu, nazwisku, emailu, telefonie. 
Mozemy wyfiltrowac kandydatow wg kampanii rekrutacyjnej oraz statusie rekrutacji. 
Mozemy przeliczyc punkty dla kazdego kandydata w liscie. Jesli lista jest przefiltrowana to tylko dla kandydatow wyfiltrowanych zostana przeliczone punkty. 
W liscie widzimy kolumny takie jak:
#(numer kandydata w liscie)	"Imię i nazwisko"	"Kod kampanii"	"Email"	"Telefon"	"Status"	"Wynik ankiety"	"Wynik testu EQ"	"Wynik oceny EQ"	"Wynik testu IQ"	"Ocena rozmowy"	"Wynik ogólny"	"Data aplikacji"	"Akcje"

W akcjach widzimy przyciski do:
- podgladu kandydata 
- dodania notatki do kandydata
- przeliczenia punktow dla kandydata (jesli po przeliczeniu punktow kandydat zalapie sie do nastepnego etapu odpowiedni email zostanie wyslany, nawet jesli odrzucilismy go recznie)
- odrzuc - odrzucamy kandydata 
- zapros na rozmowe (wysylamy zaproszenie na rozmowe kwalifikacyjna, wyswietla sie szablon zaproszenia na rozmowe z przyciskiem do wyslania)
- oczekuje na decyzje - ustawiamy status kandydata na 'oczekuje na decyzje' abysmy nie zapomnieli ze trzeba kandydata poinformowac o decyzji
- zaakceptuj - kandydat, ktorego zaakceptowalismy i chcemy go zatrudnic
- usun aplikacje - usuwamy kandydata z listy wraz z wszystkimi danymi, wszystkie testy i ankiety zostana usuniete

Przechodzac do podgladu kandydata widzimy wszystkie informacje o kandydacie oraz wyniki testow i ankiet. Mozemy dodac notatke do kandydata oraz edytowac usuwac juz istniejace. 
Mozemy skopiowac wygenerowany link dostepu do danego testu dla kandydata. Mozemy rowniez ponownie wygenerowac token dostepu dla kandydata, jesli ktorys z jakiegos powodu wygasl. Opcja ta rowniez usunie juz wykonany test dla odpowiedniego etapu, jesli taki test istnieje. 

Pytania ocenianie sa cyklicznie przez skrypt w CRON, ktory sprawdza czy kandydat ma jakis test ktore nie zostal jeszcze oceniony. Sprawdza czy wynik kandydata jest wiekszy od progu zaliczenia. Jesli tak to wysyla odpowiednie email do kandydata z dostepem do nastepnego etapu. Gdy ktos pozytywnie zaliczy test IQ to musimy juz recznie zaprosic go na rozmowe po przejrzeniu jego kandydatury. 


"""