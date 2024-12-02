import os
import sys
import logging
from dotenv import load_dotenv

class Config:
    """Konfiguracja aplikacji na podstawie zmiennych środowiskowych"""
    def __init__(self):
        env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
        load_dotenv(env_path)
        
        self.SUPABASE_URL = os.getenv('SUPABASE_URL')
        self.SUPABASE_KEY = os.getenv('SUPABASE_KEY')
        self.SMTP_SERVER = os.getenv('SMTP_SERVER')
        self.SMTP_PORT = int(os.getenv('SMTP_PORT'))
        self.SMTP_USERNAME = os.getenv('SMTP_USERNAME')
        self.SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')
        self.SENDER_EMAIL = os.getenv('SENDER_EMAIL')
        self.BASE_URL = os.getenv('BASE_URL', 'http://localhost:5000')
        self.DEBUG_MODE = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
        
        if not all([
            self.SUPABASE_URL, 
            self.SUPABASE_KEY,
            self.SMTP_SERVER,
            self.SMTP_PORT,
            self.SMTP_USERNAME,
            self.SMTP_PASSWORD,
            self.SENDER_EMAIL,
            self.BASE_URL
        ]):
            logging.error("Brak wymaganych zmiennych środowiskowych")
            sys.exit(1)