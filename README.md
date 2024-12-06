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
SUPABASE_URL="your_supabase_url"
SUPABASE_KEY="your_supabase_key"

# SMTP Configuration
SMTP_SERVER="your_smtp_server"
SMTP_PORT="587"
SMTP_USERNAME="your_smtp_username"
SMTP_PASSWORD="your_smtp_password"
SENDER_EMAIL="your_sender_email"
BASE_URL="http://localhost:5000"

# Flask Configuration
FLASK_DEBUG=True

# LDAP Configuration
LDAP_SERVER="your_ldap_server"
LDAP_SERVICE_USER="your_ldap_user"
LDAP_SERVICE_PASSWORD="your_ldap_password"
LDAP_BASE_DN="your_ldap_base_dn"

# Session Configuration
SECRET_KEY="your_generated_secret_key"  # Wygeneruj używając: python -c "import secrets; print(secrets.token_hex(32))"
SESSION_TYPE="filesystem"
SESSION_PERMANENT=True
PERMANENT_SESSION_LIFETIME=86400  # 24 hours in seconds

# Logging Configuration
LOG_DIR="/path/to/logs"
LOG_FILE="log_cron.log"
LOG_RETENTION_DAYS=7
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
