from flask import Blueprint, render_template, redirect, url_for
from routes.auth_routes import login_required

main_bp = Blueprint('main', __name__, url_prefix='')

@main_bp.route('/')
def index():
    return redirect(url_for('main.dashboard'))

@main_bp.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html') 