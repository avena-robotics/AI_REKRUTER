from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from database import supabase
import uuid
from datetime import datetime

campaign_bp = Blueprint('campaign', __name__, url_prefix='/campaigns')

@campaign_bp.route('/')
def list():
    campaigns = supabase.table('campaigns').select('*').execute()
    return render_template('campaigns/list.html', campaigns=campaigns.data)

@campaign_bp.route('/<int:id>/generate-link', methods=['POST'])
def generate_link(id):
    try:
        # Generate a unique token
        token = str(uuid.uuid4())
        
        # Update campaign with the new token
        supabase.table('campaigns')\
            .update({'universal_access_token': token})\
            .eq('id', id)\
            .execute()
            
        flash('Link został wygenerowany pomyślnie', 'success')
    except Exception as e:
        flash(f'Wystąpił błąd podczas generowania linku: {str(e)}', 'danger')
    
    return redirect(url_for('campaign.list'))

@campaign_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
def edit(id):
    if request.method == 'POST':
        try:
            campaign_data = {
                'code': request.form['code'],
                'title': request.form['title'],
                'workplace_location': request.form['workplace_location'],
                'contract_type': request.form['contract_type'],
                'employment_type': request.form['employment_type'],
                'work_start_date': request.form['work_start_date'],
                'duties': request.form['duties'],
                'requirements': request.form['requirements'],
                'employer_offerings': request.form['employer_offerings'],
                'job_description': request.form['job_description'],
                'salary_range_min': int(request.form['salary_range_min']) if request.form['salary_range_min'] else None,
                'salary_range_max': int(request.form['salary_range_max']) if request.form['salary_range_max'] else None,
                'is_active': 'is_active' in request.form,
                'updated_at': datetime.now().isoformat()
            }
            
            supabase.table('campaigns')\
                .update(campaign_data)\
                .eq('id', id)\
                .execute()
                
            flash('Kampania została zaktualizowana pomyślnie', 'success')
            return redirect(url_for('campaign.list'))
        except Exception as e:
            flash(f'Wystąpił błąd: {str(e)}', 'danger')
    
    campaign = supabase.table('campaigns')\
        .select('*')\
        .eq('id', id)\
        .single()\
        .execute()
        
    return render_template('campaigns/edit.html', campaign=campaign.data)

@campaign_bp.route('/<int:id>/delete', methods=['POST'])
def delete(id):
    try:
        supabase.table('campaigns')\
            .delete()\
            .eq('id', id)\
            .execute()
        return jsonify({'message': 'Kampania została usunięta pomyślnie'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@campaign_bp.route('/add', methods=['GET', 'POST'])
def add():
    if request.method == 'POST':
        try:
            campaign_data = {
                'code': request.form['code'],
                'title': request.form['title'],
                'workplace_location': request.form['workplace_location'],
                'contract_type': request.form['contract_type'],
                'employment_type': request.form['employment_type'],
                'work_start_date': request.form['work_start_date'],
                'duties': request.form['duties'],
                'requirements': request.form['requirements'],
                'employer_offerings': request.form['employer_offerings'],
                'job_description': request.form['job_description'],
                'salary_range_min': int(request.form['salary_range_min']),
                'salary_range_max': int(request.form['salary_range_max'])
            }
            
            supabase.table('campaigns').insert(campaign_data).execute()
            flash('Kampania została dodana pomyślnie', 'success')
            return redirect(url_for('campaign.list'))
        except Exception as e:
            flash(f'Wystąpił błąd: {str(e)}', 'danger')
    
    return render_template('campaigns/add.html')

@campaign_bp.route('/<int:id>/data')
def get_campaign_data(id):
    try:
        campaign = supabase.table('campaigns')\
            .select('*')\
            .eq('id', id)\
            .single()\
            .execute()
            
        if not campaign.data:
            return jsonify({'error': 'Campaign not found'}), 404
            
        return jsonify(campaign.data), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500 