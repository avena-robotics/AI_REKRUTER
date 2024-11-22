import os
import sys
from datetime import datetime, timedelta, timezone
import secrets
from dotenv import load_dotenv
from supabase import create_client, Client
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
import time

def cleanup_old_logs(log_file: str, max_age_days: int = 7):
    """
    Usuwa wpisy logów starsze niż określona liczba dni.
    
    Args:
        log_file: Ścieżka do pliku logów
        max_age_days: Maksymalny wiek wpisów w dniach
    """
    if not os.path.exists(log_file):
        return

    try:
        # Oblicz datę graniczną
        cutoff_date = datetime.now() - timedelta(days=max_age_days)
        
        # Przeczytaj istniejące logi
        with open(log_file, 'r', encoding='utf-8') as file:
            logs = file.readlines()

        # Filtruj logi
        recent_logs = []
        for log in logs:
            try:
                # Zakładamy format daty: "2024-11-11 10:06:39,860"
                log_date_str = log.split(' - ')[0].strip()
                log_date = datetime.strptime(log_date_str, '%Y-%m-%d %H:%M:%S,%f')
                
                if log_date >= cutoff_date:
                    recent_logs.append(log)
            except (ValueError, IndexError):
                # Zachowaj linie, których nie można sparsować
                recent_logs.append(log)

        # Zapisz tylko niedawne logi
        with open(log_file, 'w', encoding='utf-8') as file:
            file.writelines(recent_logs)

        print(f"Wyczyszczono stare wpisy z pliku logów: {log_file}")
        print(f"Usunięto {len(logs) - len(recent_logs)} wpisów starszych niż {max_age_days} dni")
        
    except Exception as e:
        print(f"Błąd podczas czyszczenia logów: {str(e)}")

# Load .env file first to get FLASK_DEBUG
env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(env_path)

# Get debug mode from environment
DEBUG_MODE = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'

# Ścieżka do pliku logów
LOG_FILE = 'cron/candidate_check.log'

# Wyczyść stare logi przed rozpoczęciem nowego logowania
cleanup_old_logs(LOG_FILE)

# Konfiguracja logowania
logger = logging.getLogger('candidate_check')
logger.setLevel(logging.DEBUG if DEBUG_MODE else logging.INFO)

# Handler dla pliku - zawsze loguje wszystko dla celów debugowania
file_handler = logging.FileHandler(LOG_FILE)
file_handler.setLevel(logging.DEBUG)
file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(file_formatter)

# Handler dla konsoli - poziom zależy od trybu debug
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG if DEBUG_MODE else logging.INFO)
console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(console_formatter)

# Dodaj oba handlery do loggera
logger.addHandler(file_handler)
logger.addHandler(console_handler)

class Config:
    """Konfiguracja aplikacji"""
    def __init__(self):
        env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
        load_dotenv(env_path)
        
        self.SUPABASE_URL = os.getenv('SUPABASE_URL')
        self.SUPABASE_KEY = os.getenv('SUPABASE_KEY')
        self.SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.office365.com')
        self.SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
        self.SMTP_USERNAME = os.getenv('SMTP_USERNAME')
        self.SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')
        self.SENDER_EMAIL = os.getenv('SENDER_EMAIL')
        self.BASE_URL = os.getenv('BASE_URL', 'http://localhost:5000')
        
        if not all([
            self.SUPABASE_URL, 
            self.SUPABASE_KEY,
            self.SMTP_USERNAME,
            self.SMTP_PASSWORD,
            self.SENDER_EMAIL,
            self.BASE_URL
        ]):
            logger.error("Brak wymaganych zmiennych środowiskowych")
            sys.exit(1)

def generate_access_token():
    """Generuje bezpieczny token dostępu"""
    return secrets.token_urlsafe(32)

