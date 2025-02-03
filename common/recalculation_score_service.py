from typing import Optional, List, Dict, Any
from datetime import datetime, timezone, timedelta
from supabase import Client
from common.logger import Logger
from common.config import Config
from common.email_service import EmailService
from common.test_score_service import TestScoreService
from common.token_utils import generate_access_token

class RecalculationException(Exception):
    """Wyjątek używany do obsługi błędów związanych z przeliczaniem wyników."""
    def __init__(self, message: str, original_error: Exception = None):
        self.message = message
        self.original_error = original_error
        super().__init__(self.message)

class RecalculationScoreService:
    """Serwis do ponownego przeliczania wyników testów"""
    
    def __init__(self, 
                 supabase: Client, 
                 config: Config,
                 test_score_service: TestScoreService,
                 email_service: EmailService
    ):
        self.supabase = supabase
        self.config = config
        self.test_score_service = test_score_service
        self.email_service = email_service
        self.logger = Logger.instance()


    def recalculate_candidate_scores(self, candidate_id: int) -> Dict[str, Any]:
        """
        Przelicza ponownie wyniki kandydata dla wszystkich testów.
        
        Args:
            candidate_id (int): ID kandydata
            
        Returns:
            Dict[str, Any]: Wynik przeliczenia z informacją o zmianach
            
        Raises:
            RecalculationException: Gdy wystąpi błąd podczas przeliczania wyników
        """
        try:
            self.logger.info(f"Rozpoczęcie ponownego przeliczania wyników dla kandydata {candidate_id}")
            
            # Get candidate data with campaign
            self.logger.debug(f"Pobieranie danych kandydata {candidate_id} wraz z kampanią")
            candidate_response = self.supabase.table('candidates')\
                .select('*, campaign:campaigns!campaign_id(*)')\
                .eq('id', candidate_id)\
                .single()\
                .execute()
                
            if not candidate_response.data:
                self.logger.warning(f"Nie znaleziono kandydata {candidate_id}")
                return {
                    "status": "error",
                    "message": "Candidate not found"
                }
                
            candidate = candidate_response.data
            campaign = candidate['campaign']
            original_status = candidate.get('recruitment_status')
            current_time = datetime.now(timezone.utc)
            
            self.logger.debug(f"Obecny status kandydata {candidate_id}: {original_status}")
            
            # If candidate is rejected, determine their last completed stage
            last_stage = original_status
            if original_status == "REJECTED" or original_status == "REJECTED_CRITICAL":
                if candidate.get("po3_score") is not None:
                    last_stage = "PO3"
                elif candidate.get("po2_5_score") is not None:
                    last_stage = "PO2_5"
                elif candidate.get("po2_score") is not None:
                    last_stage = "PO2"
                elif candidate.get("po1_score") is not None:
                    last_stage = "PO1"
                self.logger.info(f"Kandydat {candidate_id} był odrzucony na etapie {last_stage}")
            
            updates = {
                'recruitment_status': original_status
            }
            score_changes = {}
            
            # Store original scores for comparison
            original_scores = {
                'po1_score': candidate.get('po1_score'),
                'po2_score': candidate.get('po2_score'),
                'po2_5_score': candidate.get('po2_5_score'),
                'po3_score': candidate.get('po3_score'),
                'total_score': candidate.get('total_score')
            }
            
            self.logger.debug(f"Oryginalne wyniki kandydata {candidate_id}: {original_scores}")

            # Recalculate PO1
            if campaign.get('po1_test_id'):
                result = self.test_score_service.calculate_test_score(
                    candidate_id, 
                    campaign['po1_test_id'],
                    'PO1'
                )
                if result is not None:
                    updates['po1_score'] = result
                    score_changes['PO1'] = {
                        'old': original_scores['po1_score'],
                        'new': result
                    }
                    
                    test_response = self.supabase.table('tests')\
                        .select('passing_threshold')\
                        .eq('id', campaign['po1_test_id'])\
                        .single()\
                        .execute()
                        
                    if test_response.data:
                        passing_threshold = test_response.data['passing_threshold']
                        if result < passing_threshold:
                            updates['recruitment_status'] = 'REJECTED'
                        elif original_status == 'REJECTED' and last_stage == 'PO1' and result >= passing_threshold:
                            updates['recruitment_status'] = 'PO2'
                            result = self._generate_token(candidate, campaign, 'PO2')
                            updates.update(result)
                        elif original_status == 'PO1' and original_scores['po1_score'] is None and result >= passing_threshold:
                            updates['recruitment_status'] = 'PO2'
                            result = self._generate_token(candidate, campaign, 'PO2')
                            updates.update(result)
                        elif result >= passing_threshold:
                            updates['recruitment_status'] = 'PO2'

            # zakładam, że tylko po2 to tylko test EQ
            if campaign.get('po2_test_id') and updates['recruitment_status'] != 'REJECTED':
                result = self.test_score_service.calculate_test_score(
                    candidate_id, 
                    campaign['po2_test_id'],
                    'PO2'
                )

                if result is not None:
                    updates.update(result)

                    if campaign.get('po2_5_test_id') and original_scores['po2_score'] is None:
                        self.test_score_service.create_eq_evaluation_test(
                            candidate_id=candidate['id'],
                            po2_5_test_id=campaign['po2_5_test_id'],
                            eq_scores=result
                        )
                    updates['po2_score'] = 0
                    updates['recruitment_status'] = 'PO2_5'
                    updates['updated_at'] = datetime.now(timezone.utc).isoformat()
                    self.logger.info(f"Ustawiono wynik PO2=0 i zaktualizowano status na PO2_5 dla kandydata {candidate['id']}")

            # Recalculate PO2_5
            if campaign.get('po2_5_test_id') and updates['recruitment_status'] != 'REJECTED':
                result = self.test_score_service.calculate_test_score(
                    candidate_id, 
                    campaign['po2_5_test_id'],
                    'PO2_5'
                )
                if result is not None:
                    updates['po2_5_score'] = result
                    score_changes['PO2_5'] = {
                        'old': original_scores['po2_5_score'],
                        'new': result
                    }
                    
                    test_response = self.supabase.table('tests')\
                        .select('passing_threshold')\
                        .eq('id', campaign['po2_5_test_id'])\
                        .single()\
                        .execute()
                        
                    if test_response.data:
                        passing_threshold = test_response.data['passing_threshold']
                        if result < passing_threshold:
                            updates['recruitment_status'] = 'REJECTED'
                        elif original_status == 'REJECTED' and (last_stage == 'PO2_5' or last_stage == 'PO2') and result >= passing_threshold:
                            updates['recruitment_status'] = 'PO3'
                            result = self._generate_token(candidate, campaign, 'PO3')
                            updates.update(result)
                        elif (original_status == 'PO2_5' or original_status == 'PO2') and original_scores['po2_5_score'] is None and result >= passing_threshold:
                            updates['recruitment_status'] = 'PO3'
                            result = self._generate_token(candidate, campaign, 'PO3')
                            updates.update(result)
                        elif result >= passing_threshold:
                            updates['recruitment_status'] = 'PO3'
                            
            # Recalculate PO3
            if campaign.get('po3_test_id') and updates['recruitment_status'] != 'REJECTED':
                result = self.test_score_service.calculate_test_score(
                    candidate_id, 
                    campaign['po3_test_id'],
                    'PO3'
                )
                if result is not None:
                    updates['po3_score'] = result
                    score_changes['PO3'] = {
                        'old': original_scores['po3_score'],
                        'new': result
                    }
                    
                    test_response = self.supabase.table('tests')\
                        .select('passing_threshold')\
                        .eq('id', campaign['po3_test_id'])\
                        .single()\
                        .execute()
                        
                    if test_response.data:
                        passing_threshold = test_response.data['passing_threshold']
                        if result < passing_threshold:
                            updates['recruitment_status'] = 'REJECTED'
                        elif original_status == 'REJECTED' and last_stage == 'PO3' and result >= passing_threshold:
                            updates['recruitment_status'] = 'PO4'
                        elif original_status == 'PO3' and original_scores['po3_score'] is None and result >= passing_threshold:
                            updates['recruitment_status'] = 'PO4'
                        elif original_status == 'PO4' and original_scores['po3_score'] is not None and result >= passing_threshold:
                            updates['recruitment_status'] = 'PO4'
                        elif result >= passing_threshold:
                            updates['recruitment_status'] = 'PO4'

            
            if updates:
                self.logger.debug(f"Przygotowanie aktualizacji dla kandydata {candidate_id}: {updates}")
                
                # Calculate new total score
                total_score = self._calculate_total_weighted_score(
                    po1_score=updates.get('po1_score', candidate.get('po1_score')),
                    po2_score=updates.get('po2_score', candidate.get('po2_score')),
                    po2_5_score=updates.get('po2_5_score', candidate.get('po2_5_score')),
                    po3_score=updates.get('po3_score', candidate.get('po3_score')),
                    campaign=campaign
                )
                
                updates['total_score'] = total_score
                score_changes['total_score'] = {
                    'old': original_scores['total_score'],
                    'new': total_score
                }
                
                updates['updated_at'] = current_time.isoformat()
                
                # Update database
                self.logger.debug(f"Aktualizacja wyników w bazie danych dla kandydata {candidate_id}")
                self.supabase.table('candidates')\
                    .update(updates)\
                    .eq('id', candidate_id)\
                    .execute()
                
                # Log changes
                self.logger.info(f"Zaktualizowano wyniki kandydata {candidate_id}. Zmiany: {updates}")
                
                # Check if status changed
                if updates.get('recruitment_status') != original_status:
                    self.logger.warning(
                        f"Status kandydata {candidate_id} zmienił się z {original_status} "
                        f"na {updates['recruitment_status']}"
                    )
                
                return {
                    "status": "success",
                    "changes": score_changes,
                    "status_changed": updates.get('recruitment_status') != original_status
                }
                
            else:
                self.logger.info(f"Brak zmian w wynikach dla kandydata {candidate_id}")
                return {
                    "status": "success",
                    "message": "No changes needed"
                }
                
        except Exception as e:
            self.logger.error(f"Błąd podczas przeliczania wyników kandydata {candidate_id}: {str(e)}")
            raise RecalculationException(
                message="Wystąpił błąd podczas przeliczania wyników kandydata",
                original_error=e
            )


    def _calculate_total_weighted_score(self, 
                                      po1_score: Optional[float], 
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
            float: Całkowity ważony wynik
        """
        try:
            # Check if any score exists
            has_any_score = any(score is not None for score in [po1_score, po2_score, po2_5_score, po3_score])
            if not has_any_score:
                return 0.0
            
            # Get weights from campaign
            po1_weight = float(campaign.get('po1_test_weight', 0) or 0)
            po2_weight = float(campaign.get('po2_test_weight', 0) or 0)
            po2_5_weight = float(campaign.get('po2_5_test_weight', 0) or 0)
            po3_weight = float(campaign.get('po3_test_weight', 0) or 0)

            self.logger.debug(f"Wagi testów: PO1={po1_weight}, PO2={po2_weight}, PO2.5={po2_5_weight}, PO3={po3_weight}")
            
            # Initialize weighted scores
            weighted_scores = []
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
            
            if not weighted_scores or total_weights == 0:
                return 0.0
                
            total_score = sum(weighted_scores) / total_weights
            final_score = round(total_score, 2)
            self.logger.info(f"Obliczono total_score: {final_score} (suma ważona: {sum(weighted_scores)}, suma wag: {total_weights})")
            return final_score
            
        except Exception as e:
            self.logger.error(f"Błąd podczas obliczania całkowitego wyniku: {str(e)}")
            return 0.0


    def _generate_token(self, candidate: Dict[str, Any], campaign: dict[str, Any], next_stage: str) -> None:
        """
        Generuje token dostępu i wysyła email do kandydata
        
        Args:
            candidate: Dane kandydata
            campaign: Dane kampanii
            next_stage: Etap rekrutacji (PO2/PO3)
        """
        self.logger.info(f"Generowanie tokenu dla kandydata {candidate['id']} na etap {next_stage}")
        try:
            test_id = {
                'PO2': campaign.get('po2_test_id'),
                'PO2_5': campaign.get('po2_5_test_id'),
                'PO3': campaign.get('po3_test_id')
            }.get(next_stage)
            
            if not test_id:
                self.logger.warning(f"Brak ID testu dla etapu {next_stage}")
                return
            
            test_response = self.supabase.table('tests')\
                .select('title, description, time_limit_minutes')\
                .eq('id', test_id)\
                .single()\
                .execute()
            
            if not test_response.data:
                self.logger.warning(f"Nie znaleziono testu {test_id}")
                return
            
            test_details = test_response.data
            
            # Get expiry days based on stage
            expiry_days = {
                'PO2': campaign.get('po2_token_expiry_days', 7),
                'PO2_5': campaign.get('po2_5_token_expiry_days', 7),
                'PO3': campaign.get('po3_token_expiry_days', 7)
            }.get(next_stage, 7)
            
            token = generate_access_token()
            test_url = f"{self.config.BASE_URL}/test/candidate/{token}"
            
            current_time = datetime.now()
            token_expiry = (current_time + timedelta(days=expiry_days)).replace(hour=23, minute=59, second=59)
            formatted_expiry = token_expiry.strftime("%d.%m.%Y, %H:%M")
            
            updates = {
                f'access_token_{next_stage.lower()}': token,
                f'access_token_{next_stage.lower()}_expires_at': token_expiry.isoformat(),
                f'access_token_{next_stage.lower()}_is_used': False,
                'recruitment_status': next_stage,
                'updated_at': current_time.isoformat()
            }
            
            # Prepare stage name for email
            stage_name = {
                'PO2': 'Test kompetencji',
                'PO2_5': 'Test EQ',
                'PO3': 'Test końcowy'
            }.get(next_stage, f'Test {next_stage}')
            
            if self.email_service.send_test_invitation(
                to_email=candidate['email'],
                stage_name=stage_name,
                campaign_title=campaign.get('title'),
                test_url=test_url,
                expiry_date=formatted_expiry,
                test_details=test_details
            ):
                self.logger.info(f"Wysłano zaproszenie na {stage_name} do kandydata {candidate['id']}")

            return updates

        except Exception as e:
            self.logger.error(f"Błąd podczas generowania tokenu dla kandydata {candidate['id']}: {str(e)}")
            raise


 