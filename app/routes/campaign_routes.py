from flask import Blueprint, render_template, request, jsonify, flash, redirect, session, url_for
from filters import format_datetime
from database import supabase
import secrets
from datetime import datetime
from routes.auth_routes import login_required
from services.group_service import get_user_groups, get_campaign_groups

campaign_bp = Blueprint('campaign', __name__, url_prefix='/campaigns')


@campaign_bp.route('/')
@login_required
def list():
    try:
        # Get all campaigns with tests
        campaigns_response = supabase.table('campaigns')\
            .select("""
                *,
                po1:tests!campaigns_po1_test_id_fkey (test_type, description),
                po2:tests!campaigns_po2_test_id_fkey (test_type, description),
                po3:tests!campaigns_po3_test_id_fkey (test_type, description)
            """)\
            .order('created_at', desc=True)\
            .execute()

        # Format datetime fields and add groups
        campaigns_data = campaigns_response.data or []
        for campaign in campaigns_data:
            if campaign and isinstance(campaign, dict):
                if campaign.get('created_at'):
                    campaign['created_at'] = format_datetime(campaign['created_at'])
                if campaign.get('updated_at'):
                    campaign['updated_at'] = format_datetime(campaign['updated_at'])
                # Add groups to each campaign
                campaign['groups'] = get_campaign_groups(campaign['id'])

        # Get all tests for dropdowns
        tests_response = supabase.table('tests')\
            .select('id, test_type, stage, description')\
            .order('stage')\
            .order('test_type')\
            .execute()
        
        tests_data = tests_response.data or []
        
        # Get user groups
        user_id = session.get('user_id')
        groups = get_user_groups(user_id)
        
        return render_template('campaigns/list.html', 
                             campaigns=campaigns_data, 
                             tests=tests_data,
                             groups=groups)
    
    except Exception as e:
        print(f"Error in campaign list: {str(e)}")  # Debug log
        return render_template('campaigns/list.html',
                             campaigns=[],
                             tests=[],
                             groups=[],
                             error_message=f'Wystąpił błąd podczas pobierania danych: {str(e)}')

@campaign_bp.route('/check-code', methods=['POST'])
def check_code():
    try:
        code = request.json.get('code')
        campaign_id = request.json.get('campaign_id')  # For edit case
        
        if not code:
            return jsonify({'valid': False, 'error': 'Kod kampanii jest wymagany'})
        
        query = supabase.table('campaigns').select('id').eq('code', code)
        
        # If editing, exclude current campaign
        if campaign_id:
            query = query.neq('id', campaign_id)
            
        result = query.execute()
        
        exists = len(result.data) > 0
        return jsonify({
            'valid': not exists,
            'error': 'Kampania o takim kodzie już istnieje' if exists else None
        })
    except Exception as e:
        return jsonify({
            'valid': False,
            'error': f'Błąd podczas sprawdzania kodu: {str(e)}'
        })

@campaign_bp.route('/add', methods=['POST'])
def add():
    try:
        # First check if code exists
        code = request.form.get('code')
        check_result = supabase.table('campaigns')\
            .select('id')\
            .eq('code', code)\
            .execute()
            
        if check_result.data:
            return jsonify({
                'success': False,
                'error': 'Kampania o takim kodzie już istnieje'
            })
        
        groups = request.form.getlist('groups[]')
        if not groups:
            return jsonify({
                'success': False,
                'error': 'Należy wybrać co najmniej jedną grupę'
            })
        
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        campaign_data = {
            'code': code,
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
        campaign_id = result.data[0]['id']
        
        # Add group associations
        for group_id in groups:
            supabase.from_('link_groups_campaigns').insert({
                'group_id': int(group_id),
                'campaign_id': campaign_id
            }).execute()
        
        return jsonify({'success': True, 'id': campaign_id})
    
    except Exception as e:
        print(f"Error details: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@campaign_bp.route('/<int:campaign_id>/data')
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
            
        # Get assigned groups
        campaign.data['groups'] = get_campaign_groups(campaign_id)
            
        return jsonify(campaign.data)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@campaign_bp.route('/<int:campaign_id>/edit', methods=['POST'])
def edit(campaign_id):
    try:
        # First check if code exists (excluding current campaign)
        code = request.form.get('code')
        check_result = supabase.table('campaigns')\
            .select('id')\
            .eq('code', code)\
            .neq('id', campaign_id)\
            .execute()
            
        if check_result.data:
            return jsonify({
                'success': False,
                'error': 'Kampania o takim kodzie już istnieje'
            })
            
        groups = request.form.getlist('groups[]')
        if not groups:
            return jsonify({
                'success': False,
                'error': 'Należy wybrać co najmniej jedną grupę'
            })
        
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        campaign_data = {
            'code': code,
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
            
        # Update group associations
        supabase.from_('link_groups_campaigns')\
            .delete()\
            .eq('campaign_id', campaign_id)\
            .execute()
            
        for group_id in groups:
            supabase.from_('link_groups_campaigns').insert({
                'group_id': int(group_id),
                'campaign_id': campaign_id
            }).execute()
            
        return jsonify({'success': True})
    
    except Exception as e:
        print(f"Error details: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@campaign_bp.route('/<int:campaign_id>/delete', methods=['POST'])
def delete(campaign_id):
    try:
        result = supabase.table('campaigns')\
            .delete()\
            .eq('id', campaign_id)\
            .execute()
            
        return jsonify({'success': True})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@campaign_bp.route('/<int:campaign_id>/generate-link', methods=['POST'])
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