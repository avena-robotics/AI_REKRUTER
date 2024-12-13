from database import supabase
from logger import Logger
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
            campaign_response = supabase.rpc('get_single_campaign_data', {
                'p_campaign_id': campaign_id
            }).execute()
            
            if not campaign_response.data:
                logger.warning(f"Nie znaleziono kampanii o ID {campaign_id}")
                raise CampaignException(
                    message="Nie znaleziono kampanii.",
                    original_error=e
                )
                
            campaign = campaign_response.data[0]
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
                'po1_token_expiry_days': int(data.get('po1_token_expiry_days', 7)),
                'po2_token_expiry_days': int(data.get('po2_token_expiry_days', 7)),
                'po3_token_expiry_days': int(data.get('po3_token_expiry_days', 7)),
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
                'po1_token_expiry_days': int(data.get('po1_token_expiry_days', 7)),
                'po2_token_expiry_days': int(data.get('po2_token_expiry_days', 7)),
                'po3_token_expiry_days': int(data.get('po3_token_expiry_days', 7)),
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