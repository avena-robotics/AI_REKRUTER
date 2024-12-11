from flask import Blueprint, render_template, request, jsonify, flash, redirect, session, url_for
from filters import format_datetime
from database import supabase
import secrets
from datetime import datetime, timedelta, timezone
from routes.auth_routes import login_required
from services.group_service import get_user_groups, get_campaign_groups
from functools import lru_cache
import json
from zoneinfo import ZoneInfo

campaign_bp = Blueprint('campaign', __name__, url_prefix='/campaigns')

# Cache user groups for 5 minutes
@lru_cache(maxsize=1000)
def get_cached_user_groups(user_id, timestamp):
    return get_user_groups(user_id)

@campaign_bp.route('/')
@login_required
def list():
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        # Cache timestamp - updates every 5 minutes
        cache_timestamp = datetime.now().replace(second=0, microsecond=0)
        cache_timestamp = cache_timestamp.replace(minute=cache_timestamp.minute - (cache_timestamp.minute % 5))
        
        # Get user groups with caching
        user_id = session.get('user_id')
        user_groups = get_cached_user_groups(user_id, cache_timestamp)
        user_group_ids = [group['id'] for group in user_groups]
        
        # Convert list to tuple for caching
        user_group_ids_tuple = tuple(user_group_ids)
        
        # Optimize the main query to fetch only necessary data and include groups
        campaigns_response = supabase.rpc('get_campaigns_with_groups', {
            'p_user_group_ids': user_group_ids,  # Keep as list for the query
            'p_limit': per_page,
            'p_offset': (page - 1) * per_page
        }).execute()

        # Get total count for pagination
        count_response = supabase.rpc('get_campaigns_count', {
            'p_user_group_ids': user_group_ids  # Keep as list for the query
        }).execute()
        
        total_count = count_response.data[0]['count'] if count_response.data else 0
        total_pages = (total_count + per_page - 1) // per_page
        
        # Format datetime fields
        campaigns_data = campaigns_response.data or []
        for campaign in campaigns_data:
            if campaign.get('created_at'):
                campaign['created_at'] = format_datetime(campaign['created_at'])
            if campaign.get('updated_at'):
                campaign['updated_at'] = format_datetime(campaign['updated_at'])
        
        # Get all tests for dropdowns (cached) - use tuple for caching
        tests_data = get_cached_tests(user_group_ids_tuple, cache_timestamp)
        
        return render_template('campaigns/campaign_list.html', 
                             campaigns=campaigns_data, 
                             tests=tests_data,
                             groups=user_groups,
                             page=page,
                             total_pages=total_pages,
                             per_page=per_page)
    
    except Exception as e:
        print(f"Error in campaign list: {str(e)}")
        return render_template('campaigns/campaign_list.html',
                             campaigns=[],
                             tests=[],
                             groups=[],
                             error_message=f'Wystąpił błąd podczas pobierania danych: {str(e)}')

# Cache tests for 5 minutes
@lru_cache(maxsize=100)
def get_cached_tests(group_ids_tuple, timestamp):
    """
    Get tests for groups with caching
    Args:
        group_ids_tuple: Tuple of group IDs (must be tuple for caching)
        timestamp: Cache invalidation timestamp
    """
    try:
        # Convert tuple back to list for the query
        group_ids_list = list(group_ids_tuple)
        tests_response = supabase.rpc('get_group_tests', {
            'p_group_ids': group_ids_list
        }).execute()
        return tests_response.data or []
    except Exception as e:
        print(f"Error fetching tests: {str(e)}")
        return []

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
        
        current_time = datetime.now(timezone.utc)
        
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
            'po2_5_test_id': request.form.get('po2_5_test_id') or None,
            'po3_test_id': request.form.get('po3_test_id') or None,
            'po1_test_weight': int(request.form['po1_test_weight']) if request.form.get('po1_test_weight') else 0,
            'po2_test_weight': int(request.form['po2_test_weight']) if request.form.get('po2_test_weight') else 0,
            'po2_5_test_weight': int(request.form['po2_5_test_weight']) if request.form.get('po2_5_test_weight') else 0,
            'po3_test_weight': int(request.form['po3_test_weight']) if request.form.get('po3_test_weight') else 0,
            'po1_token_expiry_days': int(request.form.get('po1_token_expiry_days', 7)),
            'po2_token_expiry_days': int(request.form.get('po2_token_expiry_days', 7)),
            'po3_token_expiry_days': int(request.form.get('po3_token_expiry_days', 7)),
            'created_at': current_time.isoformat(),
            'updated_at': current_time.isoformat()
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
        # Use RPC to get campaign data with a single query
        campaign_response = supabase.rpc('get_single_campaign_data', {
            'p_campaign_id': campaign_id
        }).execute()
        
        print(campaign_response.data)
        
        if not campaign_response.data:
            return jsonify({'error': 'Campaign not found'}), 404
            
        campaign = campaign_response.data[0]
        
        # Format datetime fields
        if campaign.get('created_at'):
            campaign['created_at'] = format_datetime(campaign['created_at'])
        if campaign.get('updated_at'):
            campaign['updated_at'] = format_datetime(campaign['updated_at'])
            
        return jsonify(campaign)
    
    except Exception as e:
        print(f"Error in get_campaign_data: {str(e)}")
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
        
        current_time = datetime.now(timezone.utc)
        
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
            'po2_5_test_id': request.form.get('po2_5_test_id') or None,
            'po3_test_id': request.form.get('po3_test_id') or None,
            'po1_test_weight': int(request.form['po1_test_weight']) if request.form.get('po1_test_weight') else 0,
            'po2_test_weight': int(request.form['po2_test_weight']) if request.form.get('po2_test_weight') else 0,
            'po2_5_test_weight': int(request.form['po2_5_test_weight']) if request.form.get('po2_5_test_weight') else 0,
            'po3_test_weight': int(request.form['po3_test_weight']) if request.form.get('po3_test_weight') else 0,
            'po1_token_expiry_days': int(request.form.get('po1_token_expiry_days', 7)),
            'po2_token_expiry_days': int(request.form.get('po2_token_expiry_days', 7)),
            'po3_token_expiry_days': int(request.form.get('po3_token_expiry_days', 7)),
            'updated_at': current_time.isoformat()
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

@campaign_bp.route('/<int:campaign_id>/duplicate', methods=['POST'])
def duplicate(campaign_id):
    try:
        new_code = request.json.get('code')
        if not new_code:
            return jsonify({
                'success': False,
                'error': 'Nowy kod kampanii jest wymagany'
            })
            
        # Check if code exists
        check_result = supabase.table('campaigns')\
            .select('id')\
            .eq('code', new_code)\
            .execute()
            
        if check_result.data:
            return jsonify({
                'success': False,
                'error': 'Kampania o takim kodzie już istnieje'
            })
            
        # Use the new database function to duplicate campaign
        result = supabase.rpc('duplicate_campaign', {
            'p_campaign_id': campaign_id,
            'p_new_code': new_code
        }).execute()
        
        if result.data:
            return jsonify({
                'success': True,
                'id': result.data[0]['id'],
                'code': result.data[0]['code']
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Nie udało się zduplikować kampanii'
            })
            
    except Exception as e:
        print(f"Error duplicating campaign: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Błąd podczas duplikowania kampanii: {str(e)}'
        })