from database import supabase
from common.logger import Logger

logger = Logger.instance()

class UserService:
    @staticmethod
    def get_user_by_email(email) -> dict:
        """
        Pobiera użytkownika z bazy danych na podstawie adresu email.

        Args:
            email (str): Adres email użytkownika.

        Returns:
            dict: Dane użytkownika, jeśli znaleziony.
            None: Jeśli użytkownik nie istnieje.
        """
        try:
            logger.debug(f"Sprawdzanie użytkownika w bazie danych: {email}")
            
            # Zapytanie do Supabase
            response = supabase.table('users')\
                .select('*')\
                .eq('email', email)\
                .execute()
            
            if response.data:
                logger.debug(f"Znaleziono użytkownika: {response.data[0]}")
                return response.data[0]
            
            logger.warning(f"Nie znaleziono użytkownika z emailem: {email}")
            return None

        except Exception as e:
            logger.error(f"Błąd podczas pobierania użytkownika o emailu: {email} - {str(e)}")
            raise RuntimeError(f"Błąd bazy danych: {str(e)}")
