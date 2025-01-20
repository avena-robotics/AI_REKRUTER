import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Optional
from common.logger import Logger

class EmailService:
    """Serwis do wysyłania wiadomości email"""
    
    def __init__(self, config):
        self.config = config
        self.logger = Logger.instance()

    def send_interview_invitation(
        self,
        to_email: str,
        subject: str,
        content: str,
        campaign_title: str
    ) -> bool:
        """
        Wysyła zaproszenie na rozmowę kwalifikacyjną
        
        Args:
            to_email: Adres email kandydata
            subject: Temat wiadomości
            content: Treść wiadomości HTML
            campaign_title: Tytuł kampanii rekrutacyjnej
            
        Returns:
            bool: True jeśli wysłano pomyślnie, False w przypadku błędu
        """
        try:
            msg = MIMEMultipart()
            msg['From'] = self.config.SENDER_EMAIL
            msg['To'] = to_email
            msg['Subject'] = subject or f"Zaproszenie na rozmowę kwalifikacyjną - {campaign_title}"

            # If content is empty, use default template
            if not content:
                content = f"""
                Szanowna Pani / Szanowny Panie,

                Z przyjemnością zapraszamy na rozmowę kwalifikacyjną w ramach rekrutacji na stanowisko {campaign_title}.

                Prosimy o kontakt w celu ustalenia dogodnego terminu spotkania.

                Z poważaniem,
                Zespół Rekrutacji
                """

            msg.attach(MIMEText(content, 'html'))

            with smtplib.SMTP(self.config.SMTP_SERVER, self.config.SMTP_PORT) as server:
                server.starttls()
                server.login(self.config.SMTP_USERNAME, self.config.SMTP_PASSWORD)
                server.send_message(msg)
                
            self.logger.info(f"Pomyślnie wysłano zaproszenie na rozmowę do {to_email}")
            return True
            
        except Exception as e:
            self.logger.error(f"Błąd podczas wysyłania zaproszenia na rozmowę do {to_email}: {str(e)}")
            return False

    def send_test_invitation(
        self,
        to_email: str,
        stage_name: str,
        campaign_title: str,
        test_url: str,
        expiry_date: str,
        test_details: Optional[Dict] = None
    ) -> bool:
        """
        Wysyła zaproszenie na test do kandydata
        """
        subject = f"Zaproszenie do kolejnego etapu rekrutacji - {campaign_title}"
        
        content = [
            "Szanowna Pani / Szanowny Panie,",
            "",
            "Z przyjemnością informujemy o pomyślnym przejściu poprzedniego etapu rekrutacji.",
            f"Zapraszamy do udziału w kolejnym etapie: {stage_name}.",
            "",
        ]
        
        if test_details and test_details.get('time_limit_minutes'):
            content.extend([
                "INFORMACJE O TEŚCIE",
                "━━━━━━━━━━━━━━━━━━━━━",
                f"• Czas trwania: {test_details['time_limit_minutes']} minut",
                "• Test należy wykonać w jednej sesji",
                "• System automatycznie zakończy test po upływie czasu",
                ""
            ])

        content.extend([
            "PRZYGOTOWANIE I INSTRUKCJA",
            "━━━━━━━━━━━━━━━━━━━━━",
            "• Zapewnij stabilne połączenie internetowe",
            "• Przygotuj spokojne miejsce do pracy",
            "• Odpowiedz na wszystkie pytania",
            "• Zatwierdź test przyciskiem 'Zakończ test'",
            "",
            "LINK DO TESTU",
            "━━━━━━━━━━━━━━━━━━━━━",
            test_url,
            f"Link aktywny do: {expiry_date}",
            "",
            "W razie problemów technicznych: praca@pomagier.info",
            "",
            "Życzymy powodzenia!",
            "",
            "Z poważaniem,",
            "Zespół Rekrutacji"
        ])
        
        return self.send_email(to_email, subject, "\n".join(content))


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