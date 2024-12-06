import os
from dotenv import load_dotenv
from datetime import timedelta

load_dotenv()

class Config:
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
    
    FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
