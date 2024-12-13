from database import supabase
from logger import Logger
from typing import List, Dict

logger = Logger.instance()

def get_user_groups(user_id: int) -> List[Dict]:
    """
    Pobiera grupy przypisane do użytkownika.
    
    Args:
        user_id (int): ID użytkownika.

    Returns:
        list: Lista grup (id i nazwa).
    """
    try:
        response = supabase.from_("link_groups_users") \
            .select("groups:group_id(*)") \
            .eq("user_id", user_id) \
            .execute()
            
        if not response.data:
            logger.warning(f"Żadna grupa nie została przypisana do użytkownika {user_id}")
            return []
        
        return [item["groups"] for item in response.data]
        
    except Exception as e:
        logger.error(f"Błąd podczas pobierania grup użytkownika: {str(e)}")
        return []

def get_test_groups(test_id: int) -> List[Dict]:
    """
    Pobiera grupy przypisane do testu.

    Args:
        test_id (int): ID testu.

    Returns:
        list: Lista grup (id i nazwa).
    """
    try:
        response = supabase.from_("link_groups_tests") \
            .select("groups:group_id(*)") \
            .eq("test_id", test_id) \
            .execute()
            
        if not response.data:
            logger.warning(f"Żadna grupa nie została przypisana do testu {test_id}")
            return []
        
        return [item["groups"] for item in response.data]
        
    except Exception as e:
        logger.error(f"Błąd podczas pobierania grup testu: {str(e)}")
        return []

def get_campaign_groups(campaign_id: int) -> List[Dict]:
    """
    Pobiera grupy przypisane do kampanii.

    Args:
        campaign_id (int): ID kampanii.

    Returns:
        list: Lista grup (id i nazwa).
    """
    try: 
        response = supabase.from_("link_groups_campaigns") \
            .select("groups:group_id(*)") \
            .eq("campaign_id", campaign_id) \
            .execute()
        
        if not response.data:
            logger.warning(f"Żadna grupa nie została przypisana do kampanii {campaign_id}")
            return []
        
        # Wyciąganie danych z odpowiedzi
        return [item["groups"] for item in response.data]
        
    except Exception as e:
        logger.error(f"Błąd podczas pobierania grup kampanii: {str(e)}")
        return []