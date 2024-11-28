from flask import Blueprint, render_template, request, jsonify, redirect, url_for, abort
from database import supabase
from datetime import datetime, timedelta

test_public_bp = Blueprint('test_public', __name__)

def get_universal_test_info(token):
    """Get test information for universal access token"""
    try:
        campaign = supabase.table('campaigns')\
            .select('*, po1:tests!campaigns_po1_test_id_fkey(*)')\
            .eq('universal_access_token', token)\
            .single()\
            .execute()
        
        if campaign.data:
            return {
                'campaign': campaign.data,
                'test': campaign.data['po1'],
                'stage': 'PO1'
            }
    except:
        return None
    return None

def get_candidate_test_info(token):
    """Get test information for candidate-specific token"""
    try:
        # Try PO2 token
        candidate = supabase.table('candidates')\
            .select('*, campaign:campaigns(*)')\
            .eq('access_token_po2', token)\
            .single()\
            .execute()
        
        if candidate.data:
            # Get PO2 test info
            test = supabase.table('tests')\
                .select('*')\
                .eq('id', candidate.data['campaign']['po2_test_id'])\
                .single()\
                .execute()
            
            if test.data:
                return {
                    'campaign': candidate.data['campaign'],
                    'test': test.data,
                    'stage': 'PO2',
                    'candidate': candidate.data
                }
    except:
        pass
    
    try:
        # Try PO3 token
        candidate = supabase.table('candidates')\
            .select('*, campaign:campaigns(*)')\
            .eq('access_token_po3', token)\
            .single()\
            .execute()
        
        if candidate.data:
            # Get PO3 test info
            test = supabase.table('tests')\
                .select('*')\
                .eq('id', candidate.data['campaign']['po3_test_id'])\
                .single()\
                .execute()
            
            if test.data:
                return {
                    'campaign': candidate.data['campaign'],
                    'test': test.data,
                    'stage': 'PO3',
                    'candidate': candidate.data
                }
    except:
        pass
    
    return None

def check_token_status(token):
    """Check if token is used and get test info"""
    try:
        # Try PO2 token first
        candidate = supabase.table('candidates')\
            .select('*, campaign:campaigns(*)')\
            .eq('access_token_po2', token)\
            .single()\
            .execute()
        
        if candidate.data:
            is_used = candidate.data.get('access_token_po2_is_used', False)
            stage = 'PO2'
            completed_at = candidate.data.get('po2_completed_at')
            return candidate.data, is_used, stage, completed_at

        # Try PO3 token
        candidate = supabase.table('candidates')\
            .select('*, campaign:campaigns(*)')\
            .eq('access_token_po3', token)\
            .single()\
            .execute()
        
        if candidate.data:
            is_used = candidate.data.get('access_token_po3_is_used', False)
            stage = 'PO3'
            completed_at = candidate.data.get('po3_completed_at')
            return candidate.data, is_used, stage, completed_at

        # Try universal token
        campaign = supabase.table('campaigns')\
            .select('*')\
            .eq('universal_access_token', token)\
            .single()\
            .execute()
        
        if campaign.data:
            is_active = campaign.data.get('is_active', False)
            return campaign.data, not is_active, 'PO1', None

    except Exception as e:
        print(f"Error checking token status: {str(e)}")
        
    return None, False, None, None

def process_test_answers(candidate_id, test_id, form_data):
    """Process test answers and return total score"""
    total_score = 0
    saved_answers = []
    
    for key, value in form_data.items():
        if key.startswith('answer_'):
            if '_min' in key or '_max' in key:
                continue
                
            question_id = int(key.split('_')[1])
            question = supabase.table('questions')\
                .select('*, tests(*)')\
                .eq('id', question_id)\
                .single()\
                .execute()
            
            if not question.data or question.data['test_id'] != test_id:
                continue
            
            answer_data = {
                'candidate_id': candidate_id,
                'question_id': question_id,
                'created_at': datetime.now().isoformat()
            }
            
            answer_type = question.data['answer_type']
            score = calculate_answer_score(answer_type, value, question.data, form_data)
            
            if score is not None:
                total_score += score
                answer_data['score'] = score
            
            # Set the appropriate answer field
            if answer_type == 'TEXT':
                answer_data['text_answer'] = value
            elif answer_type == 'BOOLEAN':
                answer_data['boolean_answer'] = value.lower() == 'true'
            elif answer_type == 'SCALE':
                answer_data['scale_answer'] = int(value)
            elif answer_type == 'SALARY':
                min_value = float(form_data.get(f'answer_{question_id}_min', 0))
                max_value = float(form_data.get(f'answer_{question_id}_max', 0))
                answer_data['salary_answer'] = (min_value + max_value) / 2
            elif answer_type == 'DATE':
                answer_data['date_answer'] = value
            elif answer_type == 'ABCDEF':
                answer_data['abcdef_answer'] = value
            
            result = supabase.table('candidate_answers').insert(answer_data).execute()
            saved_answers.append(result.data[0])
    
    return total_score

