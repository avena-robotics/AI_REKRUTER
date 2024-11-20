import os
import sys
from datetime import datetime, timedelta
import secrets
from dotenv import load_dotenv
from supabase import create_client, Client
import logging

# Konfiguracja logowania
logging.basicConfig(
    filename='cron/candidate_check.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class Config:
    """Konfiguracja aplikacji"""
    def __init__(self):
        env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
        load_dotenv(env_path)
        
        self.SUPABASE_URL = os.getenv('SUPABASE_URL')
        self.SUPABASE_KEY = os.getenv('SUPABASE_KEY')
        
        if not all([self.SUPABASE_URL, self.SUPABASE_KEY]):
            logging.error("Brak wymaganych zmiennych środowiskowych")
            sys.exit(1)

def generate_access_token():
    """Generuje bezpieczny token dostępu"""
    return secrets.token_urlsafe(32)

def update_candidates(supabase: Client):
    """Aktualizuje kandydatów spełniających określone kryteria"""
    try:
        # Pobieranie kandydatów spełniających kryteria
        response = supabase.table('candidates').select('*').not_('recruitment_status', 'in', '(REJECTED,ACCEPTED)').execute()
        
        candidates = response.data
        current_time = datetime.now(datetime.UTC)
        token_expiry = current_time + timedelta(days=7)  # Token ważny przez 7 dni

        for candidate in candidates:
            updates = {}
            
            # Sprawdzamy warunki dla PO2
            if candidate.get('po1_score') and not candidate.get('access_token_po2'):
                updates.update({
                    'access_token_po2': generate_access_token(),
                    'access_token_po2_expires_at': token_expiry.isoformat(),
                })
            
            # Sprawdzamy warunki dla PO3
            if candidate.get('po2_score') and not candidate.get('access_token_po3'):
                updates.update({
                    'access_token_po3': generate_access_token(),
                    'access_token_po3_expires_at': token_expiry.isoformat(),
                })
            
            # Jeśli są jakieś aktualizacje do wykonania
            if updates:
                updates['updated_at'] = current_time.isoformat()
                supabase.table('candidates').update(updates).eq('id', candidate['id']).execute()
                
    except Exception as e:
        logging.error(f"Wystąpił błąd podczas aktualizacji kandydatów: {str(e)}")
        raise

def main():
    """Główna funkcja skryptu"""
    try:
        config = Config()
        supabase = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)
        update_candidates(supabase)
        
    except Exception as e:
        logging.error(f"Wystąpił krytyczny błąd: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 