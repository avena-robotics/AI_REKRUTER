import os
import sys
import logging
from supabase import create_client

from .config import Config
from .logger import LogManager
from .services.email_service import EmailService
from .services.test_service import TestService
from .services.candidate_service import CandidateService

def main():
    """Główna funkcja skryptu sprawdzająca i aktualizująca statusy kandydatów"""
    try:
        # Inicjalizacja konfiguracji
        config = Config()
        
        # Konfiguracja logowania
        log_manager = LogManager('cron/candidate_check.log', config.DEBUG_MODE)
        log_manager.cleanup_old_logs()
        
        logger = logging.getLogger('candidate_check')
        logger.info("Rozpoczęcie procesu sprawdzania kandydatów")
        
        # Inicjalizacja klienta Supabase
        supabase = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)
        
        # Inicjalizacja serwisów
        email_service = EmailService(config)
        test_service = TestService(supabase)
        candidate_service = CandidateService(
            supabase, 
            config, 
            email_service, 
            test_service
        )
        
        # Aktualizacja kandydatów
        candidate_service.update_candidates()
        
        logger.info("Zakończenie procesu sprawdzania kandydatów")
        
    except Exception as e:
        logger.error(f"Wystąpił krytyczny błąd: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 