from flask import Blueprint, jsonify
from database import supabase

user_bp = Blueprint('user', __name__, url_prefix='/users')

def check_user_by_email_supabase(email):
    try:
        response = supabase.table('users')\
            .select('*')\
            .eq('email', email)\
            .execute()
        
        if response.data:
            return True, response.data[0]
        return False, "Użytkownik nie ma uprawnień do systemu"
        
    except Exception as e:
        return False, f"Błąd podczas sprawdzania użytkownika: {str(e)}"

