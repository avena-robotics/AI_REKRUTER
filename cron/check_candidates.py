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
    logger.info(f"Rozpoczęcie obliczania wyniku testu dla kandydata {candidate_id}, test {test_id}")
    try:
        # Najpierw pobierz odpowiedzi kandydata
        answers_query = supabase.table('candidate_answers')\
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
            .eq('candidate_id', candidate_id)
            
        logger.debug(f"Zapytanie o odpowiedzi: {answers_query}")
        answers_response = answers_query.execute()
        
        if not answers_response.data:
            logger.info(f"Brak odpowiedzi dla kandydata {candidate_id}")
            return None
            
        # Pobierz pytania dla tych odpowiedzi
        question_ids = [answer['question_id'] for answer in answers_response.data]
        questions_query = supabase.table('questions')\
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
            .in_('id', question_ids)
            
        logger.debug(f"Zapytanie o pytania: {questions_query}")
        questions_response = questions_query.execute()
        
        if not questions_response.data:
            logger.info(f"Brak pytań dla testu {test_id}")
            return None
            
        # Utwórz słownik pytań dla szybszego dostępu
        questions = {q['id']: q for q in questions_response.data}
        
        total_score = 0
        for answer in answers_response.data:
            question = questions.get(answer['question_id'])
            if not question:
                logger.warning(f"Nie znaleziono pytania dla odpowiedzi {answer['id']}")
                continue
                
            answer_type = question['answer_type']
            
            logger.debug(f"Pytanie {question['id']}, typ odpowiedzi: {answer_type}")
            logger.debug(f"Odpowiedź kandydata: {answer}")
            logger.debug(f"Poprawna odpowiedź: {question}")
            
            # Sprawdź czy odpowiedź jest poprawna w zależności od typu
            is_correct = False
            
            if answer_type == 'TEXT':
                candidate_answer = answer.get('text_answer')
                correct_answer = question.get('correct_answer_text')
                is_correct = candidate_answer == correct_answer
                logger.debug(f"TEXT - Odpowiedź kandydata: '{candidate_answer}', Poprawna: '{correct_answer}'")
                
            elif answer_type == 'BOOLEAN':
                candidate_answer = answer.get('boolean_answer')
                correct_answer = question.get('correct_answer_boolean')
                is_correct = candidate_answer == correct_answer
                logger.debug(f"BOOLEAN - Odpowiedź kandydata: {candidate_answer}, Poprawna: {correct_answer}")
                
            elif answer_type == 'SCALE':
                candidate_answer = answer.get('scale_answer')
                correct_answer = question.get('correct_answer_scale')
                is_correct = candidate_answer == correct_answer
                logger.debug(f"SCALE - Odpowiedź kandydata: {candidate_answer}, Poprawna: {correct_answer}")
                
            elif answer_type == 'SALARY':
                candidate_answer = answer.get('numeric_answer')
                correct_answer = question.get('correct_answer_numeric')
                is_correct = candidate_answer == correct_answer if correct_answer is not None else False
                logger.debug(f"SALARY - Odpowiedź kandydata: {candidate_answer}, Poprawna: {correct_answer}")
                
            elif answer_type == 'DATE':
                candidate_answer = answer.get('date_answer')
                correct_answer = question.get('correct_answer_date')
                is_correct = candidate_answer == correct_answer
                logger.debug(f"DATE - Odpowiedź kandydata: {candidate_answer}, Poprawna: {correct_answer}")
                
            elif answer_type == 'ABCDEF':
                candidate_answer = answer.get('abcdef_answer')
                correct_answer = question.get('correct_answer_abcdef')
                is_correct = candidate_answer == correct_answer
                logger.debug(f"ABCDEF - Odpowiedź kandydata: {candidate_answer}, Poprawna: {correct_answer}")
            
            points = question.get('points', 0)
            if is_correct:
                total_score += points
                logger.debug(f"Odpowiedź poprawna, dodano {points} punktów")
            else:
                logger.debug(f"Odpowiedź niepoprawna, 0 punktów")
        
        logger.info(f"Zakończono obliczanie wyniku dla kandydata {candidate_id}: {total_score} punktów")
        return total_score
        
    except Exception as e:
        logger.error(f"Błąd podczas obliczania wyniku testu: {str(e)}")
        logger.exception("Szczegóły błędu:")
        return None

