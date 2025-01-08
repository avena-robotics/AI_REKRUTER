from ldap3 import Server, Connection, ALL, SUBTREE
import ldap3
from common.config import Config
from contextlib import contextmanager
from common.logger import Logger

logger = Logger.instance()
config = Config.instance()

@contextmanager
def ldap_connection(user=None, password=None):
    """Zarządzanie połączeniem LDAP"""
    server = Server(config.LDAP_SERVER, get_info=ALL)
    conn = None
    try:
        # Użycie konta serwisowego, jeśli nie podano poświadczeń użytkownika
        if not user:
            conn = Connection(
                server,
                user=config.LDAP_SERVICE_USER,
                password=config.LDAP_SERVICE_PASSWORD,
                authentication=ldap3.SIMPLE,
                auto_bind=True
            )
        else:
            conn = Connection(
                server,
                user=user,
                password=password,
                authentication=ldap3.SIMPLE,
                auto_bind=True
            )
        yield conn
    except ldap3.core.exceptions.LDAPBindError:
        logger.error(f"LDAP Bind Error: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Błąd podczas tworzenia połączenia LDAP: {str(e)}")
        raise
    finally:
        if conn and conn.bound:
            conn.unbind()

def ldap_authenticate(email, password) -> tuple[bool, dict]:
    """Autentykacja użytkownika przez LDAP"""
    try:
        # Znajdowanie użytkownika w LDAP
        logger.info(f"LDAP: Autentykacja użytkownika {email}")
        with ldap_connection() as conn:
            search_filter = f'(|(mail={email})(userPrincipalName={email}))'
            conn.search(
                search_base=config.LDAP_BASE_DN,
                search_filter=search_filter,
                search_scope=SUBTREE,
                attributes=['distinguishedName', 'mail', 'userPrincipalName']
            )
            if not conn.entries:
                logger.warning(f"Użytkownik {email} nie znaleziony w LDAP")
                return False, { "error": "Użytkownik nie znaleziony"}
            
            logger.info(f"LDAP: Użytkownik {email} znaleziony w LDAP")
            # Pobranie DN użytkownika
            user_dn = conn.entries[0].distinguishedName.value
            
        # Próba uwierzytelnienia użytkownika
        with ldap_connection(user_dn, password):
            logger.info(f"LDAP: Użytkownik {email} pomyślnie uwierzytelniony")
            return True, None
            
    except ldap3.core.exceptions.LDAPBindError:
        logger.warning(f"LDAP: Nieprawidłowe poświadczenia dla {email}")
        return False, { "error": "Nieprawidłowy login lub hasło"}
    except Exception as e:
        logger.error(f"LDAP: Wystąpił błąd podczas logowania dla {email}: {str(e)}")
        return False, { "error": "Wystąpił błąd podczas logowania"}

