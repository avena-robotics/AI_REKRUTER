from flask import Blueprint, jsonify
from database import supabase
from logger import Logger
from services.user_service import UserService

user_bp = Blueprint('user', __name__, url_prefix='/users')
logger = Logger.instance()

def check_user_by_email_supabase(email):
    """
    Sprawdza, czy użytkownik z podanym emailem istnieje i ma uprawnienia.
    
    Args:
        email (str): Adres email użytkownika.

    Returns:
        tuple: (bool, dict/str) - True i dane użytkownika, jeśli znaleziony, 
                                  False i komunikat błędu, jeśli nie znaleziony.
    """
    try:        
        user = UserService.get_user_by_email(email)
        if user:
            return True, user
        else:
            return False, {"error": "Użytkownik nie ma uprawnień do systemu"}
        
    except RuntimeError as e:
        return False, {"error": str(e)}
    except Exception as e:
        return False, {"error": "Wystąpił błąd podczas sprawdzania uprawnień użytkownika"}

