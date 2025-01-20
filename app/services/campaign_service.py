import json
from database import supabase
from common.logger import Logger
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple, Union
import secrets

logger = Logger.instance()

class CampaignException(Exception):
    """Wyjątek używany do obsługi błędów związanych z kampaniami."""
    def __init__(self, message: str, original_error: Exception = None):
        self.message = message
        self.original_error = original_error
        super().__init__(self.message)
        

class CampaignService:
    @staticmethod
    def get_campaigns_for_groups(group_ids: List[int]) -> List[Dict]:
        """
        Pobiera kampanie dla podanych grup.
        
        Args:
            group_ids (List[int]): Lista ID grup
            
        Returns:
            List[Dict]: Lista kampanii z danymi
        """
        try:
            campaigns_response = supabase.rpc('get_campaigns_with_groups', {
                'p_user_group_ids': group_ids
            }).execute()

            return campaigns_response.data or []
            
        except Exception as e:
            logger.error(f"Błąd podczas pobierania kampanii: {str(e)}")
            raise CampaignException(
                message="Błąd podczas pobierania kampanii dla grup.",
                original_error=e
            )


    @staticmethod
    def check_campaign_code(code: str, campaign_id: Optional[int] = None) -> Tuple[bool, Optional[str]]:
        """
        Sprawdza czy kod kampanii jest unikalny.
        
        Args:
            code (str): Kod kampanii do sprawdzenia
            campaign_id (Optional[int]): ID kampanii w przypadku edycji
            
        Returns:
            Tuple[bool, Optional[str]]: (Czy kod jest poprawny, Komunikat błędu)
        """
        try:
            if not code:
                return False, 'Kod kampanii jest wymagany'
                
            query = supabase.table('campaigns').select('id').eq('code', code)
            
            if campaign_id:
                query = query.neq('id', campaign_id)
                
            result = query.execute()
            
            exists = len(result.data) > 0
            if exists:
                return False, 'Kampania o takim kodzie już istnieje'
            else:
                return True, None
            
        except Exception as e:
            logger.error(f"Błąd podczas sprawdzania kodu kampanii: {str(e)}")
            raise CampaignException(
                message="Błąd podczas sprawdzania kodu kampanii.",
                original_error=e
            )


    @staticmethod
    def get_campaign_data(campaign_id: int) -> Optional[Dict]:
        """
        Pobiera szczegółowe dane kampanii.
        
        Args:
            campaign_id (int): ID kampanii
            
        Returns:
            Optional[Dict]: Dane kampanii lub None jeśli nie znaleziono
        """
        try:
            response = (
                supabase.from_('campaigns')
                .select('*, link_groups_campaigns(groups(id, name)), po1_test:tests!po1_test_id (test_type, title, description), po2_test:tests!po2_test_id (test_type, title, description), po2_5_test:tests!po2_5_test_id (test_type, title, description), po3_test:tests!po3_test_id (test_type, title, description), interview_email_subject, interview_email_content')
                .eq('id', campaign_id)
                .execute()
            )

            logger.debug(f"Pobieranie danych kampanii o ID {campaign_id}: {json.dumps(response.data, indent=4)}")
            campaign = response.data[0]
            campaign['groups'] = [group['groups'] for group in campaign['link_groups_campaigns']]
            
            return campaign
            
        except Exception as e:
            logger.error(f"Błąd podczas pobierania danych kampanii: {str(e)}")
            raise CampaignException(
                message="Błąd podczas pobierania danych kampanii.",
                original_error=e
            )


    @staticmethod
    def add_campaign(data: Dict, group_id: int) -> Tuple[bool, Optional[int], Optional[str]]:
        """
        Dodaje nową kampanię.
        
        Args:
            data (Dict): Dane kampanii
            group_id (int): ID grupy
            
        Returns:
            Tuple[bool, Optional[int], Optional[str]]: (Sukces, ID kampanii, Komunikat błędu)
        """
        try:
            current_time = datetime.now(timezone.utc)
            
            campaign_data = {
                'code': data.get('code'),
                'title': data.get('title'),
                'workplace_location': data.get('workplace_location'),
                'contract_type': data.get('contract_type'),
                'employment_type': data.get('employment_type'),
                'work_start_date': data.get('work_start_date'),
                'duties': data.get('duties'),
                'requirements': data.get('requirements'),
                'employer_offerings': data.get('employer_offerings'),
                'job_description': data.get('job_description'),
                'salary_range_min': int(data['salary_range_min']) if data.get('salary_range_min') else None,
                'salary_range_max': int(data['salary_range_max']) if data.get('salary_range_max') else None,
                'is_active': bool(data.get('is_active')),
                'po1_test_id': data.get('po1_test_id') or None,
                'po2_test_id': data.get('po2_test_id') or None,
                'po2_5_test_id': data.get('po2_5_test_id') or None,
                'po3_test_id': data.get('po3_test_id') or None,
                'po1_test_weight': int(data['po1_test_weight']) if data.get('po1_test_weight') else 0,
                'po2_test_weight': int(data['po2_test_weight']) if data.get('po2_test_weight') else 0,
                'po2_5_test_weight': int(data['po2_5_test_weight']) if data.get('po2_5_test_weight') else 0,
                'po3_test_weight': int(data['po3_test_weight']) if data.get('po3_test_weight') else 0,
                'po1_token_expiry_days': 36500,  # ~100 years as "infinite"
                'po2_token_expiry_days': int(data.get('po2_token_expiry_days', 7)),
                'po3_token_expiry_days': int(data.get('po3_token_expiry_days', 7)),
                'interview_email_subject': data.get('interview_email_subject'),
                'interview_email_content': data.get('interview_email_content'),
                'created_at': current_time.isoformat(),
                'updated_at': current_time.isoformat()
            }
            
            result = supabase.table('campaigns').insert(campaign_data).execute()
            campaign_id = result.data[0]['id']
            
            # Add group association
            supabase.from_('link_groups_campaigns').insert({
                'group_id': int(group_id),
                'campaign_id': campaign_id
            }).execute()
            
            return True, campaign_id, None
            
        except Exception as e:
            logger.error(f"Błąd podczas dodawania kampanii: {str(e)}")
            raise CampaignException(
                message="Wystąpił błąd podczas dodawania kampanii",
                original_error=e
            )


    @staticmethod
    def edit_campaign(campaign_id: int, data: Dict, group_id: int):
        """
        Edytuje istniejącą kampanię.
        
        Args:
            campaign_id (int): ID kampanii
            data (Dict): Dane kampanii
            group_id (int): ID grupy
            
        Raises:
            CampaignException: Gdy wystąpi błąd podczas edycji kampanii
        """
        try:
            current_time = datetime.now(timezone.utc)
            
            campaign_data = {
                'code': data.get('code'),
                'title': data.get('title'),
                'workplace_location': data.get('workplace_location'),
                'contract_type': data.get('contract_type'),
                'employment_type': data.get('employment_type'),
                'work_start_date': data.get('work_start_date'),
                'duties': data.get('duties'),
                'requirements': data.get('requirements'),
                'employer_offerings': data.get('employer_offerings'),
                'job_description': data.get('job_description'),
                'salary_range_min': int(data['salary_range_min']) if data.get('salary_range_min') else None,
                'salary_range_max': int(data['salary_range_max']) if data.get('salary_range_max') else None,
                'is_active': bool(data.get('is_active')),
                'po1_test_id': data.get('po1_test_id') or None,
                'po2_test_id': data.get('po2_test_id') or None,
                'po2_5_test_id': data.get('po2_5_test_id') or None,
                'po3_test_id': data.get('po3_test_id') or None,
                'po1_test_weight': int(data['po1_test_weight']) if data.get('po1_test_weight') else 0,
                'po2_test_weight': int(data['po2_test_weight']) if data.get('po2_test_weight') else 0,
                'po2_5_test_weight': int(data['po2_5_test_weight']) if data.get('po2_5_test_weight') else 0,
                'po3_test_weight': int(data['po3_test_weight']) if data.get('po3_test_weight') else 0,
                'po1_token_expiry_days': 36500,  # ~100 years as "infinite"
                'po2_token_expiry_days': int(data.get('po2_token_expiry_days', 7)),
                'po3_token_expiry_days': int(data.get('po3_token_expiry_days', 7)),
                'interview_email_subject': data.get('interview_email_subject'),
                'interview_email_content': data.get('interview_email_content'),
                'updated_at': current_time.isoformat()
            }

            supabase.table('campaigns')\
                .update(campaign_data)\
                .eq('id', campaign_id)\
                .execute()

            # Update group association
            supabase.from_('link_groups_campaigns')\
                .delete()\
                .eq('campaign_id', campaign_id)\
                .execute()
                
            supabase.from_('link_groups_campaigns').insert({
                'group_id': int(group_id),
                'campaign_id': campaign_id
            }).execute()

        except Exception as e:
            logger.error(f"Błąd podczas edycji kampanii: {str(e)}")
            raise CampaignException(
                message="Wystąpił błąd podczas edycji kampanii",
                original_error=e 
            )


    @staticmethod
    def delete_campaign(campaign_id: int):
        """
        Usuwa kampanię.
        
        Args:
            campaign_id (int): ID kampanii
            
        Raises:
            CampaignException: Gdy wystąpi błąd podczas usuwania kampanii
        """
        try:
            supabase.table('campaigns')\
                .delete()\
                .eq('id', campaign_id)\
                .execute()
                
        except Exception as e:
            error_message = str(e)
            
            if 'candidates_campaign_id_fkey' in error_message:
                raise CampaignException(
                    message="Nie można usunąć kampanii, ponieważ jest wykorzystywana w odpowiedziach kandydata",
                    original_error=e
                )
                
            logger.error(f"Błąd podczas usuwania kampanii: {error_message}")
            raise CampaignException(
                message="Wystąpił błąd podczas usuwania kampanii",
                original_error=e
            )


    @staticmethod
    def generate_campaign_link(campaign_id: int) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Generuje uniwersalny link dostępu do kampanii.
        
        Args:
            campaign_id (int): ID kampanii
            
        Returns:
            Tuple[bool, Optional[str], Optional[str]]: (Sukces, Token, Komunikat błędu)
            
        Raises:
            CampaignException: Gdy wystąpi błąd podczas generowania linku
        """
        try:
            token = secrets.token_urlsafe(32)
            
            supabase.table('campaigns')\
                .update({'universal_access_token': token})\
                .eq('id', campaign_id)\
                .execute()
            
            return True, token, None
        
        except Exception as e:
            logger.error(f"Błąd podczas generowania linku: {str(e)}")
            raise CampaignException(
                message="Błąd podczas generowania linku kampanii.",
                original_error=e
            )

    @staticmethod
    def get_campaigns_for_dropdown() -> List[Dict]:
        """
        Pobiera listę kampanii do wyświetlenia w dropdownie.
        
        Returns:
            List[Dict]: Lista kampanii z kodem i tytułem
            
        Raises:
            CampaignException: Gdy wystąpi błąd podczas pobierania kampanii
        """
        try:
            result = supabase.from_("campaigns")\
                .select("code, title")\
                .order("code", desc=False)\
                .execute()
                
            return result.data
                
        except Exception as e:
            logger.error(f"Błąd podczas pobierania listy kampanii: {str(e)}")
            raise CampaignException(
                message="Wystąpił błąd podczas pobierania listy kampanii",
                original_error=e
            )

    @staticmethod
    def get_interview_email_template(campaign_id: int) -> Dict[str, str]:
        """
        Pobiera szablon emaila z zaproszeniem na rozmowę dla danej kampanii.
        
        Args:
            campaign_id (int): ID kampanii
            
        Returns:
            Dict[str, str]: Słownik z subject i content
            
        Raises:
            CampaignException: Gdy wystąpi błąd podczas pobierania szablonu
        """
        try:
            logger.info(f"Pobieranie szablonu email dla kampanii {campaign_id}")
            
            result = supabase.from_('campaigns')\
                .select('interview_email_subject, interview_email_content')\
                .eq('id', campaign_id)\
                .execute()
                
            logger.debug(f"Wynik zapytania dla kampanii {campaign_id}: {json.dumps(result.data, indent=2)}")
                
            if not result.data:
                logger.warning(f"Nie znaleziono szablonu dla kampanii {campaign_id}")
                return {
                    'subject': '',
                    'content': ''
                }
                
            template = result.data[0]
            logger.info(f"Pobrano szablon dla kampanii {campaign_id}")
            logger.debug(f"Zawartość szablonu: {json.dumps(template, indent=2)}")
            
            return {
                'subject': template.get('interview_email_subject', ''),
                'content': template.get('interview_email_content', '')
            }
                
        except Exception as e:
            logger.error(f"Błąd podczas pobierania szablonu email dla kampanii {campaign_id}: {str(e)}")
            import traceback
            logger.error(f"Stacktrace: {traceback.format_exc()}")
            raise CampaignException(
                message="Wystąpił błąd podczas pobierania szablonu email",
                original_error=e
            )

    @staticmethod
    def update_interview_email_template(campaign_id: int, subject: str, content: str) -> None:
        """
        Aktualizuje szablon emaila z zaproszeniem na rozmowę dla danej kampanii.
        
        Args:
            campaign_id (int): ID kampanii
            subject (str): Temat emaila
            content (str): Treść emaila
            
        Raises:
            CampaignException: Gdy wystąpi błąd podczas aktualizacji szablonu
        """
        try:
            logger.info(f"Aktualizacja szablonu email dla kampanii {campaign_id}")
            logger.debug(f"Nowa treść szablonu: Subject: {subject}, Content length: {len(content)}")
            
            update_data = {
                'interview_email_subject': subject,
                'interview_email_content': content,
                'updated_at': datetime.now(timezone.utc).isoformat()
            }
            
            result = supabase.from_('campaigns')\
                .update(update_data)\
                .eq('id', campaign_id)\
                .execute()
                
            logger.debug(f"Wynik aktualizacji dla kampanii {campaign_id}: {json.dumps(result.data, indent=2)}")
            logger.info(f"Pomyślnie zaktualizowano szablon dla kampanii {campaign_id}")
                
        except Exception as e:
            logger.error(f"Błąd podczas aktualizacji szablonu email dla kampanii {campaign_id}: {str(e)}")
            import traceback
            logger.error(f"Stacktrace: {traceback.format_exc()}")
            raise CampaignException(
                message="Wystąpił błąd podczas aktualizacji szablonu email",
                original_error=e
            )