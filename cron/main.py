import sys
import os
import logging
from supabase import create_client

from logger import Logger

# Add the cron directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import Config
from services.email_service import EmailService
from services.test_service import TestService
from services.candidate_service import CandidateService
from services.openai_service import OpenAIService

def main():
    """Główna funkcja skryptu sprawdzająca i aktualizująca statusy kandydatów"""
    try:
        logger = logging.getLogger('candidate_check')
        logger.info("====== Rozpoczęcie nowej sesji sprawdzania kandydatów ======")
        
        # Inicjalizacja konfiguracji
        logger.debug("Inicjalizacja konfiguracji")
        config = Config()
        
        # Konfiguracja logowania
        logger.debug("Konfiguracja systemu logowania")
        log_manager = Logger.instance(config)
        log_manager.cleanup_old_logs()
        
        # Inicjalizacja klienta Supabase
        logger.debug("Inicjalizacja połączenia z bazą danych Supabase")
        supabase = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)
        
        # Inicjalizacja serwisów
        logger.debug("Inicjalizacja serwisu email")
        email_service = EmailService(config)
        logger.debug("Inicjalizacja serwisu OpenAI")
        openai_service = OpenAIService(config)
        logger.debug("Inicjalizacja serwisu testów")
        test_service = TestService(supabase, openai_service)
        logger.debug("Inicjalizacja serwisu kandydatów")
        candidate_service = CandidateService(
            supabase, 
            config, 
            email_service, 
            test_service
        )
        
        # Aktualizacja kandydatów
        logger.info("Rozpoczęcie aktualizacji statusów kandydatów")
        candidate_service.update_candidates()
        
        logger.info("====== Zakończenie sesji sprawdzania kandydatów ======")
        
    except Exception as e:
        logger.error(f"Wystąpił krytyczny błąd podczas wykonywania skryptu: {str(e)}")
        logger.exception("Szczegóły błędu:")
        sys.exit(1)

if __name__ == "__main__":
    logger = logging.getLogger('candidate_check')
    logger.info("Uruchomienie skryptu głównego")
    main() 