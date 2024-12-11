import smtplib
from logger import Logger
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import Config

class EmailService:
    """Serwis do wysyłania wiadomości email"""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = Logger.instance()

    def send_email(self, to_email: str, subject: str, body: str) -> bool:
        """
        Wysyła email do kandydata
        
        Args:
            to_email: Adres email odbiorcy
            subject: Temat wiadomości 
            body: Treść wiadomości
            
        Returns:
            bool: True jeśli wysłano pomyślnie, False w przypadku błędu
        """
        try:
            msg = MIMEMultipart()
            msg['From'] = self.config.SENDER_EMAIL
            msg['To'] = to_email
            msg['Subject'] = subject

            msg.attach(MIMEText(body, 'plain'))

            with smtplib.SMTP(self.config.SMTP_SERVER, self.config.SMTP_PORT) as server:
                server.starttls()
                server.login(self.config.SMTP_USERNAME, self.config.SMTP_PASSWORD)
                server.send_message(msg)
                
            self.logger.info(f"Pomyślnie wysłano email do {to_email}")
            return True
            
        except Exception as e:
            self.logger.error(f"Błąd podczas wysyłania emaila do {to_email}: {str(e)}")
            return False 