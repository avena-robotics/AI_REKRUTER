import logging
import os
import sys
from dotenv import load_dotenv
from datetime import timedelta

load_dotenv()

class Config:
    # Supabase Configuration
    SUPABASE_URL = os.getenv('SUPABASE_URL')
    SUPABASE_KEY = os.getenv('SUPABASE_KEY')
    
    # SMTP Configuration
    SMTP_SERVER = os.getenv('SMTP_SERVER')
    SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))  # Convert to int with default
    SMTP_USERNAME = os.getenv('SMTP_USERNAME')
    SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')
    SENDER_EMAIL = os.getenv('SENDER_EMAIL')
    BASE_URL = os.getenv('BASE_URL')
    
    # LDAP Configuration
    LDAP_SERVER = os.getenv('LDAP_SERVER')
    LDAP_SERVICE_USER = os.getenv('LDAP_SERVICE_USER')
    LDAP_SERVICE_PASSWORD = os.getenv('LDAP_SERVICE_PASSWORD')
    LDAP_BASE_DN = os.getenv('LDAP_BASE_DN')
    
    # Session Configuration
    SECRET_KEY = os.getenv('SECRET_KEY')
    SESSION_TYPE = os.getenv('SESSION_TYPE', 'filesystem')
    SESSION_PERMANENT = os.getenv('SESSION_PERMANENT', 'True').lower() == 'true'
    PERMANENT_SESSION_LIFETIME = timedelta(seconds=int(os.getenv('PERMANENT_SESSION_LIFETIME', 86400)))
    
    # Logging Configuration
    LOG_DIR = os.getenv('LOG_DIR')
    LOG_RETENTION_DAYS = int(os.getenv('LOG_RETENTION_DAYS'))
    LOG_FILE = "log_flask.log"
    
    # Debug Mode
    DEBUG_MODE = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'

    # Create log directory if it doesn't exist
    os.makedirs(LOG_DIR, exist_ok=True)
    
    # OpenAI Configuration
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    
    if not all([
        SUPABASE_URL, 
        SUPABASE_KEY, 
        SMTP_SERVER, 
        SMTP_PORT, 
        SMTP_USERNAME, 
        SMTP_PASSWORD, 
        SENDER_EMAIL, 
        BASE_URL, 
        LDAP_SERVER, 
        LDAP_SERVICE_USER, 
        LDAP_SERVICE_PASSWORD, 
        LDAP_BASE_DN, 
        SECRET_KEY, 
        SESSION_TYPE, 
        SESSION_PERMANENT, 
        PERMANENT_SESSION_LIFETIME, 
        LOG_DIR, 
        LOG_RETENTION_DAYS, 
        LOG_FILE, 
        DEBUG_MODE, 
        OPENAI_API_KEY
    ]):
        logging.error("Brak wymaganych zmiennych środowiskowych")
        sys.exit(1)