def update_candidate_scores(supabase: Client, candidate: dict, campaign: dict) -> dict:
    """
    Aktualizuje wyniki kandydata jeśli nie zostały jeszcze obliczone.
    """
    logger.info(f"Rozpoczęcie aktualizacji wyników dla kandydata {candidate['id']}")
    logger.debug(f"Stan początkowy kandydata: {candidate}")
    logger.debug(f"Dane kampanii: {campaign}")
    
    updates = {}
    
    try:
        # Sprawdź i oblicz wynik PO1
        if candidate.get('recruitment_status') == 'PO1' and \
           candidate.get('po1_score') is None and \
           campaign.get('po1_test_id'):
            
            logger.info(f"Obliczanie wyniku PO1 dla kandydata {candidate['id']}")
            po1_score = calculate_test_score(
                supabase, 
                candidate['id'], 
                campaign['po1_test_id']
            )
            
            if po1_score is not None:
                updates['po1_score'] = po1_score
                logger.info(f"Uzyskany wynik PO1: {po1_score}")
                
                # Pobierz próg zaliczenia dla testu PO1
                logger.debug(f"Pobieranie progu zaliczenia dla testu PO1 (ID: {campaign['po1_test_id']})")
                test_response = supabase.table('tests')\
                    .select('passing_threshold')\
                    .eq('id', campaign['po1_test_id'])\
                    .single()\
                    .execute()
                
                logger.debug(f"Odpowiedź z progu zaliczenia: {test_response}")
                    
                if test_response.data:
                    passing_threshold = test_response.data['passing_threshold']
                    logger.info(f"Próg zaliczenia PO1: {passing_threshold}, Wynik kandydata: {po1_score}")
                    if po1_score < passing_threshold:
                        updates['recruitment_status'] = 'REJECTED'
                        logger.info(f"Kandydat {candidate['id']} nie osiągnął progu zaliczenia PO1")
                
        # Sprawdź i oblicz wynik PO2
        if candidate.get('recruitment_status') == 'PO2' and \
           candidate.get('po2_score') is None and \
           campaign.get('po2_test_id'):
            
            logger.info(f"Obliczanie wyniku PO2 dla kandydata {candidate['id']}")
            po2_score = calculate_test_score(
                supabase, 
                candidate['id'], 
                campaign['po2_test_id']
            )
            
            if po2_score is not None:
                updates['po2_score'] = po2_score
                logger.info(f"Uzyskany wynik PO2: {po2_score}")
                
                # Pobierz próg zaliczenia dla testu PO2
                logger.debug(f"Pobieranie progu zaliczenia dla testu PO2 (ID: {campaign['po2_test_id']})")
                test_response = supabase.table('tests')\
                    .select('passing_threshold')\
                    .eq('id', campaign['po2_test_id'])\
                    .single()\
                    .execute()
                
                logger.debug(f"Odpowiedź z progu zaliczenia: {test_response}")
                    
                if test_response.data:
                    passing_threshold = test_response.data['passing_threshold']
                    logger.info(f"Próg zaliczenia PO2: {passing_threshold}, Wynik kandydata: {po2_score}")
                    if po2_score < passing_threshold:
                        updates['recruitment_status'] = 'REJECTED'
                        logger.info(f"Kandydat {candidate['id']} nie osiągnął progu zaliczenia PO2")
                
        # Sprawd i oblicz wynik PO3
        if candidate.get('recruitment_status') == 'PO3' and \
           candidate.get('po3_score') is None and \
           campaign.get('po3_test_id'):
            
            logger.info(f"Obliczanie wyniku PO3 dla kandydata {candidate['id']}")
            po3_score = calculate_test_score(
                supabase, 
                candidate['id'], 
                campaign['po3_test_id']
            )
            
            if po3_score is not None:
                updates['po3_score'] = po3_score
                logger.info(f"Uzyskany wynik PO3: {po3_score}")
                
                # Pobierz próg zaliczenia dla testu PO3
                logger.debug(f"Pobieranie progu zaliczenia dla testu PO3 (ID: {campaign['po3_test_id']})")
                test_response = supabase.table('tests')\
                    .select('passing_threshold')\
                    .eq('id', campaign['po3_test_id'])\
                    .single()\
                    .execute()
                
                logger.debug(f"Odpowiedź z progu zaliczenia: {test_response}")
                    
                if test_response.data:
                    passing_threshold = test_response.data['passing_threshold']
                    logger.info(f"Próg zaliczenia PO3: {passing_threshold}, Wynik kandydata: {po3_score}")
                    if po3_score < passing_threshold:
                        updates['recruitment_status'] = 'REJECTED'
                        logger.info(f"Kandydat {candidate['id']} nie osiągnął progu zaliczenia PO3")
                
        # Jeśli są jakieś aktualizacje, zapisz je w bazie
        if updates:
            logger.info(f"Aktualizacja danych kandydata {candidate['id']}")
            logger.debug(f"Dane do aktualizacji: {updates}")
            updates['updated_at'] = datetime.now(timezone.utc).isoformat()
            
            update_query = supabase.table('candidates')\
                .update(updates)\
                .eq('id', candidate['id'])
            logger.debug(f"Zapytanie aktualizujące: {update_query}")
            
            result = update_query.execute()
            logger.debug(f"Wynik aktualizacji: {result}")
            
        logger.info(f"Zakończenie aktualizacji wyników dla kandydata {candidate['id']}")
        return {**candidate, **updates}
        
    except Exception as e:
        logger.error(f"Błąd podczas aktualizacji wyników kandydata {candidate['id']}: {str(e)}")
        logger.exception("Szczegóły błędu:")
        return candidate

