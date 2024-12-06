from flask import Blueprint, jsonify
from database import supabase
from logger import Logger

user_bp = Blueprint('user', __name__, url_prefix='/users')
logger = Logger.instance()

def check_user_by_email_supabase(email):
    try:
        logger.debug(f"Sprawdzanie użytkownika po emailu: {email}")
        
        response = supabase.table('users')\
            .select('*')\
            .eq('email', email)\
            .execute()
        
        if response.data:
            logger.debug(f"Użytkownik {email} ma uprawnienia do systemu")
            return True, response.data[0]
            
        logger.warning(f"Użytkownik {email} nie ma uprawnień do systemu")
        return False, "Użytkownik nie ma uprawnień do systemu"
        
    except Exception as e:
        error_msg = f"Błąd podczas sprawdzania uprawnień użytkownika: {str(e)}"
        logger.error(error_msg)
        return False, error_msg

