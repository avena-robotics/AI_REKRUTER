import ldap3
from ldap3 import Server, Connection, ALL, SUBTREE
from config import Config

def find_user_dn(username):
    server = Server(Config.LDAP_SERVER, get_info=ALL)
    try:
        conn = Connection(
            server,
            user=Config.LDAP_SERVICE_USER,
            password=Config.LDAP_SERVICE_PASSWORD,
            authentication=ldap3.SIMPLE,
            auto_bind=True
        )
        
        search_filter = f'(userPrincipalName={username})'
        
        conn.search(
            search_base=Config.LDAP_BASE_DN,
            search_filter=search_filter,
            search_scope=SUBTREE,
            attributes=['distinguishedName']
        )
        
        if len(conn.entries) > 0:
            user_dn = conn.entries[0].distinguishedName.value
            return user_dn, None
        else: 
            return None, "Użytkownik nie znaleziony"
            
    except Exception as e: 
        return None, str(e)
    finally:
        if 'conn' in locals() and conn.bound:
            conn.unbind()

def ldap_authenticate(email, password):
    user_dn, error = find_user_dn(email)
    if error: 
        return False, error
        
    try:
        server = Server(Config.LDAP_SERVER, get_info=ALL)
         
        try:
            conn = Connection(
                server,
                user=user_dn,
                password=password,
                authentication=ldap3.SIMPLE,
                auto_bind=True
            )
            
            if conn.bound: 
                return True, None
                
        except ldap3.core.exceptions.LDAPBindError as bind_error: 
            return False, "Nieprawidłowy login lub hasło"
            
    except Exception as e: 
        return False, "Wystąpił błąd podczas logowania"
    finally:
        if 'conn' in locals() and conn.bound:
            conn.unbind()