def calculate_answer_score(answer_type, value, question, form_data):
    """Calculate score for a single answer"""
    if answer_type == 'TEXT':
        return question['points'] if value == question['correct_answer_text'] else 0
    elif answer_type == 'BOOLEAN':
        return question['points'] if value.lower() == str(question['correct_answer_boolean']).lower() else 0
    elif answer_type == 'SCALE':
        return question['points'] if int(value) == question['correct_answer_scale'] else 0
    elif answer_type == 'SALARY':
        min_value = float(form_data.get(f'answer_{question["id"]}_min', 0))
        max_value = float(form_data.get(f'answer_{question["id"]}_max', 0))
        correct_value = question['correct_answer_salary']
        return question['points'] if min_value <= correct_value <= max_value else 0
    elif answer_type == 'DATE':
        answer_date = datetime.strptime(value, '%Y-%m-%d').date()
        return question['points'] if answer_date == question['correct_answer_date'] else 0
    elif answer_type == 'ABCDEF':
        return question['points'] if value == question['correct_answer_abcdef'] else 0
    return None

@test_public_bp.route('/test/<token>')
def landing(token):
    """Landing page for universal test"""
    test_info = get_universal_test_info(token)
    if not test_info:
        return render_template('tests/error.html',
                             title="Test nie został znaleziony",
                             message="Nie znaleziono testu dla podanego linku.",
                             error_type="test_not_found")
    
    return render_template('tests/landing.html',
                         campaign=test_info['campaign'],
                         test=test_info['test'],
                         token=token)

@test_public_bp.route('/test/<token>/start', methods=['POST'])
def start_test(token):
    """Start universal test"""
    test_info = get_universal_test_info(token)
    if not test_info:
        return render_template('tests/error.html',
                             title="Test nie został znaleziony",
                             message="Nie znaleziono testu dla podanego linku.",
                             error_type="test_not_found")
    
    if not test_info['campaign'].get('is_active', False):
        return render_template('tests/error.html',
                             title="Test niedostępny",
                             message="Ten test nie jest już dostępny.",
                             error_type="test_inactive")
    
    try:
        questions = supabase.table('questions')\
            .select('*')\
            .eq('test_id', test_info['test']['id'])\
            .order('order_number')\
            .execute()
        
        return render_template('tests/survey.html',
                             campaign=test_info['campaign'],
                             test=test_info['test'],
                             questions=questions.data,
                             token=token)
    
    except Exception as e:
        print(f"Error starting test: {str(e)}")
        return render_template('tests/error.html',
                             title="Wystąpił błąd",
                             message="Nie udało się rozpocząć testu.",
                             error_type="unexpected_error")

