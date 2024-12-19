from database import supabase
from common.logger import Logger
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple, Union
from zoneinfo import ZoneInfo
import secrets
from common.config import Config
from common.email_service import EmailService

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
        campaign_code: Optional[str] = None,
        status: Optional[str] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        search: str = ""
    ) -> List[Dict]:
        """
        Pobiera listę kandydatów z możliwością filtrowania i sortowania.
        
        Args:
            campaign_code (Optional[str]): Kod kampanii do filtrowania
            status (Optional[str]): Status rekrutacji do filtrowania
            sort_by (str): Pole po którym sortować
            sort_order (str): Kierunek sortowania (asc/desc)
            search (str): Fraza do wyszukiwania
            
        Returns:
            List[Dict]: Lista kandydatów
            
        Raises:
            CandidateException: Gdy wystąpi błąd podczas pobierania kandydatów
        """
        try:
            # Build query for candidates with campaign data
            query = supabase.from_("candidates").select("*, campaigns!inner(*)")

            # Apply search if provided
            if search:
                search_pattern = f"%{search.lower()}%"
                query = query.or_(
                    f"first_name.ilike.{search_pattern},"
                    f"last_name.ilike.{search_pattern},"
                    f"email.ilike.{search_pattern},"
                    f"phone.ilike.{search_pattern}"
                )

            # Apply filters
            if campaign_code:
                query = query.eq("campaigns.code", campaign_code)
            if status:
                query = query.eq("recruitment_status", status)

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
                current_time = datetime.now(timezone.utc)
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
    def add_note(candidate_id: int, note_type: str, content: str) -> Dict:
        """
        Dodaje notatkę do kandydata.
        
        Args:
            candidate_id (int): ID kandydata
            note_type (str): Typ notatki
            content (str): Treść notatki
            
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
    def update_note(candidate_id: int, note_id: int, note_type: str, content: str) -> Dict:
        """
        Aktualizuje notatkę kandydata.
        
        Args:
            candidate_id (int): ID kandydata
            note_id (int): ID notatki
            note_type (str): Nowy typ notatki
            content (str): Nowa treść notatki
            
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
    def extend_token(candidate_id: int, stage: str) -> datetime:
        """
        Przedłuża ważność tokenu dostępu do testu.
        
        Args:
            candidate_id (int): ID kandydata
            stage (str): Etap rekrutacji (np. 'po2', 'po3')
            
        Raises:
            CandidateException: Gdy wystąpi błąd podczas przedłużania tokenu
        """
        try:
            # Get candidate and campaign data
            candidate = supabase.from_("candidates")\
                .select("*, campaigns(*)")\
                .eq("id", candidate_id)\
                .single()\
                .execute()
                
            if not candidate.data:
                raise CandidateException(message="Nie znaleziono kandydata")
                
            # Get token expiry days from campaign
            expiry_days = candidate.data['campaigns'].get(f'{stage.lower()}_token_expiry_days', 7)
            logger.debug(f"Przedłużanie tokenu dla kandydata {candidate_id} do etapu {stage} o {expiry_days} dni")
            
            # Calculate new expiry date
            current_time = datetime.now(timezone.utc)
            new_expiry = (current_time + timedelta(days=expiry_days)).replace(hour=23, minute=59, second=59)
            logger.debug(f"Nowa data ważności tokenu: {new_expiry}")
            
            # Update token expiry
            supabase.from_("candidates")\
                .update({
                    f'access_token_{stage.lower()}_expires_at': new_expiry.isoformat(),
                    'updated_at': current_time.isoformat()
                })\
                .eq("id", candidate_id)\
                .execute()
                
            return new_expiry
                
        except Exception as e:
            logger.error(f"Błąd podczas przedłużania tokenu dla kandydata {candidate_id}: {str(e)}")
            raise CandidateException(
                message="Wystąpił błąd podczas przedłużania ważności tokenu",
                original_error=e
            )

