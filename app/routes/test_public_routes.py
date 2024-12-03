from flask import Blueprint, render_template, request, jsonify, redirect, url_for, abort
from database import supabase
from datetime import datetime, timedelta, timezone

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
    """Check if token is used or expired and get test info"""
    try:
        # Use UTC for consistent timezone handling
        current_time = datetime.now(timezone.utc)
        
        # Try PO2 token first
        try:
            candidate = supabase.table('candidates')\
                .select('*, campaign:campaigns(*)')\
                .eq('access_token_po2', token)\
                .single()\
                .execute()
            
            if candidate.data:
                is_used = candidate.data.get('access_token_po2_is_used', False)
                expires_at = candidate.data.get('access_token_po2_expires_at')
                
                # Convert expires_at to UTC datetime if it exists
                is_expired = False
                if expires_at:
                    try:
                        # Handle different datetime string formats
                        if 'Z' in expires_at:
                            expires_dt = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
                        elif '+' in expires_at:
                            expires_dt = datetime.fromisoformat(expires_at)
                        else:
                            expires_dt = datetime.fromisoformat(expires_at).replace(tzinfo=timezone.utc)
                        
                        is_expired = expires_dt < current_time
                    except ValueError as e:
                        print(f"Error parsing date: {str(e)}")
                        is_expired = False
                
                stage = 'PO2'
                completed_at = candidate.data.get('po2_completed_at')
                return candidate.data, is_used or is_expired, stage, completed_at
        except Exception:
            
            pass  # Silently handle when PO2 token not found
        
        # Try PO3 token
        try:
            candidate = supabase.table('candidates')\
                .select('*, campaign:campaigns(*)')\
                .eq('access_token_po3', token)\
                .single()\
                .execute()
            
            if candidate.data:
                is_used = candidate.data.get('access_token_po3_is_used', False)
                expires_at = candidate.data.get('access_token_po3_expires_at')
                
                # Convert expires_at to UTC datetime if it exists
                is_expired = False
                if expires_at:
                    try:
                        # Handle different datetime string formats
                        if 'Z' in expires_at:
                            expires_dt = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
                        elif '+' in expires_at:
                            expires_dt = datetime.fromisoformat(expires_at)
                        else:
                            expires_dt = datetime.fromisoformat(expires_at).replace(tzinfo=timezone.utc)
                        
                        is_expired = expires_dt < current_time
                    except ValueError as e:
                        print(f"Error parsing date: {str(e)}")
                        is_expired = False
                
                stage = 'PO3'
                completed_at = candidate.data.get('po3_completed_at')
                return candidate.data, is_used or is_expired, stage, completed_at
        except Exception:
            pass  # Silently handle when PO3 token not found

        # Try universal token
        try:
            campaign = supabase.table('campaigns')\
                .select('*')\
                .eq('universal_access_token', token)\
                .single()\
                .execute()
            
            if campaign.data:
                is_active = campaign.data.get('is_active', False)
                return campaign.data, not is_active, 'PO1', None
        except Exception:
            pass  # Silently handle when universal token not found

    except Exception as e:
        print(f"Error checking token status: {str(e)}")
        
    return None, False, None, None

