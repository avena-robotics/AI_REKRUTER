from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from database import supabase
import secrets
from datetime import datetime

campaign_bp = Blueprint('campaign', __name__)

def format_datetime(dt_str):
    if not dt_str:
        return None
    try:
        if '.' in dt_str:
            dt_str = dt_str.split('.')[0]
        dt = datetime.fromisoformat(dt_str.replace('Z', ''))
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    except Exception as e:
        print(f"Error formatting datetime {dt_str}: {str(e)}")
        return dt_str

@campaign_bp.route('/campaigns')
def list():
    try:
        # Get all campaigns with tests
        campaigns = supabase.table('campaigns')\
            .select("""
                *,
                po1:tests!campaigns_po1_test_id_fkey (test_type, description),
                po2:tests!campaigns_po2_test_id_fkey (test_type, description),
                po3:tests!campaigns_po3_test_id_fkey (test_type, description)
            """)\
            .order('created_at', desc=True)\
            .execute()

        # Format datetime fields
        for campaign in campaigns.data:
            if campaign.get('created_at'):
                campaign['created_at'] = format_datetime(campaign['created_at'])
            if campaign.get('updated_at'):
                campaign['updated_at'] = format_datetime(campaign['updated_at'])

        # Get all tests for dropdowns
        tests = supabase.table('tests')\
            .select('id, test_type, stage, description')\
            .order('stage')\
            .order('test_type')\
            .execute()
        
        return render_template('campaigns/list.html', 
                             campaigns=campaigns.data, 
                             tests=tests.data)
    
    except Exception as e:
        flash(f'Wystąpił błąd podczas pobierania danych: {str(e)}', 'error')
        return redirect(url_for('main.index'))

@campaign_bp.route('/campaigns/add', methods=['POST'])
def add():
    try:
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        campaign_data = {
            'code': request.form.get('code'),
            'title': request.form.get('title'),
            'workplace_location': request.form.get('workplace_location'),
            'contract_type': request.form.get('contract_type'),
            'employment_type': request.form.get('employment_type'),
            'work_start_date': request.form.get('work_start_date'),
            'duties': request.form.get('duties'),
            'requirements': request.form.get('requirements'),
            'employer_offerings': request.form.get('employer_offerings'),
            'job_description': request.form.get('job_description'),
            'salary_range_min': int(request.form['salary_range_min']) if request.form.get('salary_range_min') else None,
            'salary_range_max': int(request.form['salary_range_max']) if request.form.get('salary_range_max') else None,
            'is_active': bool(request.form.get('is_active')),
            'po1_test_id': request.form.get('po1_test_id') or None,
            'po2_test_id': request.form.get('po2_test_id') or None,
            'po3_test_id': request.form.get('po3_test_id') or None,
            'created_at': current_time,
            'updated_at': current_time
        }
        
        result = supabase.table('campaigns').insert(campaign_data).execute()
        return jsonify({'success': True, 'id': result.data[0]['id']})
    
    except Exception as e:
        print(f"Error details: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@campaign_bp.route('/campaigns/<int:campaign_id>/data')
def get_campaign_data(campaign_id):
    try:
        campaign = supabase.table('campaigns')\
            .select("""
                *,
                po1:tests!campaigns_po1_test_id_fkey (test_type, description),
                po2:tests!campaigns_po2_test_id_fkey (test_type, description),
                po3:tests!campaigns_po3_test_id_fkey (test_type, description)
            """)\
            .eq('id', campaign_id)\
            .single()\
            .execute()
        
        if not campaign.data:
            return jsonify({'error': 'Campaign not found'}), 404
            
        # Format datetime fields
        if campaign.data.get('created_at'):
            campaign.data['created_at'] = format_datetime(campaign.data['created_at'])
        if campaign.data.get('updated_at'):
            campaign.data['updated_at'] = format_datetime(campaign.data['updated_at'])
            
        return jsonify(campaign.data)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@campaign_bp.route('/campaigns/<int:campaign_id>/edit', methods=['POST'])
def edit(campaign_id):
    try:
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        campaign_data = {
            'code': request.form.get('code'),
            'title': request.form.get('title'),
            'workplace_location': request.form.get('workplace_location'),
            'contract_type': request.form.get('contract_type'),
            'employment_type': request.form.get('employment_type'),
            'work_start_date': request.form.get('work_start_date'),
            'duties': request.form.get('duties'),
            'requirements': request.form.get('requirements'),
            'employer_offerings': request.form.get('employer_offerings'),
            'job_description': request.form.get('job_description'),
            'salary_range_min': int(request.form['salary_range_min']) if request.form.get('salary_range_min') else None,
            'salary_range_max': int(request.form['salary_range_max']) if request.form.get('salary_range_max') else None,
            'is_active': bool(request.form.get('is_active')),
            'po1_test_id': request.form.get('po1_test_id') or None,
            'po2_test_id': request.form.get('po2_test_id') or None,
            'po3_test_id': request.form.get('po3_test_id') or None,
            'updated_at': current_time
        }
        
        result = supabase.table('campaigns')\
            .update(campaign_data)\
            .eq('id', campaign_id)\
            .execute()
            
        return jsonify({'success': True})
    
    except Exception as e:
        print(f"Error details: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@campaign_bp.route('/campaigns/<int:campaign_id>/delete', methods=['POST'])
def delete(campaign_id):
    try:
        result = supabase.table('campaigns')\
            .delete()\
            .eq('id', campaign_id)\
            .execute()
            
        return jsonify({'success': True})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@campaign_bp.route('/campaigns/<int:campaign_id>/generate-link', methods=['POST'])
def generate_link(campaign_id):
    try:
        token = secrets.token_urlsafe(32)
        
        result = supabase.table('campaigns')\
            .update({'universal_access_token': token})\
            .eq('id', campaign_id)\
            .execute()
        
        return jsonify({
            'success': True,
            'token': token,
            'message': 'Link został wygenerowany pomyślnie'
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})