def send_email(
    config: Config,
    to_email: str,
    subject: str,
    body: str,
) -> bool:
    """
    Wysyła email używając skonfigurowanego serwera SMTP.
    
    Args:
        config: Obiekt konfiguracji
        to_email: Adres email odbiorcy
        subject: Temat wiadomości
        body: Treść wiadomości
        
    Returns:
        bool: True jeśli wysyłka się powiodła, False w przeciwnym razie
    """
    try:
        msg = MIMEMultipart()
        msg['From'] = config.SENDER_EMAIL
        msg['To'] = to_email
        msg['Subject'] = subject

        msg.attach(MIMEText(body, 'plain'))

        with smtplib.SMTP(config.SMTP_SERVER, config.SMTP_PORT) as server:
            server.starttls()
            server.login(config.SMTP_USERNAME, config.SMTP_PASSWORD)
            server.send_message(msg)
            
        logger.info(f"Pomyślnie wysłano email do {to_email}")
        return True
        
    except Exception as e:
        logger.error(f"Błąd podczas wysyłania emaila do {to_email}: {str(e)}")
        return False

def calculate_test_score(supabase: Client, candidate_id: int, test_id: int) -> Optional[int]:
    """Oblicza wynik testu dla danego kandydata."""
    try:
        answers_response = supabase.table('candidate_answers')\
            .select('''
                id,
                question_id,
                text_answer,
                boolean_answer,
                numeric_answer,
                scale_answer,
                date_answer,
                abcdef_answer
            ''')\
            .eq('candidate_id', candidate_id)\
            .execute()
        
        if not answers_response.data:
            logger.info(f"Brak odpowiedzi dla kandydata {candidate_id}")
            return None
            
        question_ids = [answer['question_id'] for answer in answers_response.data]
        questions_response = supabase.table('questions')\
            .select('''
                id,
                answer_type,
                points,
                correct_answer_text,
                correct_answer_boolean,
                correct_answer_numeric,
                correct_answer_scale,
                correct_answer_date,
                correct_answer_abcdef
            ''')\
            .eq('test_id', test_id)\
            .in_('id', question_ids)\
            .execute()
        
        if not questions_response.data:
            logger.info(f"Brak pytań dla testu {test_id}")
            return None
            
        questions = {q['id']: q for q in questions_response.data}
        
        total_score = 0
        for answer in answers_response.data:
            question = questions.get(answer['question_id'])
            if not question:
                logger.warning(f"Nie znaleziono pytania dla odpowiedzi {answer['id']}")
                continue
                
            answer_type = question['answer_type']
            is_correct = False
            
            if answer_type == 'TEXT':
                is_correct = answer.get('text_answer') == question.get('correct_answer_text')
            elif answer_type == 'BOOLEAN':
                is_correct = answer.get('boolean_answer') == question.get('correct_answer_boolean')
            elif answer_type == 'SCALE':
                is_correct = answer.get('scale_answer') == question.get('correct_answer_scale')
            elif answer_type == 'SALARY':
                correct_answer = question.get('correct_answer_numeric')
                is_correct = answer.get('numeric_answer') == correct_answer if correct_answer is not None else False
            elif answer_type == 'DATE':
                is_correct = answer.get('date_answer') == question.get('correct_answer_date')
            elif answer_type == 'ABCDEF':
                is_correct = answer.get('abcdef_answer') == question.get('correct_answer_abcdef')
            
            if is_correct:
                total_score += question.get('points', 0)
        
        logger.info(f"Kandydat {candidate_id} uzyskał {total_score} punktów w teście {test_id}")
        return total_score
        
    except Exception as e:
        logger.error(f"Błąd podczas obliczania wyniku testu: {str(e)}")
        return None

