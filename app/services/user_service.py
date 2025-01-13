from database import supabase
from common.logger import Logger

logger = Logger.instance()

class UserService:
    @staticmethod
    def get_user_by_email_and_source(email: str, auth_source: str) -> dict:
        """
        Pobiera użytkownika z bazy danych na podstawie adresu email i źródła autentykacji.

        Args:
            email (str): Adres email użytkownika
            auth_source (str): Źródło autentykacji ('email' lub 'ldap')

        Returns:
            dict: Dane użytkownika, jeśli znaleziony i aktywny
            None: Jeśli użytkownik nie istnieje lub jest nieaktywny
        """
        try:
            logger.debug(f"Sprawdzanie użytkownika w bazie danych: {email} (source: {auth_source})")
            
            response = supabase.table('users')\
                .select('*')\
                .eq('email', email)\
                .eq('auth_source', auth_source)\
                .eq('is_active', True)\
                .execute()
            
            if response.data:
                logger.debug(f"Znaleziono użytkownika: {response.data[0]}")
                return response.data[0]
            
            logger.warning(f"Nie znaleziono aktywnego użytkownika: {email} (source: {auth_source})")
            return None

        except Exception as e:
            logger.error(f"Błąd podczas pobierania użytkownika: {email} - {str(e)}")
            raise RuntimeError(f"Błąd bazy danych: {str(e)}")