@test_public_bp.route('/test/<token>/submit', methods=['POST'])
def submit_test(token):
    """Submit the universal test"""
    if not token:
        abort(400, description="Token is required")
        
    test_info = get_universal_test_info(token)
    if not test_info:
        abort(404, description="Invalid token")
    
    try:
        # Create candidate for universal test (PO1)
        candidate_data = {
            'campaign_id': test_info['campaign']['id'],
            'first_name': request.form.get('first_name'),
            'last_name': request.form.get('last_name'),
            'email': request.form.get('email'),
            'phone': request.form.get('phone'),
            'recruitment_status': 'PO1',
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        result = supabase.table('candidates').insert(candidate_data).execute()
        candidate_id = result.data[0]['id']

        # Process answers and calculate score
        total_score = process_test_answers(candidate_id, test_info['test']['id'], request.form)
        
        # Update candidate with score
        update_data = {
            'po1_score': total_score,
            'po1_completed_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        supabase.table('candidates')\
            .update(update_data)\
            .eq('id', candidate_id)\
            .execute()
        
        return redirect(url_for('test_public.complete'))
        
    except Exception as e:
        print(f"Error submitting test: {str(e)}")
        abort(500, description="Error submitting test")

@test_public_bp.route('/test/candidate/<token>/submit', methods=['POST'])
def submit_candidate_test(token):
    """Submit the candidate test"""
    if not token:
        abort(400, description="Token is required")
        
    test_info = get_candidate_test_info(token)
    if not test_info:
        abort(404, description="Invalid token")
    
    try:
        candidate_id = test_info['candidate']['id']
        stage = test_info['stage']

        # Process answers and calculate score
        total_score = process_test_answers(candidate_id, test_info['test']['id'], request.form)
        
        # Update candidate with score
        update_data = {
            f'{stage.lower()}_score': total_score,
            f'{stage.lower()}_completed_at': datetime.now().isoformat(),
            f'access_token_{stage.lower()}_is_used': True,
            'updated_at': datetime.now().isoformat()
        }
        
        supabase.table('candidates')\
            .update(update_data)\
            .eq('id', candidate_id)\
            .execute()
        
        return redirect(url_for('test_public.complete'))
        
    except Exception as e:
        print(f"Error submitting test: {str(e)}")
        abort(500, description="Error submitting test")

@test_public_bp.route('/test/<token>/cancel')
def cancel_test(token):
    """Cancel the test"""
    try:
        # Try universal test first
        test_info = get_universal_test_info(token)
        if test_info:
            return render_template('tests/cancelled.html',
                                 message="Test został anulowany z powodu upływu czasu.")
        
        # Try candidate test
        test_info = get_candidate_test_info(token)
        if test_info:
            # Mark token as used
            stage = test_info['stage']
            update_data = {
                f'access_token_{stage.lower()}_is_used': True,
                'updated_at': datetime.now().isoformat()
            }
            
            supabase.table('candidates')\
                .update(update_data)\
                .eq('id', test_info['candidate']['id'])\
                .execute()
            
            return render_template('tests/cancelled.html',
                                 message="Test został anulowany z powodu upływu czasu.")
        
        return render_template('tests/error.html',
                             title="Test nie został znaleziony",
                             message="Nie znaleziono testu dla podanego linku.",
                             error_type="test_not_found")
            
    except Exception as e:
        print(f"Error cancelling test: {str(e)}")
        return render_template('tests/error.html',
                             title="Wystąpił błąd",
                             message="Nie udało się anulować testu.",
                             error_type="unexpected_error")

@test_public_bp.route('/test/candidate/<token>/cancel')
def cancel_candidate_test(token):
    """Cancel the candidate test"""
    try:
        # Try PO2 token first
        candidate = supabase.table('candidates')\
            .select('*, campaign:campaigns(*)')\
            .eq('access_token_po2', token)\
            .single()\
            .execute()
        
        if candidate.data:
            # Mark PO2 token as used
            update_data = {
                'access_token_po2_is_used': True,
                'updated_at': datetime.now().isoformat()
            }
            
            supabase.table('candidates')\
                .update(update_data)\
                .eq('id', candidate.data['id'])\
                .execute()
            
            return render_template('tests/cancelled.html', 
                                 message="Test został anulowany z powodu upływu czasu.")
        
        # Try PO3 token
        candidate = supabase.table('candidates')\
            .select('*, campaign:campaigns(*)')\
            .eq('access_token_po3', token)\
            .single()\
            .execute()
        
        if candidate.data:
            # Mark PO3 token as used
            update_data = {
                'access_token_po3_is_used': True,
                'updated_at': datetime.now().isoformat()
            }
            
            supabase.table('candidates')\
                .update(update_data)\
                .eq('id', candidate.data['id'])\
                .execute()
            
            return render_template('tests/cancelled.html',
                                 message="Test został anulowany z powodu upływu czasu.")
        
        return render_template('tests/error.html',
                             title="Test nie został znaleziony",
                             message="Nie znaleziono testu dla podanego linku.",
                             error_type="test_not_found")
            
    except Exception as e:
        print(f"Error cancelling test: {str(e)}")
        return render_template('tests/error.html',
                             title="Wystąpił błąd",
                             message="Nie udało się anulować testu.",
                             error_type="unexpected_error")

@test_public_bp.route('/test/complete')
def complete():
    """Show test completion page"""
    return render_template('tests/complete.html')

@test_public_bp.route('/test/candidate/<token>')
def candidate_landing(token):
    """Landing page for candidate test"""
    test_info = get_candidate_test_info(token)
    if not test_info:
        return render_template('tests/error.html',
                             title="Test nie został znaleziony",
                             message="Nie znaleziono testu dla podanego linku.",
                             error_type="test_not_found")
    
    return render_template('tests/landing.html',
                         campaign=test_info['campaign'],
                         test=test_info['test'],
                         token=token,
                         candidate=test_info.get('candidate'))

@test_public_bp.route('/test/candidate/<token>/start', methods=['POST'])
def start_candidate_test(token):
    """Start candidate test"""
    test_info = get_candidate_test_info(token)
    if not test_info:
        return render_template('tests/error.html',
                             title="Test nie został znaleziony",
                             message="Nie znaleziono testu dla podanego linku.",
                             error_type="test_not_found")
    
    try:
        questions = supabase.table('questions')\
            .select('*')\
            .eq('test_id', test_info['test']['id'])\
            .order('order_number')\
            .execute()
        
        template = 'tests/survey.html'
        if test_info['test']['test_type'] in ['IQ', 'EQ']:
            template = 'tests/cognitive.html'
        
        return render_template(template,
                             campaign=test_info['campaign'],
                             test=test_info['test'],
                             questions=questions.data,
                             token=token,
                             candidate=test_info.get('candidate'))
    
    except Exception as e:
        print(f"Error starting candidate test: {str(e)}")
        return render_template('tests/error.html',
                             title="Wystąpił błąd",
                             message="Nie udało się rozpocząć testu.",
                             error_type="unexpected_error") 