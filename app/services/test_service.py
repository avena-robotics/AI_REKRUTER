from database import supabase
from logger import Logger
from typing import Dict, List

logger = Logger.instance()

class TestException(Exception):
    """Wyjątek używany do obsługi błędów związanych z testami."""
    def __init__(self, message: str, original_error: Exception = None):
        self.message = message
        self.original_error = original_error
        super().__init__(self.message)

class TestService:
    @staticmethod
    def get_tests_for_groups(group_ids: List[int]) -> List[Dict]:
        """
        Pobiera testy dla podanych grup.
    
        Args:
            group_ids (List[int]): Lista ID grup
            
        Returns:
            List[Dict]: Lista testów
            
        Raises:
            TestException: Gdy wystąpi błąd podczas pobierania testów
        """
        try:
            tests_response = supabase.rpc('get_group_tests', {
                'p_group_ids': group_ids
            }).execute()
            
            return tests_response.data or []
            
        except Exception as e:
            logger.error(f"Błąd podczas pobierania testów dla grup {group_ids}: {str(e)}")
            raise TestException(
                message="Błąd podczas pobierania testów dla grup.",
                original_error=e
            )