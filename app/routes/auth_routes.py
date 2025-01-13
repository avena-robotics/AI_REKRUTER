from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from functools import wraps
from database import supabase
from ldap import ldap_authenticate
from routes.user_routes import check_user_by_email_supabase
from services.auth_service import AuthService

auth_bp = Blueprint('auth', __name__)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            if request.is_json:
                return jsonify({'error': 'Unauthorized'}), 401
            session['next_url'] = request.url
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['username']
        password = request.form['password']
        
        success, user_id, auth_source = AuthService.authenticate(email, password)
        
        if success:
            # Zapisanie w sesji
            session['user_email'] = email
            session['user_id'] = user_id
            session['auth_source'] = auth_source
            
            next_url = session.pop('next_url', None)
            return jsonify({
                'success': True,
                'redirect': next_url or url_for('main.dashboard'),
                'message': 'Zalogowano pomyślnie',
                'type': 'success'
            })
        
        return jsonify({
            'success': False,
            'message': 'Nieprawidłowy login lub hasło',
            'type': 'error'
        })
    
    return render_template('auth/login.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    return jsonify({
        'success': True,
        'redirect': url_for('auth.login'),
        'message': 'Wylogowano pomyślnie',
        'type': 'success'
    }) 