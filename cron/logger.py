import os
import logging
from datetime import datetime, timedelta

class LogManager:
    """Zarządza logowaniem i przechowywaniem logów aplikacji"""
    
    def __init__(self, config):
        self.config = config
        self.log_path = os.path.join(self.config.LOG_DIR, self.config.LOG_FILE)
        self.setup_logger()
        
    def cleanup_old_logs(self) -> None:
        """Usuwa stare logi starsze niż określona liczba dni"""
        if not os.path.exists(self.log_path):
            return

        try:
            cutoff_date = datetime.now() - timedelta(days=self.config.LOG_RETENTION_DAYS)
            
            with open(self.log_path, 'r', encoding='utf-8') as file:
                logs = file.readlines()

            recent_logs = []
            for log in logs:
                try:
                    log_date_str = log.split(' - ')[0].strip()
                    log_date = datetime.strptime(log_date_str, '%Y-%m-%d %H:%M:%S,%f')
                    
                    if log_date >= cutoff_date:
                        recent_logs.append(log)
                except (ValueError, IndexError):
                    recent_logs.append(log)

            with open(self.log_path, 'w', encoding='utf-8') as file:
                file.writelines(recent_logs)

            print(f"Wyczyszczono stare logi z pliku: {self.log_path}")
            print(f"Usunięto {len(logs) - len(recent_logs)} wpisów starszych niż {self.config.LOG_RETENTION_DAYS} dni")
            
        except Exception as e:
            print(f"Błąd podczas czyszczenia logów: {str(e)}")

    def setup_logger(self) -> None:
        """Konfiguruje system logowania do pliku i konsoli"""
        logger = logging.getLogger('candidate_check')
        logger.setLevel(logging.DEBUG if self.config.DEBUG_MODE else logging.WARNING)

        logger.handlers = []

        # Logger do pliku
        file_handler = logging.FileHandler(self.log_path)
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(file_formatter)

        # Logger do konsoli
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG if self.config.DEBUG_MODE else logging.WARNING)
        console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(console_formatter)

        logger.addHandler(file_handler)
        logger.addHandler(console_handler) 