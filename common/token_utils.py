import secrets

def generate_access_token() -> str:
    """Generuje bezpieczny token dostępu dla kandydata"""
    return secrets.token_urlsafe(32) 