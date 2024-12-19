import sys
import os
from supabase import create_client

# Add the cron directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from common.config import Config
from common.email_service import EmailService
from services.test_service import TestService
from services.candidate_service import CandidateService
from common.openai_service import OpenAIService

from common.logger import Logger

def main():
    """Główna funkcja skryptu sprawdzająca i aktualizująca statusy kandydatów"""
    try:
        # Initialize configuration
        config = Config.instance()
    
        # Initialize logger singleton
        logger = Logger.instance(config, logFile='cron_app.log')
        logger.info("====== Starting new candidate check session ======")
        
        # Clean up old logs
        logger.info("Cleaning up old logs")
        logger.cleanup_old_logs()
        
        # Initialize Supabase client
        logger.debug("Initializing Supabase database connection")
        supabase = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)
        
        # Initialize services
        logger.debug("Initializing email service")
        email_service = EmailService(config)
        
        logger.debug("Initializing OpenAI service")
        openai_service = OpenAIService(config)
        
        logger.debug("Initializing test service")
        test_service = TestService(supabase, openai_service)
        
        logger.debug("Initializing candidate service")
        candidate_service = CandidateService(
            supabase,
            config,
            email_service,
            test_service,
        )
        
        # Update candidates
        logger.info("Starting candidate status updates")
        candidate_service.update_candidates()
        
        logger.info("====== Candidate check session completed ======")
        
    except Exception as e:
        logger = Logger.instance()  # Get logger instance without config
        logger.critical(f"Critical error occurred during script execution: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main() 