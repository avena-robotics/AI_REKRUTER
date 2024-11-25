from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from functools import wraps
from database import supabase
from helpers import ldap_authenticate, check_group_membership

auth_bp = Blueprint('auth', __name__)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_email' not in session:
            if request.is_json:
                return jsonify({'error': 'Unauthorized'}), 401
            return redirect(url_for('auth.login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['username']
        password = request.form['password']
        
        auth_success, auth_message = ldap_authenticate(email, password)
        if auth_success:
            group_success, group_message = check_group_membership(email, supabase)
            if group_success:
                session['user_email'] = email
                return jsonify({
                    'success': True,
                    'redirect': url_for('main.dashboard'),
                    'message': 'Zalogowano pomyślnie',
                    'type': 'success'
                })
            else:
                return jsonify({
                    'success': False,
                    'message': f'Błąd: {group_message}',
                    'type': 'error'
                })
        else:
            return jsonify({
                'success': False,
                'message': f'Błąd logowania: {auth_message}',
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