def update_candidate_scores(supabase: Client, candidate: dict, campaign: dict) -> dict:
    """Aktualizuje wyniki kandydata jeśli nie zostały jeszcze obliczone."""
    updates = {}
    
    try:
        # Sprawdź i oblicz wynik PO1
        if candidate.get('recruitment_status') == 'PO1' and \
           candidate.get('po1_score') is None and \
           campaign.get('po1_test_id'):
            
            po1_score = calculate_test_score(
                supabase, 
                candidate['id'], 
                campaign['po1_test_id']
            )
            
            if po1_score is not None:
                updates['po1_score'] = po1_score
                
                test_response = supabase.table('tests')\
                    .select('passing_threshold')\
                    .eq('id', campaign['po1_test_id'])\
                    .single()\
                    .execute()
                    
                if test_response.data:
                    passing_threshold = test_response.data['passing_threshold']
                    if po1_score < passing_threshold:
                        updates['recruitment_status'] = 'REJECTED'
                        logger.info(f"Kandydat {candidate['id']} nie osiągnął wymaganego progu {passing_threshold} punktów w PO1")

        # Sprawdź i oblicz wynik PO2
        if candidate.get('recruitment_status') == 'PO2' and \
           candidate.get('po2_score') is None and \
           campaign.get('po2_test_id'):
            
            po2_score = calculate_test_score(
                supabase, 
                candidate['id'], 
                campaign['po2_test_id']
            )
            
            if po2_score is not None:
                updates['po2_score'] = po2_score
                
                test_response = supabase.table('tests')\
                    .select('passing_threshold')\
                    .eq('id', campaign['po2_test_id'])\
                    .single()\
                    .execute()
                    
                if test_response.data:
                    passing_threshold = test_response.data['passing_threshold']
                    if po2_score < passing_threshold:
                        updates['recruitment_status'] = 'REJECTED'
                        logger.info(f"Kandydat {candidate['id']} nie osiągnął wymaganego progu {passing_threshold} punktów w PO2")

        # Sprawdź i oblicz wynik PO3
        if candidate.get('recruitment_status') == 'PO3' and \
           candidate.get('po3_score') is None and \
           campaign.get('po3_test_id'):
            
            po3_score = calculate_test_score(
                supabase, 
                candidate['id'], 
                campaign['po3_test_id']
            )
            
            if po3_score is not None:
                updates['po3_score'] = po3_score
                
                test_response = supabase.table('tests')\
                    .select('passing_threshold')\
                    .eq('id', campaign['po3_test_id'])\
                    .single()\
                    .execute()
                    
                if test_response.data:
                    passing_threshold = test_response.data['passing_threshold']
                    if po3_score < passing_threshold:
                        updates['recruitment_status'] = 'REJECTED'
                        logger.info(f"Kandydat {candidate['id']} nie osiągnął wymaganego progu {passing_threshold} punktów w PO3")

        # Jeśli są jakieś aktualizacje, zapisz je w bazie
        if updates:
            updates['updated_at'] = datetime.now(timezone.utc).isoformat()
            
            supabase.table('candidates')\
                .update(updates)\
                .eq('id', candidate['id'])\
                .execute()
            
            if 'recruitment_status' in updates:
                logger.info(f"Zaktualizowano status kandydata {candidate['id']} na {updates['recruitment_status']}")
            elif any(key.endswith('_score') for key in updates):
                logger.info(f"Zaktualizowano wyniki kandydata {candidate['id']}")
            
        return {**candidate, **updates}
        
    except Exception as e:
        logger.error(f"Błąd podczas aktualizacji wyników kandydata {candidate['id']}: {str(e)}")
        return candidate