def update_candidates(supabase: Client, config: Config):
    """Aktualizuje kandydatów spełniających określone kryteria"""
    logger.info("Rozpoczęcie procesu aktualizacji kandydatów")
    try:
        # Najpierw pobierz kandydatów
        query = supabase.table('candidates')\
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
            .neq('recruitment_status', 'ACCEPTED')
        
        logger.debug(f"Zapytanie o kandydatów: {query}")
        response = query.execute()
        logger.debug(f"Odpowiedź z zapytania o kandydatów: {response}")
        
        candidates = response.data
        if not candidates:
            logger.info("Brak kandydatów do aktualizacji")
            return
            
        logger.info(f"Znaleziono {len(candidates)} kandydatów do sprawdzenia")
        
        current_time = datetime.now(timezone.utc)
        token_expiry = current_time + timedelta(days=7)
        logger.debug(f"Ustawiono czas wygaśnięcia tokenów na: {token_expiry}")

        for idx, candidate in enumerate(candidates, 1):
            logger.info(f"Przetwarzanie kandydata {idx}/{len(candidates)} (ID: {candidate['id']})")
            
            # Pobierz dane kampanii oddzielnie
            try:
                campaign_response = supabase.table('campaigns')\
                    .select('id, po1_test_id, po2_test_id, po3_test_id')\
                    .eq('id', candidate['campaign_id'])\
                    .single()\
                    .execute()
                    
                campaign = campaign_response.data
                if not campaign:
                    logger.warning(f"Nie znaleziono kampanii o ID {candidate['campaign_id']} dla kandydata {candidate['id']}")
                    continue
                    
                logger.debug(f"Pobrano dane kampanii: {campaign}")
                
            except Exception as e:
                logger.error(f"Błąd podczas pobierania danych kampanii dla kandydata {candidate['id']}: {str(e)}")
                continue
            
            # Najpierw oblicz brakujące wyniki
            candidate = update_candidate_scores(supabase, candidate, campaign)
            
            # Jeśli kandydat nie został odrzucony, sprawdź czy należy wygenerować token
            if candidate.get('recruitment_status') != 'REJECTED':
                updates = {}
                
                # Sprawdź czy należy wygenerować token PO2
                if candidate.get('recruitment_status') == 'PO1' and \
                   candidate.get('po1_score') is not None and \
                   not candidate.get('access_token_po2'):
                    logger.info(f"Generowanie tokenu PO2 dla kandydata {candidate['id']}")
                    token = generate_access_token()
                    test_url = f"{config.BASE_URL}/test/{token}"
                    updates.update({
                        'access_token_po2': token,
                        'access_token_po2_expires_at': token_expiry.isoformat(),
                        'access_token_po2_is_used': False,
                        'recruitment_status': 'PO2'
                    })
                    logger.debug(f"Token PO2: {token}")
                    logger.debug(f"URL testu: {test_url}")
                    
                    send_email(
                        config,
                        candidate['email'],
                        "Dostęp do etapu PO2",
                        f"Gratulacje! Pomyślnie ukończyłeś/aś etap PO1 i otrzymujesz dostęp do kolejnego etapu rekrutacji.\n"
                        f"Link do testu: {test_url}\n"
                        f"Link jest ważny do: {token_expiry.isoformat()}"
                    )
                
                # Sprawdź czy należy wygenerować token PO3
                if candidate.get('recruitment_status') == 'PO2' and \
                   candidate.get('po2_score') is not None and \
                   not candidate.get('access_token_po3'):
                    logger.info(f"Generowanie tokenu PO3 dla kandydata {candidate['id']}")
                    token = generate_access_token()
                    test_url = f"{config.BASE_URL}/test/{token}"
                    updates.update({
                        'access_token_po3': token,
                        'access_token_po3_expires_at': token_expiry.isoformat(),
                        'access_token_po3_is_used': False,
                        'recruitment_status': 'PO3'
                    })
                    logger.debug(f"Token PO3: {token}")
                    logger.debug(f"URL testu: {test_url}")
                    
                    send_email(
                        config,
                        candidate['email'],
                        "Dostęp do etapu PO3",
                        f"Gratulacje! Pomyślnie ukończyłeś/aś etap PO2 i otrzymujesz dostęp do kolejnego etapu rekrutacji.\n"
                        f"Link do testu: {test_url}\n"
                        f"Link jest ważny do: {token_expiry.isoformat()}"
                    )
                
                # Jeśli są jakieś aktualizacje, zapisz je w bazie
                if updates:
                    logger.info(f"Aktualizacja danych kandydata {candidate['id']}")
                    logger.debug(f"Dane do aktualizacji: {updates}")
                    updates['updated_at'] = current_time.isoformat()
                    
                    update_query = supabase.table('candidates')\
                        .update(updates)\
                        .eq('id', candidate['id'])
                    logger.debug(f"Zapytanie aktualizujące: {update_query}")
                    
                    result = update_query.execute()
                    logger.debug(f"Wynik aktualizacji: {result}")
                    
                    logger.info(f"Zaktualizowano dane kandydata {candidate['id']}")
                
    except Exception as e:
        logger.error(f"Wystąpił błąd podczas aktualizacji kandydatów: {str(e)}")
        logger.exception("Szczegóły błędu:")
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