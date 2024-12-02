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
        # Get user groups first
        user_id = session.get('user_id')
        user_groups = get_user_groups(user_id)
        user_group_ids = [group['id'] for group in user_groups]
        
        # Get all campaigns with tests
        campaigns_response = supabase.table('campaigns')\
            .select("""
                *,
                po1:tests!campaigns_po1_test_id_fkey (test_type, title, description),
                po2:tests!campaigns_po2_test_id_fkey (test_type, title, description),
                po3:tests!campaigns_po3_test_id_fkey (test_type, title, description)
            """)\
            .order('created_at', desc=True)\
            .execute()

        # Format datetime fields and filter campaigns
        filtered_campaigns = []
        campaigns_data = campaigns_response.data or []
        
        for campaign in campaigns_data:
            if campaign and isinstance(campaign, dict):
                # Format datetime fields
                if campaign.get('created_at'):
                    campaign['created_at'] = format_datetime(campaign['created_at'])
                if campaign.get('updated_at'):
                    campaign['updated_at'] = format_datetime(campaign['updated_at'])
                
                # Get groups for this campaign
                campaign_groups = get_campaign_groups(campaign['id'])
                campaign['groups'] = campaign_groups
                
                # Check if campaign has any groups that user belongs to
                campaign_group_ids = [group['id'] for group in campaign_groups]
                if any(group_id in user_group_ids for group_id in campaign_group_ids):
                    filtered_campaigns.append(campaign)

        # Get all tests for dropdowns
        tests_response = supabase.table('tests')\
            .select('id, test_type, title, description')\
            .order('test_type')\
            .execute()
        
        tests_data = tests_response.data or []
        
        return render_template('campaigns/list.html', 
                             campaigns=filtered_campaigns, 
                             tests=tests_data,
                             groups=user_groups)
    
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
        
        group_id = request.form.get('group_id')
        if not group_id:
            return jsonify({
                'success': False,
                'error': 'Należy wybrać grupę'
            })
        
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Explicitly define the fields to be inserted
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
            'po1_test_weight': int(request.form['po1_test_weight']) if request.form.get('po1_test_weight') else 0,
            'po2_test_weight': int(request.form['po2_test_weight']) if request.form.get('po2_test_weight') else 0,
            'po3_test_weight': int(request.form['po3_test_weight']) if request.form.get('po3_test_weight') else 0,
            'created_at': current_time,
            'updated_at': current_time
        }
        
        # Ensure no ID is included in the insert
        if 'id' in campaign_data:
            del campaign_data['id']
        
        result = supabase.table('campaigns').insert(campaign_data).execute()
        campaign_id = result.data[0]['id']
        
        # Add single group association
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
        print(f"Error in get_campaign_data: {str(e)}")  # Debug log
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
            
        group_id = request.form.get('group_id')
        if not group_id:
            return jsonify({
                'success': False,
                'error': 'Należy wybrać grupę'
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
            'po1_test_weight': int(request.form['po1_test_weight']) if request.form.get('po1_test_weight') else 0,
            'po2_test_weight': int(request.form['po2_test_weight']) if request.form.get('po2_test_weight') else 0,
            'po3_test_weight': int(request.form['po3_test_weight']) if request.form.get('po3_test_weight') else 0,
            'updated_at': current_time
        }

        supabase.table('campaigns')\
            .update(campaign_data)\
            .eq('id', campaign_id)\
            .execute()

        # Update group association
        supabase.from_('link_groups_campaigns')\
            .delete()\
            .eq('campaign_id', campaign_id)\
            .execute()
            
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
        supabase.table('campaigns')\
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

# Add new endpoint to get tests for a specific group
@campaign_bp.route('/group/<int:group_id>/tests')
def get_group_tests(group_id):
    try:
        # Get all tests associated with this group
        link_response = supabase.from_('link_groups_tests')\
            .select('test_id')\
            .eq('group_id', group_id)\
            .execute()
            
        if not link_response.data:
            return jsonify([])
            
        test_ids = [item['test_id'] for item in link_response.data]
        
        tests_response = supabase.from_('tests')\
            .select('id, test_type, title, description')\
            .in_('id', test_ids)\
            .order('test_type')\
            .execute()
            
        return jsonify(tests_response.data or [])
    except Exception as e:
        print(f"Error getting group tests: {str(e)}")
        return jsonify([])