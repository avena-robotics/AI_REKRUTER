from common.openai_service import OpenAIService
from common.test_score_service import TestScoreService
from database import supabase
from common.logger import Logger
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple, Union
from zoneinfo import ZoneInfo
import secrets
from common.config import Config
from common.email_service import EmailService
from common.recalculation_score_service import RecalculationScoreService

logger = Logger.instance()


class CandidateException(Exception):
    """Wyjątek używany do obsługi błędów związanych z kandydatami."""
    def __init__(self, message: str, original_error: Exception = None):
        self.message = message
        self.original_error = original_error
        super().__init__(self.message)


class CandidateService:
    @staticmethod
    def get_candidates(
        user_group_ids: List[int],
        campaign_codes: List[str] = None,
        statuses: List[str] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        search: str = ""
    ) -> List[Dict]:
        """
        Pobiera listę kandydatów z możliwością filtrowania i sortowania.
        
        Args:
            user_group_ids (List[int]): Lista ID grup do których należy użytkownik (wymagane)
            campaign_codes (List[str]): Lista kodów kampanii do filtrowania
            statuses (List[str]): Lista statusów rekrutacji do filtrowania
            sort_by (str): Pole po którym sortować
            sort_order (str): Kierunek sortowania (asc/desc)
            search (str): Fraza do wyszukiwania
            
        Returns:
            List[Dict]: Lista kandydatów
            
        Raises:
            CandidateException: Gdy wystąpi błąd podczas pobierania kandydatów
        """
        try:
            # If no groups assigned, return empty list
            if not user_group_ids:
                return []

            # Get campaign IDs that user has access to
            campaign_access = supabase.from_("link_groups_campaigns")\
                .select("campaign_id")\
                .in_("group_id", user_group_ids)\
                .execute()
            campaign_ids = [item['campaign_id'] for item in campaign_access.data]
            
            # If no campaigns accessible, return empty list
            if not campaign_ids:
                return []

            # Build query for candidates with campaign data
            query = supabase.from_("candidates").select("*, campaigns!inner(*)")

            # Filter by user's campaign access
            query = query.in_("campaign_id", campaign_ids)

            # Apply campaign codes filter
            if campaign_codes:
                query = query.in_("campaigns.code", campaign_codes)

            # Apply status filter
            if statuses:
                query = query.in_("recruitment_status", statuses)

            # Apply search if provided
            if search:
                search_pattern = f"%{search.lower()}%"
                query = query.or_(
                    f"first_name.ilike.{search_pattern},"
                    f"last_name.ilike.{search_pattern},"
                    f"email.ilike.{search_pattern},"
                    f"phone.ilike.{search_pattern}"
                )

            # Apply sorting
            query = query.order(sort_by, desc=(sort_order == "desc"))

            result = query.execute()
            return result.data

        except Exception as e:
            logger.error(f"Błąd podczas pobierania kandydatów: {str(e)}")
            raise CandidateException(
                message="Wystąpił błąd podczas pobierania listy kandydatów",
                original_error=e
            )


    @staticmethod
    def get_candidate_details(candidate_id: int) -> Dict:
        try:
            logger.info(f"Pobieranie szczegółów kandydata {candidate_id}")
            
            result = supabase.rpc(
                'get_candidate_with_tests',
                {'p_candidate_id': candidate_id}
            ).execute()

            if not result.data or not result.data[0]['candidate_data']:
                logger.warning(f"Nie znaleziono kandydata o ID {candidate_id}")
                raise CandidateException(message="Nie znaleziono kandydata")

            logger.debug(f"Pobrano dane kandydata {candidate_id} wraz z testami")
            candidate_data = result.data[0]['candidate_data']
            tests_data = result.data[0]['tests_data'] or {}
            notes_data = result.data[0]['notes_data'] or []

            # Process test data to add question count and total points
            logger.debug(f"Rozpoczęcie przetwarzania danych testów dla kandydata {candidate_id}")
            for stage, test_data in tests_data.items():
                logger.debug(f"Przetwarzanie testu dla etapu {stage}")
                if test_data and 'questions' in test_data:
                    # Calculate question count
                    test_data['question_count'] = len(test_data['questions'])
                    logger.debug(f"Liczba pytań w etapie {stage}: {test_data['question_count']}")
                    
                    # Calculate total points
                    total_points = sum(q['points'] for q in test_data['questions'])
                    test_data['total_points'] = total_points
                    logger.debug(f"Łączna liczba punktów w etapie {stage}: {test_data['total_points']}")
                    
                    # Calculate scored points
                    scored_points = sum(
                        float(q['answer']['score']) 
                        for q in test_data['questions'] 
                        if q.get('answer') and q['answer'].get('score') is not None
                    )
                    test_data['scored_points'] = scored_points
                    logger.debug(f"Łączna liczba punktów w etapie {stage}: {test_data['scored_points']}")
                    
                    # Add started_at and completed_at from candidate data
                    started_at_field = f"{stage.lower()}_started_at"
                    completed_at_field = f"{stage.lower()}_completed_at"
                    
                    # Get timestamps and convert to datetime objects if they exist
                    started_at = candidate_data.get(started_at_field)
                    completed_at = candidate_data.get(completed_at_field)
                    
                    if started_at:
                        started_at = datetime.fromisoformat(started_at.replace('Z', '+00:00'))
                    if completed_at:
                        completed_at = datetime.fromisoformat(completed_at.replace('Z', '+00:00'))
                    
                    test_data['started_at'] = started_at
                    test_data['completed_at'] = completed_at
                    
                    for q in test_data['questions']:
                        logger.debug(f"Pytanie {q['id']}: {q['answer']}")
            return { 
                'candidate': candidate_data,
                'tests': tests_data,
                'notes_data': notes_data,
            }
            
        except CandidateException:
            raise
        except Exception as e:
            logger.error(f"Nieoczekiwany błąd podczas pobierania szczegółów kandydata {candidate_id}: {str(e)}")
            raise CandidateException(
                message="Wystąpił nieoczekiwany błąd podczas pobierania danych kandydata",
                original_error=e
            )


    @staticmethod
    def reject_candidate(candidate_id: int) -> None:
        """
        Odrzuca kandydata.
        
        Args:
            candidate_id (int): ID kandydata
            
        Raises:
            CandidateException: Gdy wystąpi błąd podczas odrzucania kandydata
        """
        try:
            supabase.from_("candidates")\
                .update({
                    'recruitment_status': 'REJECTED',
                    'updated_at': datetime.now(timezone.utc).isoformat()
                })\
                .eq("id", candidate_id)\
                .execute()
                
        except Exception as e:
            logger.error(f"Błąd podczas odrzucania kandydata {candidate_id}: {str(e)}")
            raise CandidateException(
                message="Wystąpił błąd podczas odrzucania kandydata",
                original_error=e
            )


    @staticmethod
    def accept_candidate(candidate_id: int) -> None:
        """
        Akceptuje kandydata.
        
        Args:
            candidate_id (int): ID kandydata
            
        Raises:
            CandidateException: Gdy wystąpi błąd podczas akceptacji kandydata
        """
        try:
            supabase.from_("candidates")\
                .update({
                    'recruitment_status': 'ACCEPTED',
                    'updated_at': datetime.now(timezone.utc).isoformat()
                })\
                .eq("id", candidate_id)\
                .execute()
                
        except Exception as e:
            logger.error(f"Błąd podczas akceptacji kandydata {candidate_id}: {str(e)}")
            raise CandidateException(
                message="Wystąpił błąd podczas akceptacji kandydata",
                original_error=e
            )


    @staticmethod
    def delete_candidate(candidate_id: int) -> None:
        """
        Usuwa kandydata.
        
        Args:
            candidate_id (int): ID kandydata
            
        Raises:
            CandidateException: Gdy wystąpi błąd podczas usuwania kandydata
        """
        try:
            supabase.from_("candidates")\
                .delete()\
                .eq("id", candidate_id)\
                .execute()
                
        except Exception as e:
            logger.error(f"Błąd podczas usuwania kandydata {candidate_id}: {str(e)}")
            raise CandidateException(
                message="Wystąpił błąd podczas usuwania kandydata",
                original_error=e
            )


    @staticmethod
    def move_to_next_stage(candidate_id: int, smtp_config: Dict) -> None:
        """
        Przenosi kandydata do następnego etapu rekrutacji.
        
        Args:
            candidate_id (int): ID kandydata
            smtp_config (Dict): Konfiguracja SMTP do wysyłki maili
            
        Raises:
            CandidateException: Gdy wystąpi błąd podczas przenoszenia kandydata
        """
        logger.info(f"Rozpoczęcie procesu przenoszenia kandydata {candidate_id} do następnego etapu")
        try:
            # Get current candidate data
            candidate = supabase.from_("candidates")\
                .select("*, campaigns(*)")\
                .eq("id", candidate_id)\
                .single()\
                .execute()
                
            if not candidate.data:
                logger.warning(f"Nie znaleziono kandydata {candidate_id}")
                raise CandidateException(message="Nie znaleziono kandydata")
                
            current_status = candidate.data["recruitment_status"]
            logger.debug(f"Obecny status kandydata {candidate_id}: {current_status}")
            campaign = candidate.data["campaigns"]
            
            # If candidate is rejected, determine their last completed stage
            if current_status == "REJECTED":
                if candidate.data["po3_score"] is not None:
                    current_status = "PO3"
                elif candidate.data["po2_score"] is not None:
                    current_status = "PO2"
                elif candidate.data["po1_score"] is not None:
                    current_status = "PO1"
                else:
                    raise CandidateException(message="Nie można określić ostatniego ukończonego etapu")
            
            # Define next stage based on current status
            if current_status == "PO1":
                next_status = "PO2"
                test_id = campaign.get("po2_test_id")
            elif current_status == "PO2":
                next_status = "PO3"
                test_id = campaign.get("po3_test_id")
            elif current_status == "PO3":
                next_status = "PO4"
                test_id = None
            else:
                raise CandidateException(message="Nieprawidłowy obecny etap")

            logger.debug(f"Przygotowanie aktualizacji dla kandydata {candidate_id}")
            updates = {
                "recruitment_status": next_status,
                'updated_at': datetime.now(timezone.utc).isoformat()
            }
            
            # Dla PO4 tylko aktualizujemy status
            if next_status == "PO4":
                supabase.from_("candidates")\
                    .update(updates)\
                    .eq("id", candidate_id)\
                    .execute()
                logger.info(f"Kandydat {candidate_id} został przeniesiony do etapu {next_status}")
                return
            
            # Dla PO2 i PO3 generujemy token i wysyłamy maila
            if next_status in ["PO2", "PO3"]:
                if not test_id:
                    raise CandidateException(
                        message=f"Brak skonfigurowanego testu dla etapu {next_status}"
                    )
                
                logger.debug(f"Generowanie tokenu dla kandydata {candidate_id}")
                
                # Get token expiry days from campaign
                expiry_days = campaign.get(f'po{next_status[-1]}_token_expiry_days', 7)
                
                # Generate token and prepare updates
                current_time = datetime.now()
                token_expiry = (current_time + timedelta(days=expiry_days)).replace(hour=23, minute=59, second=59)
                token = secrets.token_urlsafe(32)
                
                updates.update({
                    f'access_token_{next_status.lower()}': token,
                    f'access_token_{next_status.lower()}_expires_at': token_expiry.isoformat(),
                    f'access_token_{next_status.lower()}_is_used': False
                })
                
                # Update candidate in database
                supabase.from_("candidates")\
                    .update(updates)\
                    .eq("id", candidate_id)\
                    .execute()
                    
                # Send email with test link
                logger.info(f"Wysyłanie emaila do kandydata {candidate_id}")
                try:
                    CandidateService._send_test_email(
                        candidate_data=candidate.data,
                        token=token,
                        current_status=current_status,
                        next_status=next_status,
                        token_expiry=token_expiry,
                        smtp_config=smtp_config
                    )
                    logger.info(f"Email został wysłany do kandydata {candidate_id}")
                except Exception as e:
                    logger.error(f"Błąd podczas wysyłania emaila do kandydata {candidate_id}: {str(e)}")
                    raise CandidateException(message="Nie udało się wysłać emaila z dostępem do testu")
            
            logger.info(f"Kandydat {candidate_id} został przeniesiony do etapu {next_status}")
                
        except CandidateException:
            raise
        except Exception as e:
            logger.error(f"Błąd podczas przenoszenia kandydata {candidate_id} do następnego etapu: {str(e)}")
            raise CandidateException(
                message="Wystąpił błąd podczas przenoszenia kandydata do następnego etapu",
                original_error=e
            )


    @staticmethod
    def _send_test_email(
        candidate_data: Dict,
        token: str,
        current_status: str,
        next_status: str,
        token_expiry: datetime,
        smtp_config: Dict
    ) -> None:
        """
        Wysyła email z linkiem do testu.
        
        Args:
            candidate_data (Dict): Dane kandydata
            token (str): Token dostępu
            current_status (str): Obecny status
            next_status (str): Następny status
            token_expiry (datetime): Data wygaśnięcia tokenu
            smtp_config (Dict): Konfiguracja SMTP
            
        Raises:
            CandidateException: Gdy wystąpi błąd podczas wysyłania emaila
        """
        try:
            # Create EmailService instance
            config = Config.instance()
            email_service = EmailService(config)
            
            # Format expiry date
            formatted_expiry = token_expiry.astimezone(ZoneInfo("Europe/Warsaw")).strftime("%Y-%m-%d %H:%M")
            
            # Generate test URL
            test_url = f"{config.BASE_URL.rstrip('/')}/test/candidate/{token}"
            
            # Map status to stage name
            stage_names = {
                'PO1': 'Test kwalifikacyjny',
                'PO2': 'Test kompetencji',
                'PO3': 'Test końcowy'
            }
            stage_name = stage_names.get(next_status, f'Test {next_status}')
            
            # Get campaign title
            campaign_title = candidate_data.get('campaigns', {}).get('title', 'Rekrutacja')
            
            # Send email using EmailService
            success = email_service.send_test_invitation(
                to_email=candidate_data["email"],
                stage_name=stage_name,
                campaign_title=campaign_title,
                test_url=test_url,
                expiry_date=formatted_expiry,
                test_details=None  # We don't have test details at this point
            )
            
            if not success:
                raise CandidateException(message="Nie udało się wysłać emaila z dostępem do testu")
                
        except Exception as e:
            logger.error(f"Błąd podczas wysyłania emaila do kandydata: {str(e)}")
            raise CandidateException(
                message="Nie udało się wysłać emaila z dostępem do testu",
                original_error=e
            )


    @staticmethod
    def add_note(candidate_id: int, note_type: str, content: str, user_id: int, user_email: str) -> Dict:
        """
        Dodaje notatkę do kandydata.
        
        Args:
            candidate_id (int): ID kandydata
            note_type (str): Typ notatki
            content (str): Treść notatki
            user_id (int): ID użytkownika dodającego notatkę
            user_email (str): Email użytkownika dodającego notatkę
            
        Returns:
            Dict: Dane utworzonej notatki
            
        Raises:
            CandidateException: Gdy wystąpi błąd podczas dodawania notatki
        """
        try:
            result = supabase.from_("candidate_notes")\
                .insert({
                    "candidate_id": candidate_id,
                    "note_type": note_type,
                    "content": content,
                    "user_id": user_id,
                    "user_email": user_email,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "updated_at": datetime.now(timezone.utc).isoformat()
                })\
                .execute()
                
            if not result.data:
                raise CandidateException(message="Nie udało się dodać notatki")
                
            return result.data[0]
            
        except Exception as e:
            logger.error(f"Błąd podczas dodawania notatki dla kandydata {candidate_id}: {str(e)}")
            raise CandidateException(
                message="Wystąpił błąd podczas dodawania notatki",
                original_error=e
            )


    @staticmethod
    def delete_note(candidate_id: int, note_id: int) -> None:
        """
        Usuwa notatkę kandydata.
        
        Args:
            candidate_id (int): ID kandydata
            note_id (int): ID notatki
            
        Raises:
            CandidateException: Gdy wystąpi błąd podczas usuwania notatki
        """
        try:
            result = supabase.from_("candidate_notes")\
                .delete()\
                .eq("id", note_id)\
                .eq("candidate_id", candidate_id)\
                .execute()
                
            if not result.data:
                raise CandidateException(message="Nie znaleziono notatki")
                
        except Exception as e:
            logger.error(f"Błąd podczas usuwania notatki {note_id} kandydata {candidate_id}: {str(e)}")
            raise CandidateException(
                message="Wystąpił błąd podczas usuwania notatki",
                original_error=e
            )


    @staticmethod
    def update_note(candidate_id: int, note_id: int, note_type: str, content: str, user_id: int, user_email: str) -> Dict:
        """
        Aktualizuje notatkę kandydata.
        
        Args:
            candidate_id (int): ID kandydata
            note_id (int): ID notatki
            note_type (str): Nowy typ notatki
            content (str): Nowa treść notatki
            user_id (int): ID użytkownika aktualizującego notatkę
            user_email (str): Email użytkownika aktualizującego notatkę
            
        Returns:
            Dict: Zaktualizowane dane notatki
            
        Raises:
            CandidateException: Gdy wystąpi błąd podczas aktualizacji notatki
        """
        try:
            result = supabase.from_("candidate_notes")\
                .update({
                    "note_type": note_type,
                    "content": content,
                    "user_id": user_id,
                    "user_email": user_email,
                    "updated_at": datetime.now(timezone.utc).isoformat()
                })\
                .eq("id", note_id)\
                .eq("candidate_id", candidate_id)\
                .execute()
                
            if not result.data:
                raise CandidateException(message="Nie znaleziono notatki")
                
            return result.data[0]
            
        except Exception as e:
            logger.error(f"Błąd podczas aktualizacji notatki {note_id} kandydata {candidate_id}: {str(e)}")
            raise CandidateException(
                message="Wystąpił błąd podczas aktualizacji notatki",
                original_error=e
            )


    @staticmethod
    def recalculate_candidate_scores(candidate_id: int) -> Dict:
        """
        Przelicza punkty kandydata.
        
        Args:
            candidate_id (int): ID kandydata
            
        Returns:
            Dict: Wynik przeliczenia z informacją o zmianach
            
        Raises:
            CandidateException: Gdy wystąpi błąd podczas przeliczania punktów
        """
        try:
            config = Config.instance()
            email_service = EmailService(config)
            openai_service = OpenAIService(config)
            test_score_service = TestScoreService(supabase, openai_service)
            recalculation_service = RecalculationScoreService(
                supabase=supabase,
                config=config,
                test_score_service=test_score_service,
                email_service=email_service
            )
            
            result = recalculation_service.recalculate_candidate_scores(candidate_id)
            
            if result.get("status") == "error":
                raise CandidateException(message=result.get("message", "Błąd przeliczania punktów"))
                
            return {
                "success": True,
                "status_changed": result.get("status_changed", False),
                "changes": result.get("changes", {})
            }
            
        except Exception as e:
            logger.error(f"Błąd podczas przeliczania punktów kandydata {candidate_id}: {str(e)}")
            raise CandidateException(
                message="Wystąpił błąd podczas przeliczania punktów kandydata",
                original_error=e
            )

    @staticmethod
    def regenerate_token(candidate_id: int, stage: str) -> Dict[str, Union[bool, str, datetime]]:
        """
        Generuje nowy token dostępu do testu.
        
        Args:
            candidate_id (int): ID kandydata
            stage (str): Etap rekrutacji (np. 'PO2', 'PO3')
            
        Returns:
            Dict: Słownik zawierający nowy token i datę wygaśnięcia
            
        Raises:
            CandidateException: Gdy wystąpi błąd podczas generowania tokenu
        """
        try:
            logger.info(f"Service: Rozpoczęcie regeneracji tokenu dla kandydata {candidate_id}, etap {stage}")
            
            # Get candidate and campaign data
            candidate = supabase.from_("candidates")\
                .select("*, campaigns(*)")\
                .eq("id", candidate_id)\
                .single()\
                .execute()
                
            logger.debug(f"Pobrane dane kandydata: {candidate.data}")
            
            if not candidate.data:
                logger.warning(f"Nie znaleziono kandydata {candidate_id}")
                raise CandidateException(message="Nie znaleziono kandydata")
                
            # Get token expiry days from campaign
            expiry_days = candidate.data['campaigns'].get(f'{stage.lower()}_token_expiry_days', 7)
            logger.debug(f"Dni ważności tokenu: {expiry_days}")
            
            # Generate new token and calculate expiry date
            current_time = datetime.now()
            new_expiry = (current_time + timedelta(days=expiry_days)).replace(hour=23, minute=59, second=59)
            new_token = secrets.token_urlsafe(32)
            
            logger.debug(f"Wygenerowany nowy token: {new_token}, wygasa: {new_expiry}")
            
            # Update token and its expiry
            update_data = {
                f'access_token_{stage.lower()}': new_token,
                f'access_token_{stage.lower()}_expires_at': new_expiry.isoformat(),
                f'access_token_{stage.lower()}_is_used': False,
                'updated_at': current_time.isoformat()
            }

            # Reset test start and completion times based on stage
            if stage == 'PO2':
                update_data.update({
                    'po2_started_at': None,
                    'po2_completed_at': None,
                    'po2_score': None,
                    'po2_5_score': None  # Reset PO2.5 score as well
                })
            elif stage == 'PO3':
                update_data.update({
                    'po3_started_at': None,
                    'po3_completed_at': None,
                    'po3_score': None
                })

            logger.debug(f"Dane do aktualizacji: {update_data}")
            
            # Delete candidate answers based on stage
            if stage == 'PO2':
                # Delete PO2 and PO2.5 answers
                supabase.from_("candidate_answers")\
                    .delete()\
                    .eq("candidate_id", candidate_id)\
                    .in_("stage", ['PO2', 'PO2_5'])\
                    .execute()
                logger.debug("Usunięto odpowiedzi dla testów PO2 i PO2.5")
            elif stage == 'PO3':
                # Delete PO3 answers
                supabase.from_("candidate_answers")\
                    .delete()\
                    .eq("candidate_id", candidate_id)\
                    .eq("stage", 'PO3')\
                    .execute()
                logger.debug("Usunięto odpowiedzi dla testu PO3")
            
            # Update candidate data
            result = supabase.from_("candidates")\
                .update(update_data)\
                .eq("id", candidate_id)\
                .execute()
                
            logger.debug(f"Wynik aktualizacji: {result.data}")
            
            response_data = {
                "success": True,
                "token": new_token,
                "new_expiry": new_expiry.isoformat(),
                "message": "Token został wygenerowany"
            }
            logger.info(f"Token został pomyślnie wygenerowany dla kandydata {candidate_id}")
            return response_data
            
        except Exception as e:
            logger.error(f"Błąd podczas generowania nowego tokenu dla kandydata {candidate_id}: {str(e)}")
            raise CandidateException(
                message="Wystąpił błąd podczas generowania nowego tokenu",
                original_error=e
            )


    @staticmethod
    def invite_to_interview(candidate_id: int) -> None:
        """
        Zmienia status kandydata na 'zaproszono na rozmowę'.
        
        Args:
            candidate_id (int): ID kandydata
            
        Raises:
            CandidateException: Gdy wystąpi błąd podczas zmiany statusu kandydata
        """
        try:
            supabase.from_("candidates")\
                .update({
                    'recruitment_status': 'INVITED_TO_INTERVIEW',
                    'updated_at': datetime.now(timezone.utc).isoformat()
                })\
                .eq("id", candidate_id)\
                .execute()
                
        except Exception as e:
            logger.error(f"Błąd podczas zmiany statusu kandydata {candidate_id} na 'zaproszono na rozmowę': {str(e)}")
            raise CandidateException(
                message="Wystąpił błąd podczas zmiany statusu na 'zaproszono na rozmowę'",
                original_error=e
            )


    @staticmethod
    def set_awaiting_decision(candidate_id: int) -> None:
        """
        Zmienia status kandydata na 'oczekuje na decyzję'.
        
        Args:
            candidate_id (int): ID kandydata
            
        Raises:
            CandidateException: Gdy wystąpi błąd podczas zmiany statusu kandydata
        """
        try:
            supabase.from_("candidates")\
                .update({
                    'recruitment_status': 'AWAITING_DECISION',
                    'updated_at': datetime.now(timezone.utc).isoformat()
                })\
                .eq("id", candidate_id)\
                .execute()
                
        except Exception as e:
            logger.error(f"Błąd podczas zmiany statusu kandydata {candidate_id} na 'oczekuje na decyzję': {str(e)}")
            raise CandidateException(
                message="Wystąpił błąd podczas zmiany statusu na 'oczekuje na decyzję'",
                original_error=e
            )


    @staticmethod
    def get_candidate_email_data(candidate_id: int) -> Dict:
        """
        Pobiera tylko dane kandydata potrzebne do wysłania emaila z zaproszeniem na rozmowę.
        
        Args:
            candidate_id (int): ID kandydata
            
        Returns:
            Dict: Słownik zawierający email kandydata i dane kampanii
            
        Raises:
            CandidateException: Gdy wystąpi błąd podczas pobierania danych
        """
        try:
            result = supabase.from_("candidates")\
                .select("id, email, campaign:campaigns (id, title)")\
                .eq("id", candidate_id)\
                .single()\
                .execute()
                
            if not result.data:
                logger.warning(f"Nie znaleziono kandydata {candidate_id}")
                raise CandidateException(message="Nie znaleziono kandydata")
                
            return result.data
            
        except Exception as e:
            logger.error(f"Błąd podczas pobierania danych email kandydata {candidate_id}: {str(e)}")
            raise CandidateException(
                message="Wystąpił błąd podczas pobierania danych kandydata",
                original_error=e
            )

