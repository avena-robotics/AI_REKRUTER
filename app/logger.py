import os
import logging
from datetime import datetime, timedelta
from typing import Optional


class Logger:
    """Singleton logger class for application-wide logging"""

    _instance: Optional["Logger"] = None
    _logger: Optional[logging.Logger] = None

    @classmethod
    def instance(cls, config=None) -> "Logger":
        """Get or create singleton instance"""
        if cls._instance is None:
            cls._instance = cls()
            cls._instance._initialize(config)
        elif config is not None:
            # Reinitialize with new config if provided
            cls._instance._initialize(config)
        return cls._instance

    def __init__(self):
        """Private constructor"""
        if Logger._instance is not None:
            raise Exception("This class is a singleton. Use Logger.instance() instead.")
        Logger._instance = self

    def _initialize(self, config) -> None:
        """Initialize logger configuration if not already initialized"""
        if config is None:
            return

        self.config = config
        self.log_path = os.path.join(self.config.LOG_DIR, self.config.LOG_FILE)
        self._setup_logger()

    def _setup_logger(self) -> None:
        """Configure logging to file and console"""
        self._logger = logging.getLogger("flask_app")
        self._logger.setLevel(logging.DEBUG if self.config.DEBUG_MODE else logging.WARNING)

        # Clear existing handlers
        self._logger.handlers = []

        # File handler
        file_handler = logging.FileHandler(self.log_path)
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        file_handler.setFormatter(file_formatter)

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG if self.config.DEBUG_MODE else logging.WARNING)
        console_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        console_handler.setFormatter(console_formatter)

        self._logger.addHandler(file_handler)
        self._logger.addHandler(console_handler)

    def cleanup_old_logs(self) -> None:
        """Remove logs older than specified number of days"""
        if not hasattr(self, "config") or not hasattr(self, "log_path"):
            raise Exception("Logger not initialized. Call Logger.instance(config) first.")

        if not os.path.exists(self.log_path):
            return

        try:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=self.config.LOG_RETENTION_DAYS)

            with open(self.log_path, "r", encoding="utf-8") as file:
                logs = file.readlines()

            recent_logs = []
            for log in logs:
                try:
                    log_date_str = log.split(" - ")[0].strip()
                    log_date = datetime.strptime(log_date_str, "%Y-%m-%d %H:%M:%S,%f")

                    if log_date >= cutoff_date:
                        recent_logs.append(log)
                except (ValueError, IndexError):
                    recent_logs.append(log)

            with open(self.log_path, "w", encoding="utf-8") as file:
                file.writelines(recent_logs)

            print(f"Cleaned old logs from file: {self.log_path}")
            print(
                f"Removed {len(logs) - len(recent_logs)} entries older than {self.config.LOG_RETENTION_DAYS} days"
            )

        except Exception as e:
            print(f"Error cleaning logs: {str(e)}")

    def debug(self, message: str) -> None:
        if self._logger is None:
            raise Exception("Logger not initialized. Call Logger.instance(config) first.")
        self._logger.debug(message)

    def info(self, message: str) -> None:
        if self._logger is None:
            raise Exception("Logger not initialized. Call Logger.instance(config) first.")
        self._logger.info(message)

    def warning(self, message: str) -> None:
        if self._logger is None:
            raise Exception("Logger not initialized. Call Logger.instance(config) first.")
        self._logger.warning(message)

    def error(self, message: str) -> None:
        if self._logger is None:
            raise Exception("Logger not initialized. Call Logger.instance(config) first.")
        self._logger.error(message)

    def critical(self, message: str) -> None:
        if self._logger is None:
            raise Exception("Logger not initialized. Call Logger.instance(config) first.")
        self._logger.critical(message) 