from common.logger import Logger
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional
from supabase import Client
from utils.token_utils import generate_access_token
from common.config import Config
from common.email_service import EmailService
from services.test_service import TestService

class CandidateService:
    """Serwis do zarządzania kandydatami i ich statusami"""
    
    def __init__(self, supabase: Client, config: Config, 
                 email_service: EmailService, test_service: TestService):
        self.supabase = supabase
        self.config = config
        self.email_service = email_service
        self.test_service = test_service
        self.logger = Logger.instance()

    def update_candidate_scores(self, candidate: dict, campaign: dict) -> dict:
        """
        Aktualizuje wyniki testów kandydata
        
        Args:
            candidate: Dane kandydata
            campaign: Dane kampanii rekrutacyjnej
            
        Returns:
            dict: Zaktualizowane dane kandydata
        """
        try:
            current_time = datetime.now(timezone.utc)
            updates = {}
            
            # When updating scores, also ensure timestamps are in UTC
            if any(key in updates for key in ['po1_score', 'po2_score', 'po2_5_score', 'po3_score']):
                stage = candidate.get('recruitment_status', '').lower()
                if stage in ['po1', 'po2', 'po2_5', 'po3']:
                    updates[f'{stage}_completed_at'] = current_time.isoformat()
            
            self.logger.info(f"Rozpoczęcie aktualizacji wyników dla kandydata {candidate['id']} o statusie {candidate.get('recruitment_status')}")
            
            # Sprawdź czy kandydat potrzebuje aktualizacji wyników EQ
            needs_eq_update = all(
                candidate.get(score_key) is None 
                for score_key in ['score_ko', 'score_re', 'score_w', 'score_in', 
                                'score_pz', 'score_kz', 'score_dz', 'score_sw']
            )
            
            self.logger.info(f"Kandydat {candidate['id']} - potrzebuje aktualizacji EQ: {needs_eq_update}")

            # Sprawdzenie i obliczenie wyniku PO1
            if (candidate.get('po1_score') is None and campaign.get('po1_test_id')):
                self.logger.info(f"Obliczanie wyniku PO1 dla kandydata {candidate['id']}, test {campaign['po1_test_id']}")
                
                result = self.test_service.calculate_test_score(
                    candidate['id'], 
                    campaign['po1_test_id'],
                    'PO1'
                )
                
                if result is not None:
                    updates['po1_score'] = result
                    
                    test_response = self.supabase.table('tests')\
                        .select('passing_threshold')\
                        .eq('id', campaign['po1_test_id'])\
                        .single()\
                        .execute()
                        
                    if test_response.data:
                        passing_threshold = test_response.data['passing_threshold']
                        if result < passing_threshold and candidate.get('recruitment_status') == 'PO1':
                            updates['recruitment_status'] = 'REJECTED'
                            self.logger.warning(f"Kandydat {candidate['id']} nie osiągnął wymaganego progu {passing_threshold} punktów w PO1 (wynik: {result})")
                        elif result >= passing_threshold and candidate.get('recruitment_status') == 'PO1':
                            self._handle_token_generation(candidate, 'PO2')
                else:
                    self.logger.warning(f"Nie otrzymano wyniku dla kandydata {candidate['id']} w teście PO1")

            # Sprawdzenie i obliczenie wyniku PO2
            if (candidate.get('po2_score') is None or needs_eq_update) and campaign.get('po2_test_id'):
                self.logger.info(f"Obliczanie wyniku PO2 dla kandydata {candidate['id']}, test {campaign['po2_test_id']}")
                
                result = self.test_service.calculate_test_score(
                    candidate['id'], 
                    campaign['po2_test_id'],
                    'PO2'
                )
                
                if isinstance(result, dict):  # EQ test results
                    updates.update(result)
                    
                    # Simulate EQ_EVALUATION answers if PO2_5 test exists
                    if campaign.get('po2_5_test_id'):
                        self.test_service.simulate_eq_evaluation(
                            candidate_id=candidate['id'],
                            campaign_id=campaign['id'],
                            eq_scores=result
                        )
                        updates['po2_score'] = 0
                        self.logger.info(f"Ustawiono wynik PO2=0 i zaktualizowano status na PO2_5 dla kandydata {candidate['id']}")

                elif result is not None:  # Regular test score
                    updates['po2_score'] = result
                    
                    test_response = self.supabase.table('tests')\
                        .select('passing_threshold')\
                        .eq('id', campaign['po2_test_id'])\
                        .single()\
                        .execute()
                        
                    if test_response.data:
                        passing_threshold = test_response.data['passing_threshold']
                        if result < passing_threshold and candidate.get('recruitment_status') == 'PO2':
                            updates['recruitment_status'] = 'REJECTED'
                            self.logger.info(f"Kandydat {candidate['id']} nie osiągnął wymaganego progu {passing_threshold} punktów w PO2")
                        elif result >= passing_threshold and candidate.get('recruitment_status') == 'PO2':
                            self._handle_token_generation(candidate, 'PO3')

            # Sprawdzenie i obliczenie wyniku PO2_5
            if (candidate.get('po2_5_score') is None and campaign.get('po2_5_test_id')):
                self.logger.info(f"Obliczanie wyniku PO2_5 dla kandydata {candidate['id']}, test {campaign['po2_5_test_id']}")
                
                result = self.test_service.calculate_test_score(
                    candidate['id'], 
                    campaign['po2_5_test_id'],
                    'PO2_5'
                )
                
                if result is not None:  # Regular test score
                    updates['po2_5_score'] = result
                    
                    test_response = self.supabase.table('tests')\
                        .select('passing_threshold')\
                        .eq('id', campaign['po2_5_test_id'])\
                        .single()\
                        .execute()
                        
                    if test_response.data:
                        passing_threshold = test_response.data['passing_threshold']
                        if result < passing_threshold and (candidate.get('recruitment_status') == 'PO2' or candidate.get('recruitment_status') == 'PO2_5'):
                            updates['recruitment_status'] = 'REJECTED'
                            self.logger.info(f"Kandydat {candidate['id']} nie osiągnął wymaganego progu {passing_threshold} punktów w PO2_5")
                        elif result >= passing_threshold and (candidate.get('recruitment_status') == 'PO2' or candidate.get('recruitment_status') == 'PO2_5'):
                            self._handle_token_generation(candidate, 'PO3')

            # Sprawdzenie i obliczenie wyniku PO3
            if (candidate.get('po3_score') is None and campaign.get('po3_test_id')):
                self.logger.info(f"Obliczanie wyniku PO3 dla kandydata {candidate['id']}, test {campaign['po3_test_id']}")
                
                result = self.test_service.calculate_test_score(
                    candidate['id'], 
                    campaign['po3_test_id'],
                    'PO3'
                )
                
                if result is not None:  # Regular test score
                    updates['po3_score'] = result
                    
                    test_response = self.supabase.table('tests')\
                        .select('passing_threshold')\
                        .eq('id', campaign['po3_test_id'])\
                        .single()\
                        .execute()
                        
                    if test_response.data:
                        passing_threshold = test_response.data['passing_threshold']
                        if result < passing_threshold and candidate.get('recruitment_status') == 'PO3':
                            updates['recruitment_status'] = 'REJECTED'
                            self.logger.info(f"Kandydat {candidate['id']} nie osiągnął wymaganego progu {passing_threshold} punktów w PO3")
                        elif result >= passing_threshold and candidate.get('recruitment_status') == 'PO3':
                            self._next_stage(candidate)

            if updates:
                self.logger.info(f"Aktualizacja danych kandydata {candidate['id']}: {updates}")
                
                # Calculate total score before updating database
                if any(key in updates for key in ['po1_score', 'po2_score', 'po2_5_score', 'po3_score']):
                    total_score = self._calculate_total_weighted_score(
                        po1_score=updates.get('po1_score', candidate.get('po1_score')),
                        po2_score=updates.get('po2_score', candidate.get('po2_score')),
                        po2_5_score=updates.get('po2_5_score', candidate.get('po2_5_score')),
                        po3_score=updates.get('po3_score', candidate.get('po3_score')),
                        campaign=campaign
                    )
                    updates['total_score'] = total_score
                    self.logger.info(f"Zaktualizowano total_score dla kandydata {candidate['id']}: {total_score}")
                
                updates['updated_at'] = datetime.now(timezone.utc).isoformat()
                
                # Update database with all changes including total_score
                self.supabase.table('candidates')\
                    .update(updates)\
                    .eq('id', candidate['id'])\
                    .execute()
                
                if 'recruitment_status' in updates:
                    self.logger.info(f"Zaktualizowano status kandydata {candidate['id']} na {updates['recruitment_status']}")
                elif any(key.endswith('_score') for key in updates):
                    self.logger.info(f"Zaktualizowano wyniki kandydata {candidate['id']}: {updates}")
                
            else:
                self.logger.info(f"Brak aktualizacji dla kandydata {candidate['id']}")
                
            return {**candidate, **updates}
            
        except Exception as e:
            self.logger.error(
                f"Błąd podczas aktualizacji wyników kandydata {candidate['id']}: {str(e)}", 
                exc_info=True
            )
            return candidate

    def _calculate_total_weighted_score(self, po1_score: Optional[float], 
                                      po2_score: Optional[float], 
                                      po2_5_score: Optional[float], 
                                      po3_score: Optional[float], 
                                      campaign: dict) -> float:
        """
        Oblicza całkowity ważony wynik na podstawie wyników testów i wag z kampanii
        
        Args:
            po1_score: Wynik testu PO1
            po2_score: Wynik testu PO2
            po2_5_score: Wynik testu PO2_5
            po3_score: Wynik testu PO3
            campaign: Dane kampanii rekrutacyjnej
            
        Returns:
            float: Całkowity ważony wynik (0.0 jeśli nie można obliczyć, ale istnieje jakikolwiek wynik)
        """
        try:
            self.logger.debug(f"Obliczanie total_score dla wyników: PO1={po1_score}, PO2={po2_score}, PO2.5={po2_5_score}, PO3={po3_score}")
            
            # Check if any score exists
            has_any_score = any(score is not None for score in [po1_score, po2_score, po2_5_score, po3_score])
            if not has_any_score:
                self.logger.warning("Brak jakichkolwiek wyników testów")
                return 0.0
            
            # Get weights from campaign
            po1_weight = campaign.get('po1_test_weight', 0)
            po2_weight = campaign.get('po2_test_weight', 0)
            po2_5_weight = campaign.get('po2_5_test_weight', 0)
            po3_weight = campaign.get('po3_test_weight', 0)
            
            po1_weight = float(po1_weight) if po1_weight is not None else 0
            po2_weight = float(po2_weight) if po2_weight is not None else 0
            po2_5_weight = float(po2_5_weight) if po2_5_weight is not None else 0
            po3_weight = float(po3_weight) if po3_weight is not None else 0
            
            self.logger.debug(f"Wagi testów: PO1={po1_weight}, PO2={po2_weight}, PO2.5={po2_5_weight}, PO3={po3_weight}")
            
            # Initialize weighted scores
            weighted_scores = [0]
            total_weights = po1_weight + po2_weight + po2_5_weight + po3_weight
            
            # Add weighted scores only for non-None values
            if po1_score is not None and po1_weight > 0:
                weighted_scores.append(float(po1_score) * po1_weight) 
                self.logger.debug(f"Dodano wynik PO1: {po1_score} * {po1_weight} = {float(po1_score) * po1_weight}")
                
            if po2_score is not None and po2_weight > 0:
                weighted_scores.append(float(po2_score) * po2_weight) 
                self.logger.debug(f"Dodano wynik PO2: {po2_score} * {po2_weight} = {float(po2_score) * po2_weight}")
                
            if po2_5_score is not None and po2_5_weight > 0:
                weighted_scores.append(float(po2_5_score) * po2_5_weight) 
                self.logger.debug(f"Dodano wynik PO2.5: {po2_5_score} * {po2_5_weight} = {float(po2_5_score) * po2_5_weight}")
                
            if po3_score is not None and po3_weight > 0:
                weighted_scores.append(float(po3_score) * po3_weight) 
                self.logger.debug(f"Dodano wynik PO3: {po3_score} * {po3_weight} = {float(po3_score) * po3_weight}")
            
            total_score = sum(weighted_scores) / total_weights
            final_score = round(total_score, 2)
            self.logger.info(f"Obliczono total_score: {final_score} (suma ważona: {sum(weighted_scores)}, suma wag: {total_weights})")
            return final_score
            
        except Exception as e:
            self.logger.error(f"Błąd podczas obliczania całkowitego wyniku: {str(e)}", exc_info=True)
            return 0.0

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
                    po2_5_score,
                    po3_score,
                    access_token_po2,
                    access_token_po3
                ''')\
                .neq('recruitment_status', 'REJECTED')\
                .neq('recruitment_status', 'ACCEPTED')\
                .neq('recruitment_status', 'PO4')\
                .execute()
            
            candidates = response.data
            if not candidates:
                self.logger.info("Brak kandydatów do aktualizacji")
                return
                
            self.logger.info(f"Rozpoczęto aktualizację {len(candidates)} kandydatów")

            for candidate in candidates:
                try:
                    campaign_response = self.supabase.table('campaigns')\
                        .select('''
                            id, 
                            po1_test_id, 
                            po2_test_id, 
                            po2_5_test_id, 
                            po3_test_id, 
                            po1_test_weight, 
                            po2_test_weight, 
                            po2_5_test_weight, 
                            po3_test_weight
                        ''')\
                        .eq('id', candidate['campaign_id'])\
                        .single()\
                        .execute()
                        
                    campaign = campaign_response.data
                    if not campaign:
                        self.logger.warning(f"Nie znaleziono kampanii {candidate['campaign_id']} dla kandydata {candidate['id']}")
                        continue
                    
                    candidate = self.update_candidate_scores(candidate, campaign)
                    
                except Exception as e:
                    self.logger.error(f"Błąd podczas przetwarzania kandydata {candidate['id']}: {str(e)}")
                    continue
                    
            self.logger.info("Zakończono aktualizację kandydatów")
            
        except Exception as e:
            self.logger.error(f"Błąd podczas pobierania listy kandydatów: {str(e)}")
            raise

    def _next_stage(self, candidate: Dict[str, Any]):
        """
        Pobiera następny etap rekrutacji dla kandydata
        
        Args:
            candidate: Dane kandydata
            
        Returns:
            str: Następny etap rekrutacji
        """
        updates = {}
        
        if candidate.get('recruitment_status') == 'PO1':
            updates['recruitment_status'] = 'PO2'
        elif candidate.get('recruitment_status') == 'PO2':
            updates['recruitment_status'] = 'PO2_5'
        elif candidate.get('recruitment_status') == 'PO2_5':
            updates['recruitment_status'] = 'PO3'
        elif candidate.get('recruitment_status') == 'PO3':
            updates['recruitment_status'] = 'PO4'
        
        if updates:
            self.supabase.table('candidates')\
                .update(updates)\
                .eq('id', candidate['id'])\
                .execute()
            self.logger.info(f"Zaktualizowano status kandydata {candidate['id']} na {updates['recruitment_status']}")
        else:
            self.logger.info(f"Status nie może być zaktualizowany dla kandydata {candidate['id']}")


    def _handle_token_generation(self, candidate: Dict[str, Any], stage: str) -> None:
        """
        Generuje token dostępu i wysyła email do kandydata
        
        Args:
            candidate: Dane kandydata
            stage: Etap rekrutacji (PO2/PO3)
        """
        # Get campaign and test data
        campaign_response = self.supabase.table('campaigns')\
            .select('title, po2_test_id, po3_test_id, po1_token_expiry_days, po2_token_expiry_days, po3_token_expiry_days')\
            .eq('id', candidate['campaign_id'])\
            .single()\
            .execute()
        
        if not campaign_response.data:
            self.logger.error(f"Nie znaleziono kampanii dla kandydata {candidate['id']}")
            return
        
        # Get test details
        test_id = None
        if stage == 'PO2':
            test_id = campaign_response.data.get('po2_test_id')
        elif stage == 'PO3':
            test_id = campaign_response.data.get('po3_test_id')
        
        test_details = None
        if test_id:
            test_response = self.supabase.table('tests')\
                .select('title, description, time_limit_minutes')\
                .eq('id', test_id)\
                .single()\
                .execute()
            if test_response.data:
                test_details = test_response.data
        
        # Get expiry days based on stage
        expiry_days = {
            'PO1': campaign_response.data['po1_token_expiry_days'],
            'PO2': campaign_response.data['po2_token_expiry_days'],
            'PO3': campaign_response.data['po3_token_expiry_days']
        }.get(candidate.get('recruitment_status'), 7)
        
        token = generate_access_token()
        test_url = f"{self.config.BASE_URL}/test/candidate/{token}"
        
        current_time = datetime.now()
        token_expiry = (current_time + timedelta(days=expiry_days)).replace(hour=23, minute=59, second=59)
        formatted_expiry = token_expiry.strftime("%d.%m.%Y, %H:%M")
        
        updates = {
            f'access_token_{stage.lower()}': token,
            f'access_token_{stage.lower()}_expires_at': token_expiry.isoformat(),
            f'access_token_{stage.lower()}_is_used': False,
            'recruitment_status': stage,
            'updated_at': current_time.isoformat()
        }
        
        self.supabase.table('candidates')\
            .update(updates)\
            .eq('id', candidate['id'])\
            .execute()

        # Prepare stage name for email
        stage_names = {
            'PO1': 'Test kwalifikacyjny',
            'PO2': 'Test kompetencji',
            'PO3': 'Test końcowy'
        }
        stage_name = stage_names.get(stage, f'Test {stage}')
        
        if self.email_service.send_test_invitation(
            to_email=candidate['email'],
            stage_name=stage_name,
            campaign_title=campaign_response.data['title'],
            test_url=test_url,
            expiry_date=formatted_expiry,
            test_details=test_details
        ):
            self.logger.info(f"Wysłano zaproszenie na {stage_name} do kandydata {candidate['id']}")

    def _get_test_threshold(self, test_id: int) -> int:
        """
        Pobiera próg zaliczenia dla testu
        
        Args:
            test_id: ID testu
            
        Returns:
            int: Próg zaliczenia lub 0 jeśli nie znaleziono
        """
        try:
            test_response = self.supabase.table('tests')\
                .select('passing_threshold')\
                .eq('id', test_id)\
                .single()\
                .execute()
                
            if test_response.data:
                return test_response.data['passing_threshold']
            return 0
                
        except Exception as e:
            self.logger.error(f"Błąd podczas pobierania progu zaliczenia dla testu {test_id}: {str(e)}")
            return 0