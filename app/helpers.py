import ldap3
from ldap3 import Server, Connection, ALL, SUBTREE

def find_user_dn(username):
    server = Server("ldaps://cfm07adc001.chcemy.polska", get_info=ALL)
    try:
        service_user = 'CN=api service,OU=Funkcyjne,OU=Users,OU=AVENA,DC=chcemy,DC=polska'
        service_password = 'Muhzxib2UIBuibUI@baioubsiub1uibdiqaa98789zbhj'
        base_dn = 'DC=chcemy,DC=polska'
        
        conn = Connection(
            server,
            user=service_user,
            password=service_password,
            authentication=ldap3.SIMPLE,
            auto_bind=True
        )
        
        search_filter = f'(userPrincipalName={username})'
        
        conn.search(
            search_base=base_dn,
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
        server = Server("ldaps://cfm07adc001.chcemy.polska", get_info=ALL)
         
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

def check_group_membership(email, supabase): 
    user_dn, error = find_user_dn(email)
    if error: 
        return False, error

    server = Server("ldaps://cfm07adc001.chcemy.polska", get_info=ALL)
    try:
        service_user = 'CN=api service,OU=Funkcyjne,OU=Users,OU=AVENA,DC=chcemy,DC=polska'
        service_password = 'Muhzxib2UIBuibUI@baioubsiub1uibdiqaa98789zbhj'
        base_dn = 'DC=chcemy,DC=polska'
        
        conn = Connection(
            server,
            user=service_user,
            password=service_password,
            authentication=ldap3.SIMPLE,
            auto_bind=True
        )
         
        conn.search(
            search_base=base_dn,
            search_filter=f'(distinguishedName={user_dn})',
            search_scope=SUBTREE,
            attributes=['cn', 'sAMAccountName', 'mail', 'givenName', 'sn']
        )
        
        if len(conn.entries) == 0: 
            return False, "Nie znaleziono danych użytkownika"
            
        user_data = conn.entries[0]
        user_email = user_data.mail.value if hasattr(user_data, 'mail') else None
        
        if not user_email: 
            return False, "Brak adresu email w LDAP"
            
 
        search_filter = f'(&(distinguishedName={user_dn})(memberOf:1.2.840.113556.1.4.1941:=CN=ai_manager,OU=Grupy,DC=chcemy,DC=polska))'
        
        conn.search(
            search_base=base_dn,
            search_filter=search_filter,
            search_scope=SUBTREE,
            attributes=['cn']
        )
        
        if len(conn.entries) > 0:
            user_response = supabase.table('users').select('*').eq('email', user_email).execute()
            
            if not user_response.data:
                new_user = {
                    'email': user_email,
                    'first_name': user_data.givenName.value if hasattr(user_data, 'givenName') else '',
                    'last_name': user_data.sn.value if hasattr(user_data, 'sn') else '',
                    'phone': user_data.telephoneNumber.value if hasattr(user_data, 'telephoneNumber') else None,
                    'can_edit_tests': True 
                }
                
                try:
                    supabase.table('users').insert(new_user).execute() 
                except Exception as e: 
                    return False, f"Błąd tworzenia konta użytkownika: {str(e)}"
            
            return True, "Użytkownik należy do wymaganej grupy LDAP"
        else: 
            return False, "Brak dostępu - użytkownik nie należy do wymaganej grupy LDAP"
            
    except Exception as e: 
        return False, f"Błąd sprawdzania uprawnień: {str(e)}"
    finally:
        if 'conn' in locals() and conn.bound:
            conn.unbind()