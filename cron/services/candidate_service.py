import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, Any
from supabase import Client
from ..config import Config
from ..utils.token_utils import generate_access_token
from .email_service import EmailService
from .test_service import TestService

class CandidateService:
    """Serwis do zarządzania kandydatami i ich statusami"""
    
    def __init__(self, supabase: Client, config: Config, 
                 email_service: EmailService, test_service: TestService):
        self.supabase = supabase
        self.config = config
        self.email_service = email_service
        self.test_service = test_service
        self.logger = logging.getLogger('candidate_check')

    def update_candidate_scores(self, candidate: dict, campaign: dict) -> dict:
        """
        Aktualizuje wyniki testów kandydata
        
        Args:
            candidate: Dane kandydata
            campaign: Dane kampanii rekrutacyjnej
            
        Returns:
            dict: Zaktualizowane dane kandydata
        """
        updates = {}
        
        try:
            # Sprawdzenie i obliczenie wyniku PO1
            if candidate.get('recruitment_status') == 'PO1' and \
               candidate.get('po1_score') is None and \
               campaign.get('po1_test_id'):
                
                po1_score = self.test_service.calculate_test_score(
                    candidate['id'], 
                    campaign['po1_test_id']
                )
                
                if po1_score is not None:
                    updates['po1_score'] = po1_score
                    
                    test_response = self.supabase.table('tests')\
                        .select('passing_threshold')\
                        .eq('id', campaign['po1_test_id'])\
                        .single()\
                        .execute()
                        
                    if test_response.data:
                        passing_threshold = test_response.data['passing_threshold']
                        if po1_score < passing_threshold:
                            updates['recruitment_status'] = 'REJECTED'
                            self.logger.info(f"Kandydat {candidate['id']} nie osiągnął wymaganego progu {passing_threshold} punktów w PO1")

            # Sprawdzenie i obliczenie wyniku PO2
            elif candidate.get('recruitment_status') == 'PO2' and \
               candidate.get('po2_score') is None and \
               campaign.get('po2_test_id'):
                
                po2_score = self.test_service.calculate_test_score(
                    candidate['id'], 
                    campaign['po2_test_id']
                )
                
                if po2_score is not None:
                    updates['po2_score'] = po2_score
                    
                    test_response = self.supabase.table('tests')\
                        .select('passing_threshold')\
                        .eq('id', campaign['po2_test_id'])\
                        .single()\
                        .execute()
                        
                    if test_response.data:
                        passing_threshold = test_response.data['passing_threshold']
                        if po2_score < passing_threshold:
                            updates['recruitment_status'] = 'REJECTED'
                            self.logger.info(f"Kandydat {candidate['id']} nie osiągnął wymaganego progu {passing_threshold} punktów w PO2")

            # Sprawdzenie i obliczenie wyniku PO3
            elif candidate.get('recruitment_status') == 'PO3' and \
               candidate.get('po3_score') is None and \
               campaign.get('po3_test_id'):
                
                po3_score = self.test_service.calculate_test_score(
                    candidate['id'], 
                    campaign['po3_test_id']
                )
                
                if po3_score is not None:
                    updates['po3_score'] = po3_score
                    
                    test_response = self.supabase.table('tests')\
                        .select('passing_threshold')\
                        .eq('id', campaign['po3_test_id'])\
                        .single()\
                        .execute()
                        
                    if test_response.data:
                        passing_threshold = test_response.data['passing_threshold']
                        if po3_score < passing_threshold:
                            updates['recruitment_status'] = 'REJECTED'
                            self.logger.info(f"Kandydat {candidate['id']} nie osiągnął wymaganego progu {passing_threshold} punktów w PO3")

            if updates:
                updates['updated_at'] = datetime.now(timezone.utc).isoformat()
                
                self.supabase.table('candidates')\
                    .update(updates)\
                    .eq('id', candidate['id'])\
                    .execute()
                
                if 'recruitment_status' in updates:
                    self.logger.info(f"Zaktualizowano status kandydata {candidate['id']} na {updates['recruitment_status']}")
                elif any(key.endswith('_score') for key in updates):
                    self.logger.info(f"Zaktualizowano wyniki kandydata {candidate['id']}")
                
            return {**candidate, **updates}
            
        except Exception as e:
            self.logger.error(f"Błąd podczas aktualizacji wyników kandydata {candidate['id']}: {str(e)}")
            return candidate

    def update_candidates(self):
        """Aktualizuje statusy i wyniki wszystkich aktywnych kandydatów"""
        try:
            response = self.supabase.table('candidates')\
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
                self.logger.info("Brak kandydatów do aktualizacji")
                return
                
            self.logger.info(f"Rozpoczęto aktualizację {len(candidates)} kandydatów")
            
            current_time = datetime.now(timezone.utc)
            token_expiry = current_time + timedelta(days=7)
            formatted_expiry = token_expiry.strftime("%Y-%m-%d %H:%M")

            for candidate in candidates:
                try:
                    campaign_response = self.supabase.table('campaigns')\
                        .select('id, po1_test_id, po2_test_id, po3_test_id')\
                        .eq('id', candidate['campaign_id'])\
                        .single()\
                        .execute()
                        
                    campaign = campaign_response.data
                    if not campaign:
                        self.logger.warning(f"Nie znaleziono kampanii {candidate['campaign_id']} dla kandydata {candidate['id']}")
                        continue
                    
                    candidate = self.update_candidate_scores(candidate, campaign)
                    
                    # Generowanie tokenu PO2
                    if candidate.get('recruitment_status') == 'PO1' and \
                       campaign.get('po2_test_id') and \
                       candidate.get('po1_score') is not None and \
                       not candidate.get('access_token_po2'):
                        
                        self._handle_token_generation(
                            candidate, 
                            'PO2', 
                            token_expiry, 
                            formatted_expiry
                        )
                    
                    # Generowanie tokenu PO3
                    if candidate.get('recruitment_status') == 'PO2' and \
                       campaign.get('po3_test_id') and \
                       candidate.get('po2_score') is not None and \
                       not candidate.get('access_token_po3'):
                        
                        self._handle_token_generation(
                            candidate, 
                            'PO3', 
                            token_expiry, 
                            formatted_expiry
                        )
                    
                except Exception as e:
                    self.logger.error(f"Błąd podczas przetwarzania kandydata {candidate['id']}: {str(e)}")
                    continue
                    
            self.logger.info("Zakończono aktualizację kandydatów")
            
        except Exception as e:
            self.logger.error(f"Błąd podczas pobierania listy kandydatów: {str(e)}")
            raise

    def _handle_token_generation(self, candidate: Dict[str, Any], 
                               stage: str, token_expiry: datetime, 
                               formatted_expiry: str) -> None:
        """
        Generuje token dostępu i wysyła email do kandydata
        
        Args:
            candidate: Dane kandydata
            stage: Etap rekrutacji (PO2/PO3)
            token_expiry: Data wygaśnięcia tokenu
            formatted_expiry: Sformatowana data wygaśnięcia
        """
        token = generate_access_token()
        test_url = f"{self.config.BASE_URL}/test/candidate/{token}"
        
        updates = {
            f'access_token_{stage.lower()}': token,
            f'access_token_{stage.lower()}_expires_at': token_expiry.isoformat(),
            f'access_token_{stage.lower()}_is_used': False,
            'recruitment_status': stage,
            'updated_at': datetime.now(timezone.utc).isoformat()
        }
        
        self.supabase.table('candidates')\
            .update(updates)\
            .eq('id', candidate['id'])\
            .execute()
        
        if self.email_service.send_email(
            candidate['email'],
            f"Dostęp do etapu {stage}",
            f"Gratulacje! Pomyślnie ukończyłeś/aś etap {stage[:-1]} "
            f"i otrzymujesz dostęp do kolejnego etapu rekrutacji.\n"
            f"Link do testu: {test_url}\n"
            f"Link jest ważny do: {formatted_expiry}"
        ):
            self.logger.info(f"Wysłano token {stage} do kandydata {candidate['id']}") 