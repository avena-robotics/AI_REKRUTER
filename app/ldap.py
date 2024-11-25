import ldap3
from ldap3 import Server, Connection, ALL, SUBTREE
from config import Config
from contextlib import contextmanager

@contextmanager
def ldap_connection(user=None, password=None):
    """Context manager for LDAP connections"""
    server = Server(Config.LDAP_SERVER, get_info=ALL)
    conn = None
    try:
        # Use service account if no user credentials provided
        if not user:
            conn = Connection(
                server,
                user=Config.LDAP_SERVICE_USER,
                password=Config.LDAP_SERVICE_PASSWORD,
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
        raise
    except Exception as e:
        raise
    finally:
        if conn and conn.bound:
            conn.unbind()

def ldap_authenticate(email, password):
    """Authenticate user against LDAP"""
    try:
        # First find user DN
        with ldap_connection() as conn:
            conn.search(
                search_base=Config.LDAP_BASE_DN,
                search_filter=f'(userPrincipalName={email})',
                search_scope=SUBTREE,
                attributes=['distinguishedName']
            )
            
            if not conn.entries:
                return False, "Użytkownik nie znaleziony"
            
            user_dn = conn.entries[0].distinguishedName.value

        # Then try to authenticate with user credentials
        with ldap_connection(user_dn, password):
            return True, None
            
    except ldap3.core.exceptions.LDAPBindError:
        return False, "Nieprawidłowy login lub hasło"
    except Exception as e:
        return False, "Wystąpił błąd podczas logowania"

