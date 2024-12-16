import logging
import os
import sys
from dotenv import load_dotenv
from datetime import timedelta
from typing import Optional

class Config:
    """Konfiguracja aplikacji na podstawie zmiennych środowiskowych"""
    
    _instance: Optional['Config'] = None
    
    def __new__(cls) -> 'Config':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        # Skip initialization if already done
        if getattr(self, '_initialized', False):
            return
            
        self._initialized = True
        
        # Load environment variables
        env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
        load_dotenv(env_path)
        
        # Supabase Configuration
        self.SUPABASE_URL = os.getenv('SUPABASE_URL')
        self.SUPABASE_KEY = os.getenv('SUPABASE_KEY')
        
        # SMTP Configuration
        self.SMTP_SERVER = os.getenv('SMTP_SERVER')
        self.SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
        self.SMTP_USERNAME = os.getenv('SMTP_USERNAME')
        self.SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')
        self.SENDER_EMAIL = os.getenv('SENDER_EMAIL')
        self.BASE_URL = os.getenv('BASE_URL')
        
        # LDAP Configuration
        self.LDAP_SERVER = os.getenv('LDAP_SERVER')
        self.LDAP_SERVICE_USER = os.getenv('LDAP_SERVICE_USER')
        self.LDAP_SERVICE_PASSWORD = os.getenv('LDAP_SERVICE_PASSWORD')
        self.LDAP_BASE_DN = os.getenv('LDAP_BASE_DN')
        
        # Session Configuration
        self.SECRET_KEY = os.getenv('SECRET_KEY')
        self.SESSION_TYPE = os.getenv('SESSION_TYPE', 'filesystem')
        self.SESSION_PERMANENT = os.getenv('SESSION_PERMANENT', 'True').lower() == 'true'
        self.PERMANENT_SESSION_LIFETIME = timedelta(seconds=int(os.getenv('PERMANENT_SESSION_LIFETIME', 86400)))
        
        # Logging Configuration
        self.LOG_DIR = os.getenv('LOG_DIR')
        self.LOG_RETENTION_DAYS = int(os.getenv('LOG_RETENTION_DAYS'))
        self.LOG_FILE = "log_flask.log"
        
        # Debug Mode
        self.DEBUG_MODE = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
        
        # OpenAI Configuration
        self.OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

        # Create log directory if it doesn't exist
        os.makedirs(self.LOG_DIR, exist_ok=True)
        
        # Debug log all configuration values
        self._log_config_values()
        
        # Validate configuration
        self._validate_config()
    
    def _log_config_values(self):
        """Log all configuration values for debugging"""
        logging.debug("Configuration values:")
        logging.debug(f"SUPABASE_URL: {self.SUPABASE_URL}")
        logging.debug(f"SUPABASE_KEY: {self.SUPABASE_KEY}")
        logging.debug(f"SMTP_SERVER: {self.SMTP_SERVER}")
        logging.debug(f"SMTP_PORT: {self.SMTP_PORT}")
        logging.debug(f"SMTP_USERNAME: {self.SMTP_USERNAME}")
        logging.debug(f"SMTP_PASSWORD: {'*' * 8 if self.SMTP_PASSWORD else None}")
        logging.debug(f"SENDER_EMAIL: {self.SENDER_EMAIL}")
        logging.debug(f"BASE_URL: {self.BASE_URL}")
        logging.debug(f"LOG_DIR: {self.LOG_DIR}")
        logging.debug(f"LOG_FILE: {self.LOG_FILE}")
        logging.debug(f"LOG_RETENTION_DAYS: {self.LOG_RETENTION_DAYS}")
        logging.debug(f"DEBUG_MODE: {self.DEBUG_MODE}")
        logging.debug(f"OPENAI_API_KEY: {'*' * 8 if self.OPENAI_API_KEY else None}")
    
    def _validate_config(self):
        """Validate that all required configuration values are present"""
        required_values = [
            self.SUPABASE_URL,
            self.SUPABASE_KEY,
            self.SMTP_SERVER,
            self.SMTP_PORT,
            self.SMTP_USERNAME,
            self.SMTP_PASSWORD,
            self.SENDER_EMAIL,
            self.BASE_URL,
            self.LDAP_SERVER,
            self.LDAP_SERVICE_USER,
            self.LDAP_SERVICE_PASSWORD,
            self.LDAP_BASE_DN,
            self.SECRET_KEY,
            self.SESSION_TYPE,
            self.SESSION_PERMANENT,
            self.PERMANENT_SESSION_LIFETIME,
            self.LOG_DIR,
            self.LOG_RETENTION_DAYS,
            self.LOG_FILE,
            self.DEBUG_MODE,
            self.OPENAI_API_KEY
        ]
        
        if not all([True for value in required_values if value is not None]):
            self._log_config_values()
            logging.error("Brak wymaganych zmiennych środowiskowych")
            sys.exit(1)
    
    @classmethod
    def instance(cls) -> 'Config':
        """Get singleton instance of Config"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance