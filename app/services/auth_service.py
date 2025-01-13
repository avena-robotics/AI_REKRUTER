from typing import Tuple, Optional, Dict
from database import supabase
from ldap import ldap_authenticate
from services.user_service import UserService
from common.logger import Logger

logger = Logger.instance()

class AuthService:
    @staticmethod
    def authenticate(email: str, password: str) -> Tuple[bool, Optional[str], str]:
        """
        Próbuje uwierzytelnić użytkownika przez Supabase Auth, a następnie przez LDAP.
        """
        # 1. Próba logowania przez Supabase Auth
        try:
            response = supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            if response.user:
                logger.info(f"Użytkownik {email} zalogowany przez Supabase Auth")
                return True, response.user.id, 'supabase'
        except Exception as e:
            logger.debug(f"Logowanie przez Supabase nie powiodło się: {str(e)}")

        # 2. Próba logowania przez LDAP
        auth_success, auth_message = ldap_authenticate(email, password)
        if auth_success:
            # Sprawdzenie czy użytkownik ma uprawnienia w systemie
            user_data = UserService.get_user_by_email(email)
            if user_data:
                # Opcjonalnie: Utworzenie lub aktualizacja konta w Supabase
                AuthService._sync_ldap_user_with_supabase(email, password, user_data)
                return True, user_data['id'], 'ldap'

        return False, None, ''

    @staticmethod
    def _sync_ldap_user_with_supabase(email: str, password: str, user_data: Dict) -> None:
        """
        Synchronizuje użytkownika LDAP z Supabase Auth.
        """
        try:
            # Próba zalogowania się jako admin, aby sprawdzić czy użytkownik istnieje
            response = supabase.auth.admin.list_users()
            logger.debug(f"Lista użytkowników: {response}")
            existing_user = next(
                (user for user in response if user.email == email),
                None
            )
            
            if not existing_user:
                # Utwórz konto w Supabase Auth
                supabase.auth.admin.create_user({
                    "email": email,
                    "password": password,
                    "email_confirm": True,
                    "user_metadata": {
                        "auth_source": "ldap",
                        "ldap_synced": True,
                        "first_name": user_data.get('first_name'),
                        "last_name": user_data.get('last_name')
                    }
                })
                logger.info(f"Utworzono konto Supabase dla użytkownika LDAP: {email}")
            else:
                logger.debug(f"Użytkownik {email} już istnieje w Supabase")
        
        except Exception as e:
            logger.error(f"Błąd podczas synchronizacji z Supabase: {str(e)}")

 