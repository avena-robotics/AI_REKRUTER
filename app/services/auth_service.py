from typing import Tuple, Optional
from ldap import ldap_authenticate
from services.user_service import UserService
from common.logger import Logger

logger = Logger.instance()

class AuthService:
    @staticmethod
    def authenticate(email: str, password: str) -> Tuple[bool, Optional[int], str]:
        """
        Próbuje uwierzytelnić użytkownika lokalnie, a następnie przez LDAP.
        
        Returns:
            Tuple[bool, Optional[int], str]: 
            - bool: Czy autentykacja się powiodła
            - int: ID użytkownika lub None
            - str: Źródło autentykacji ('email' lub 'ldap')
        """
        # 1. Próba logowania lokalnego
        email_user = UserService.get_user_by_email_and_source(email, 'email')
        if email_user and email_user.get('password'):
            if email_user['password'] == password:
                logger.info(f"Użytkownik {email} zalogowany")
                return True, email_user['id'], 'email'
            logger.debug(f"Nieprawidłowe hasło dla lokalnego użytkownika: {email}")
            return False, None, ''

        # 2. Próba logowania przez LDAP
        auth_success, auth_message = ldap_authenticate(email, password)
        if auth_success:
            # Sprawdzenie czy użytkownik ma uprawnienia w systemie
            ldap_user = UserService.get_user_by_email_and_source(email, 'ldap')
            if ldap_user:
                logger.info(f"Użytkownik {email} zalogowany przez LDAP")
                return True, ldap_user['id'], 'ldap'

        return False, None, ''

 