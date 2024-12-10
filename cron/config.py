import os
import sys
import logging
from dotenv import load_dotenv

class Config:
    """Konfiguracja aplikacji na podstawie zmiennych środowiskowych"""
    def __init__(self):
        env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
        load_dotenv(env_path)
        
        # Supabase Configuration
        self.SUPABASE_URL = os.getenv('SUPABASE_URL')
        self.SUPABASE_KEY = os.getenv('SUPABASE_KEY')
        
        # SMTP Configuration
        self.SMTP_SERVER = os.getenv('SMTP_SERVER')
        self.SMTP_PORT = int(os.getenv('SMTP_PORT'))
        self.SMTP_USERNAME = os.getenv('SMTP_USERNAME')
        self.SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')
        self.SENDER_EMAIL = os.getenv('SENDER_EMAIL')
        self.BASE_URL = os.getenv('BASE_URL')
        
        # Logging Configuration
        self.LOG_DIR = os.getenv('LOG_DIR')
        self.LOG_RETENTION_DAYS = int(os.getenv('LOG_RETENTION_DAYS'))
        self.LOG_FILE = "log_cron.log"
        
        # Debug Mode
        self.DEBUG_MODE = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
        
        # OpenAI Configuration
        self.OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
        
        # Create log directory if it doesn't exist
        os.makedirs(self.LOG_DIR, exist_ok=True)
        
        if not all([
            self.SUPABASE_URL, 
            self.SUPABASE_KEY,
            self.SMTP_SERVER,
            self.SMTP_PORT,
            self.SMTP_USERNAME,
            self.SMTP_PASSWORD,
            self.SENDER_EMAIL,
            self.BASE_URL,
            self.LOG_DIR,
            self.LOG_FILE,
            self.LOG_RETENTION_DAYS
        ]):
            logging.error("Brak wymaganych zmiennych środowiskowych")
            sys.exit(1)