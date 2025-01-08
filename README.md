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