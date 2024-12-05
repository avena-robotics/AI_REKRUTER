
# Uruchomienie aplikacji

Utwórz nową sesję `screen` i uruchom następujące polecenie:
```bash
screen -S flask_app
```

W sesji `flask_app` przejdź do katalogu głównego projektu i uruchom następujące polecenie:
```bash
cd ~/AI_REKRUTER/app
gunicorn -c gunicorn.conf.py app:app
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
