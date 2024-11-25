from flask import Blueprint, render_template, redirect, url_for

main_bp = Blueprint('main', __name__, url_prefix='')

@main_bp.route('/')
def index():
    return redirect(url_for('main.dashboard'))

@main_bp.route('/dashboard')
def dashboard():
    return render_template('dashboard.html') 