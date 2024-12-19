from flask import Blueprint, render_template, request, jsonify, session
from datetime import datetime, timezone
from routes.auth_routes import login_required
from services.group_service import get_user_groups
from services.campaign_service import CampaignService, CampaignException
from services.test_service import TestService, TestException
from common.logger import Logger

campaign_bp = Blueprint('campaign', __name__, url_prefix='/campaigns')
logger = Logger.instance()

@campaign_bp.route('/')
@login_required
def list():
    try:
        user_id = session.get('user_id')
        user_groups = get_user_groups(user_id)
        user_group_ids = [group['id'] for group in user_groups]
        
        campaigns_data = CampaignService.get_campaigns_for_groups(user_group_ids)
        tests_data = TestService.get_tests_for_groups(user_group_ids)
        
        return render_template('campaigns/campaign_list.html', 
                             campaigns=campaigns_data, 
                             tests=tests_data,
                             groups=user_groups)
        
    except CampaignException as e:
        logger.error(f"Wystąpił błąd podczas pobierania kampanii: {str(e)}")
        return render_template('campaigns/campaign_list.html',
                             campaigns=[],
                             tests=[],
                             groups=[],
                             error_message=e.message)
    
    except TestException as e:
        return render_template('campaigns/campaign_list.html',
                             campaigns=[],
                             tests=[],
                             groups=[],
                             error_message=e.message)
    
    except Exception as e:
        logger.error(f"Wystąpił błąd podczas pobierania kampanii: {str(e)}")
        return render_template('campaigns/campaign_list.html',
                             campaigns=[],
                             tests=[],
                             groups=[],
                             error_message='Wystąpił błąd podczas pobierania kampanii')


@campaign_bp.route('/check-code', methods=['POST'])
def check_code():
    try:
        code = request.json.get('code')
        campaign_id = request.json.get('campaign_id')
        
        if not code:
            return jsonify({'valid': False, 'error': 'Kod kampanii jest wymagany'})
        
        is_valid, error_message = CampaignService.check_campaign_code(code, campaign_id)
        
        return jsonify({
            'valid': is_valid,
            'error': error_message
        })

    except CampaignException as e:
        return jsonify({
            'valid': False,
            'error': e.message
        })
    
    except Exception as e:
        return jsonify({
            'valid': False,
            'error': 'Błąd podczas sprawdzania kodu kampanii'
        })


@campaign_bp.route('/<int:campaign_id>/data')
def get_campaign(campaign_id):
    try:
        campaign = CampaignService.get_campaign_data(campaign_id)
        return jsonify(campaign)
    
    except CampaignException as e:
        return jsonify({'error': e.message}), 404
    
    except Exception as e:
        logger.error(f"Błąd podczas pobierania danych kampanii: {str(e)}")
        return jsonify({'error': str(e)}), 500


@campaign_bp.route('/add', methods=['POST'])
def add():
    try:
        group_id = request.form.get('group_id')
        if not group_id:
            return jsonify({
                'success': False,
                'error': 'Należy wybrać grupę'
            })
        
        success, campaign_id, error = CampaignService.add_campaign(request.form, int(group_id))
        
        return jsonify({
            'success': success,
            'id': campaign_id,
            'error': error
        })
    
    except CampaignException as e:
        return jsonify({
            'success': False,
            'error': e.message
        })
    
    except Exception as e:
        logger.error(f"Błąd podczas dodawania kampanii: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Wystąpił nieoczekiwany błąd podczas dodawania kampanii.'
        })


@campaign_bp.route('/<int:campaign_id>/edit', methods=['POST'])
def edit(campaign_id):
    try:
        # Najpierw sprawdzamy czy kod kampanii jest poprawny i czy jest unikalny
        code = request.form.get('code')
        if not code:
            return jsonify({
                'valid': False,
                'success': False,
                'error': 'Kod kampanii jest wymagany',
            })
        
        is_valid, error_message = CampaignService.check_campaign_code(code, campaign_id)
        if not is_valid:
            return jsonify({
                'valid': False,
                'success': False,
                'error': error_message
            })
      
        group_id = request.form.get('group_id')
        if not group_id:
            return jsonify({
                'success': False,
                'error': 'Należy wybrać grupę'
            })
            
        CampaignService.edit_campaign(campaign_id, request.form, int(group_id))
        return jsonify({
            'success': True,
        })
    
    except CampaignException as e:
        return jsonify({
            'success': False,
            'error': e.message
        })
    
    except Exception as e:
        logger.error(f"Błąd podczas edycji kampanii: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Wystąpił nieoczekiwany błąd podczas edycji kampanii.'
        })


@campaign_bp.route('/<int:campaign_id>/delete', methods=['POST'])
def delete(campaign_id):
    try:
        CampaignService.delete_campaign(campaign_id)
        return jsonify({
            'success': True,
        })
        
    except CampaignException as e:
        return jsonify({
            'success': False,
            'error': e.message
        })
    
    except Exception as e:
        logger.error(f"Błąd podczas usuwania kampanii: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Wystąpił nieoczekiwany błąd podczas usuwania kampanii.'
        })


@campaign_bp.route('/<int:campaign_id>/generate-link', methods=['POST'])
def generate_link(campaign_id):
    try:
        success, token, error = CampaignService.generate_campaign_link(campaign_id)
        
        return jsonify({
            'success': success,
            'token': token,
            'message': 'Link został wygenerowany pomyślnie' if success else error
        })
        
    except CampaignException as e:
        return jsonify({
            'success': False,
            'error': e.message
        })
    
    except Exception as e:
        logger.error(f"Błąd podczas generowania linku: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Wystąpił błąd podczas generowania linku kampanii'
        })


@campaign_bp.route('/group/<int:group_id>/tests')
def get_group_tests(group_id):
    """Pobiera testy dostępne dla danej grupy"""
    try:
        tests = TestService.get_tests_for_groups([group_id])
        return jsonify(tests)
        
    except TestException as e:
        return jsonify({'error': e.message}), 404
        
    except Exception as e:
        logger.error(f"Błąd podczas pobierania testów dla grupy: {str(e)}")
        return jsonify({'error': 'Wystąpił błąd podczas pobierania testów'}), 500