def process_test_answers(candidate_id, test_id, form_data):
    """Process test answers"""
    def get_stage_for_candidate(candidate_id):
        result = supabase.table('candidates').select('recruitment_status').eq('id', candidate_id).single().execute()
        return result.data['recruitment_status'] if result.data else None

    stage = get_stage_for_candidate(candidate_id)
    if not stage:
        raise Exception("Could not determine stage for candidate")

    answers_to_insert = []
    
    # Get all questions for this test in one query
    questions = supabase.table('questions')\
        .select('*')\
        .eq('test_id', test_id)\
        .execute()
    
    # Create a lookup dictionary for questions
    questions_lookup = {str(q['id']): q for q in questions.data}
    
    # Process regular answers
    regular_answers = {}
    ah_points_answers = {}
    
    # First pass - organize the data
    for key, value in form_data.items():
        if not key.startswith('answer_'):
            continue
            
        if '_min' in key or '_max' in key:
            continue
            
        # Handle AH_POINTS type answers
        if any(suffix in key for suffix in ['_a', '_b', '_c', '_d', '_e', '_f', '_g', '_h']):
            question_id = key.split('_')[1]
            letter = key.split('_')[2]
            
            if question_id not in ah_points_answers:
                ah_points_answers[question_id] = {}
            
            if value:  # Only store non-empty values
                ah_points_answers[question_id][letter] = int(value or 0)
        else:
            question_id = key.split('_')[1]
            regular_answers[question_id] = value

    # Process AH_POINTS answers
    for question_id, points in ah_points_answers.items():
        if not points:  # Skip if no points recorded
            continue
            
        question = questions_lookup.get(question_id)
        if not question or question['test_id'] != test_id:
            continue
            
        answer_data = {
            'candidate_id': candidate_id,
            'question_id': int(question_id),
            'stage': stage,
            'points_per_option': points,
            'created_at': datetime.now().isoformat()
        }
        answers_to_insert.append(answer_data)

    # Process regular answers
    for question_id, value in regular_answers.items():
        question = questions_lookup.get(question_id)
        if not question or question['test_id'] != test_id:
            continue
            
        answer_data = {
            'candidate_id': candidate_id,
            'question_id': int(question_id),
            'stage': stage,
            'created_at': datetime.now().isoformat()
        }
        
        answer_type = question['answer_type']
        
        # Set the appropriate answer field based on type
        if answer_type == 'TEXT':
            answer_data['text_answer'] = value
        elif answer_type == 'BOOLEAN':
            answer_data['boolean_answer'] = value.lower() == 'true'
        elif answer_type == 'SCALE':
            answer_data['scale_answer'] = int(value)
        elif answer_type == 'SALARY':
            answer_data['salary_answer'] = float(value) if value else 0
        elif answer_type == 'DATE':
            answer_data['date_answer'] = value
        elif answer_type == 'ABCDEF':
            answer_data['abcdef_answer'] = value
            
        answers_to_insert.append(answer_data)

    # Batch insert all answers
    if answers_to_insert:
        supabase.table('candidate_answers').insert(answers_to_insert).execute()

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
        # Get start time from form data (will be sent from localStorage)
        start_time_str = request.form.get('test_start_time')
        if start_time_str:
            try:
                start_time = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
            except ValueError:
                start_time = datetime.now(timezone.utc)
        else:
            start_time = datetime.now(timezone.utc)
            
        current_time = datetime.now(timezone.utc)
        
        # Create candidate for universal test (PO1)
        candidate_data = {
            'campaign_id': test_info['campaign']['id'],
            'first_name': request.form.get('first_name'),
            'last_name': request.form.get('last_name'),
            'email': request.form.get('email'),
            'phone': request.form.get('phone'),
            'recruitment_status': 'PO1',
            'po1_started_at': start_time.isoformat(),
            'po1_completed_at': current_time.isoformat(),
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
    # Check if token is used or expired
    candidate, is_invalid, stage, completed_at = check_token_status(token)
    
    # Handle invalid token
    if not candidate:
        return render_template('tests/error.html',
                             title="Nieprawidłowy token",
                             message="Podany link jest nieprawidłowy.",
                             error_type="token_not_found")
    
    # Handle PO2/PO3 specific checks
    if stage in ['PO2', 'PO3']:
        # Check if token is expired
        expires_at = candidate.get(f'access_token_{stage.lower()}_expires_at')
        if expires_at:
            try:
                # Convert expires_at to UTC datetime
                if 'Z' in expires_at:
                    expires_dt = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
                elif '+' in expires_at:
                    expires_dt = datetime.fromisoformat(expires_at)
                else:
                    expires_dt = datetime.fromisoformat(expires_at).replace(tzinfo=timezone.utc)
                
                current_time = datetime.now(timezone.utc)
                if expires_dt < current_time:
                    return render_template('tests/error.html',
                                        title="Link wygasł",
                                        message="Link do testu wygasł i nie jest już aktywny.",
                                        error_type="test_expired")
            except ValueError as e:
                print(f"Error parsing date: {str(e)}")
        
        # Check if token was already used
        is_used = candidate.get(f'access_token_{stage.lower()}_is_used', False)
        if is_used:
            return render_template('tests/used.html')
        
        # Check if test was already completed
        if completed_at:
            return render_template('tests/used.html')
    
    # Get test info
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
    # Check if token is used or expired
    candidate, is_invalid, stage, completed_at = check_token_status(token)
    
    # Handle invalid token
    if not candidate:
        return render_template('tests/error.html',
                             title="Nieprawidłowy token",
                             message="Podany link jest nieprawidłowy.",
                             error_type="token_not_found")
    
    # Handle PO2/PO3 specific checks
    if stage in ['PO2', 'PO3']:
        # Check if token is expired
        expires_at = candidate.get(f'access_token_{stage.lower()}_expires_at')
        if expires_at:
            try:
                # Convert expires_at to UTC datetime
                if 'Z' in expires_at:
                    expires_dt = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
                elif '+' in expires_at:
                    expires_dt = datetime.fromisoformat(expires_at)
                else:
                    expires_dt = datetime.fromisoformat(expires_at).replace(tzinfo=timezone.utc)
                
                current_time = datetime.now(timezone.utc)
                if expires_dt < current_time:
                    return render_template('tests/error.html',
                                        title="Link wygasł",
                                        message="Link do testu wygasł i nie jest już aktywny.",
                                        error_type="test_expired")
            except ValueError as e:
                print(f"Error parsing date: {str(e)}")
        
        # Check if token was already used
        is_used = candidate.get(f'access_token_{stage.lower()}_is_used', False)
        if is_used:
            return render_template('tests/used.html')
        
        # Check if test was already completed
        if completed_at:
            return render_template('tests/used.html')
        
        try:
            # Mark token as used and record start time
            update_data = {
                f'access_token_{stage.lower()}_is_used': True,
                f'{stage.lower()}_started_at': datetime.now(timezone.utc).isoformat(),
                'updated_at': datetime.now(timezone.utc).isoformat()
            }
            
            supabase.table('candidates')\
                .update(update_data)\
                .eq('id', candidate['id'])\
                .execute()
        except Exception as e:
            print(f"Error marking token as used: {str(e)}")
            return render_template('tests/error.html',
                                title="Wystąpił błąd",
                                message="Nie udało się rozpocząć testu.",
                                error_type="unexpected_error")
    
    # Get test info
    test_info = get_candidate_test_info(token)
    if not test_info:
        return render_template('tests/error.html',
                             title="Test nie został znaleziony",
                             message="Nie znaleziono testu dla podanego linku.",
                             error_type="test_not_found")
    
    try:
        # Get questions
        questions = supabase.table('questions')\
            .select('*')\
            .eq('test_id', test_info['test']['id'])\
            .order('order_number')\
            .execute()
        
        if not questions.data:
            return render_template('tests/error.html',
                                 title="Brak pytań",
                                 message="Test nie zawiera żadnych pytań.",
                                 error_type="no_questions")
        
        # Choose template based on test type
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