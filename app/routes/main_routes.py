from flask import Blueprint, render_template, redirect, url_for, session
from routes.auth_routes import login_required
from services.group_service import get_user_groups

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    return redirect(url_for('main.dashboard'))

@main_bp.route('/dashboard')
@login_required
def dashboard():
    user_groups = get_user_groups(session.get('user_id'))
    return render_template('dashboard.html', user_groups=user_groups) 