def update_candidates(supabase: Client, config: Config):
    """Aktualizuje kandydatów spełniających określone kryteria"""
    try:
        response = supabase.table('candidates')\
            .select('''
                id,
                email,
                campaign_id,
                recruitment_status,
                po1_score,
                po2_score,
                po3_score,
                access_token_po2,
                access_token_po3
            ''')\
            .neq('recruitment_status', 'REJECTED')\
            .neq('recruitment_status', 'ACCEPTED')\
            .execute()
        
        candidates = response.data
        if not candidates:
            logger.info("Brak kandydatów do aktualizacji")
            return
            
        logger.info(f"Rozpoczęto aktualizację {len(candidates)} kandydatów")
        
        current_time = datetime.now(timezone.utc)
        token_expiry = current_time + timedelta(days=7)

        for candidate in candidates:
            try:
                campaign_response = supabase.table('campaigns')\
                    .select('id, po1_test_id, po2_test_id, po3_test_id')\
                    .eq('id', candidate['campaign_id'])\
                    .single()\
                    .execute()
                    
                campaign = campaign_response.data
                if not campaign:
                    logger.warning(f"Nie znaleziono kampanii {candidate['campaign_id']} dla kandydata {candidate['id']}")
                    continue
                
                candidate = update_candidate_scores(supabase, candidate, campaign)
                
                # Sprawdź czy należy wygenerować token PO2
                if candidate.get('recruitment_status') == 'PO1' and \
                   candidate.get('po1_score') is not None and \
                   not candidate.get('access_token_po2'):
                    
                    token = generate_access_token()
                    test_url = f"{config.BASE_URL}/test/candidate/{token}"
                    
                    updates = {
                        'access_token_po2': token,
                        'access_token_po2_expires_at': token_expiry.isoformat(),
                        'access_token_po2_is_used': False,
                        'recruitment_status': 'PO2',
                        'updated_at': current_time.isoformat()
                    }
                    
                    supabase.table('candidates')\
                        .update(updates)\
                        .eq('id', candidate['id'])\
                        .execute()
                    
                    if send_email(
                        config,
                        candidate['email'],
                        "Dostęp do etapu PO2",
                        f"Gratulacje! Pomyślnie ukończyłeś/aś etap PO1 i otrzymujesz dostęp do kolejnego etapu rekrutacji.\n"
                        f"Link do testu: {test_url}\n"
                        f"Link jest ważny do: {token_expiry.isoformat()}"
                    ):
                        logger.info(f"Wysłano token PO2 do kandydata {candidate['id']}")
                
                # Sprawdź czy należy wygenerować token PO3
                if candidate.get('recruitment_status') == 'PO2' and \
                   candidate.get('po2_score') is not None and \
                   not candidate.get('access_token_po3'):
                    
                    token = generate_access_token()
                    test_url = f"{config.BASE_URL}/test/{token}"
                    
                    updates = {
                        'access_token_po3': token,
                        'access_token_po3_expires_at': token_expiry.isoformat(),
                        'access_token_po3_is_used': False,
                        'recruitment_status': 'PO3',
                        'updated_at': current_time.isoformat()
                    }
                    
                    supabase.table('candidates')\
                        .update(updates)\
                        .eq('id', candidate['id'])\
                        .execute()
                    
                    if send_email(
                        config,
                        candidate['email'],
                        "Dostęp do etapu PO3",
                        f"Gratulacje! Pomyślnie ukończyłeś/aś etap PO2 i otrzymujesz dostęp do kolejnego etapu rekrutacji.\n"
                        f"Link do testu: {test_url}\n"
                        f"Link jest ważny do: {token_expiry.isoformat()}"
                    ):
                        logger.info(f"Wysłano token PO3 do kandydata {candidate['id']}")
                
            except Exception as e:
                logger.error(f"Błąd podczas przetwarzania kandydata {candidate['id']}: {str(e)}")
                continue
                
        logger.info("Zakończono aktualizację kandydatów")
        
    except Exception as e:
        logger.error(f"Błąd podczas pobierania listy kandydatów: {str(e)}")
        raise

def main():
    """Główna funkcja skryptu"""
    try:
        logger.info("Rozpoczęcie procesu sprawdzania kandydatów")
        config = Config()
        supabase = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)
        update_candidates(supabase, config)
        logger.info("Zakończenie procesu sprawdzania kandydatów")
        
    except Exception as e:
        logger.error(f"Wystąpił krytyczny błąd: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 