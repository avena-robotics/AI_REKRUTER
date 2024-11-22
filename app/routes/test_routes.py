import json
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for, abort
from database import supabase
from datetime import datetime, timedelta
import secrets

test_bp = Blueprint('test', __name__)

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
            .not_.is_('access_token_po2_is_used', True)\
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
            .not_.is_('access_token_po3_is_used', True)\
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

# Add new function to check token status
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

    except:
        pass
    
    return None, False, None, None

# Universal test routes
@test_bp.route('/test/<token>')
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

@test_bp.route('/test/<token>/start', methods=['POST'])
def start_test(token):
    """Start universal test"""
    test_info = get_universal_test_info(token)
    if not test_info:
        abort(404)
    
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

# Candidate-specific test routes
@test_bp.route('/test/candidate/<token>')
def candidate_landing(token):
    """Landing page for candidate test"""
    try:
        # Check both PO2 and PO3 tokens
        po2_candidates = supabase.table('candidates')\
            .select('access_token_po2_is_used')\
            .eq('access_token_po2', token)\
            .execute()
        
        po3_candidates = supabase.table('candidates')\
            .select('access_token_po3_is_used')\
            .eq('access_token_po3', token)\
            .execute()
        
        # Get first result if exists
        po2_candidate = po2_candidates.data[0] if po2_candidates.data else None
        po3_candidate = po3_candidates.data[0] if po3_candidates.data else None
        
        # Check if token exists in either PO2 or PO3
        if not (po2_candidate or po3_candidate):
            return render_template('tests/error.html',
                                 title="Token nie został znaleziony",
                                 message="Nie znaleziono testu dla podanego linku.",
                                 error_type="token_not_found")
        
        # Check if token is used
        if (po2_candidate and po2_candidate.get('access_token_po2_is_used', False)) or \
           (po3_candidate and po3_candidate.get('access_token_po3_is_used', False)):
            return render_template('tests/used.html')
            
    except Exception as e:
        print(f"Error checking token: {str(e)}")
        return render_template('tests/error.html',
                             title="Wystąpił błąd",
                             message="Nie udało się zweryfikować tokenu testowego.",
                             error_type="unexpected_error")
    
    # If we get here, token exists and is not used
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

@test_bp.route('/test/candidate/<token>/start', methods=['POST'])
def start_candidate_test(token):
    """Start candidate test"""
    test_info = get_candidate_test_info(token)
    if not test_info:
        abort(404)
    
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

@test_bp.route('/test/candidate/<token>/submit', methods=['POST'])
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
        
        return redirect(url_for('test.complete'))
        
    except Exception as e:
        print(f"Error submitting test: {str(e)}")
        abort(500, description="Error submitting test")

@test_bp.route('/test/save-progress', methods=['POST'])
def save_progress():
    """Save partial test progress"""
    data = request.json
    token = data.get('token')
    answers = data.get('answers')
    
    test_info = get_test_info(token)
    if not test_info:
        return jsonify({'success': False, 'error': 'Invalid token'}), 400
    
    # Save answers to temporary storage
    # You might want to create a new table for temporary answers
    return jsonify({'success': True})

@test_bp.route('/test/<token>/submit', methods=['POST'])
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
        
        return redirect(url_for('test.complete'))
        
    except Exception as e:
        print(f"Error submitting test: {str(e)}")
        abort(500, description="Error submitting test")

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
                answer_data['numeric_answer'] = (min_value + max_value) / 2
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
        correct_value = question['correct_answer_numeric']
        return question['points'] if min_value <= correct_value <= max_value else 0
    elif answer_type == 'DATE':
        answer_date = datetime.strptime(value, '%Y-%m-%d').date()
        return question['points'] if answer_date == question['correct_answer_date'] else 0
    elif answer_type == 'ABCDEF':
        return question['points'] if value == question['correct_answer_abcdef'] else 0
    return None

@test_bp.route('/test/<token>/cancel', methods=['GET'])
def cancel_test(token):
    """Cancel the test"""
    try:
        # Try universal test first
        test_info = get_universal_test_info(token)
        if test_info:
            return render_template('tests/cancelled.html')
        
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
            
            return render_template('tests/cancelled.html')
        
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

@test_bp.route('/tests')
def list():
    try:
        tests = supabase.from_('tests')\
            .select('*, created_at')\
            .order('created_at', desc=True)\
            .execute()
        
        for test in tests.data:
            questions = supabase.from_('questions')\
                .select('*')\
                .eq('test_id', test['id'])\
                .execute()
            test['questions'] = questions.data
            test['question_count'] = len(questions.data)
            test['total_points'] = sum(q.get('points', 0) for q in questions.data)
        
        return render_template('tests/list.html', 
                             tests=tests.data or [])
    
    except Exception as e:
        print(f"Error in test list: {str(e)}")  # Debug log
        return jsonify({
            'success': False,
            'error': f'Wystąpił błąd podczas pobierania testów: {str(e)}'
        }), 500

@test_bp.route('/tests/add', methods=['POST'])
def add():
    try:
        passing_threshold = request.form.get('passing_threshold')
        time_limit = request.form.get('time_limit_minutes')
        
        passing_threshold = int(passing_threshold) if passing_threshold and passing_threshold.strip() else 0
        
        time_limit = int(time_limit) if time_limit and time_limit.strip() else None
        
        test_data = {
            'test_type': request.form.get('test_type'),
            'stage': request.form.get('stage'),
            'description': request.form.get('description'),
            'passing_threshold': passing_threshold,
            'time_limit_minutes': time_limit
        }
        
        result = supabase.from_('tests').insert(test_data).execute()
        test_id = result.data[0]['id']
        
        questions = json.loads(request.form.get('questions', '[]'))
        for question in questions:
            clean_question = {
                'test_id': test_id,
                'question_text': question['question_text'],
                'answer_type': question['answer_type'],
                'points': int(question.get('points', 0)),
                'order_number': question['order_number'],
                'is_required': question.get('is_required', True),
                'image': question.get('image'),
            }
            
            if question['answer_type'] == 'SALARY':
                numeric_value = question.get('correct_answer_numeric')
                clean_question['correct_answer_numeric'] = float(numeric_value) if numeric_value is not None else None
            else:
                answer_field = f'correct_answer_{question["answer_type"].lower()}'
                if answer_field in question and question[answer_field] is not None:
                    clean_question[answer_field] = question[answer_field]
            
            supabase.from_('questions').insert(clean_question).execute()
        
        return jsonify({
            'success': True,
            'message': 'Test został dodany pomyślnie'
        })
    
    except ValueError as e:
        print(f"Error adding test (value error): {str(e)}")
        return jsonify({
            'success': False, 
            'error': 'Nieprawidłowe wartości numeryczne'
        })
    except Exception as e:
        print(f"Error adding test: {str(e)}")
        return jsonify({
            'success': False, 
            'error': str(e)
        })

@test_bp.route('/tests/<int:test_id>/data')
def get_test_data(test_id):
    try:
        test = supabase.from_('tests')\
            .select('*')\
            .eq('id', test_id)\
            .single()\
            .execute()
        
        if not test.data:
            return jsonify({'error': 'Test not found'}), 404
        
        questions = supabase.from_('questions')\
            .select('*')\
            .eq('test_id', test_id)\
            .execute()
        
        test.data['questions'] = sorted(
            questions.data,
            key=lambda x: x.get('order_number', 0)
        )
            
        return jsonify(test.data)
    
    except Exception as e:
        print(f"Debug - Error in get_test_data: {str(e)}")
        return jsonify({'error': str(e)}), 500

@test_bp.route('/tests/<int:test_id>/edit', methods=['POST'])
def edit(test_id):
    try:
        test_data = {
            'test_type': request.form.get('test_type'),
            'stage': request.form.get('stage'),
            'description': request.form.get('description'),
            'passing_threshold': int(request.form.get('passing_threshold', 0)),
            'time_limit_minutes': int(request.form.get('time_limit_minutes', 0)) if request.form.get('time_limit_minutes') else None
        }
        
        supabase.from_('tests')\
            .update(test_data)\
            .eq('id', test_id)\
            .execute()
        
        questions = json.loads(request.form.get('questions', '[]'))
        print("Received questions data:", questions)  # Debug log
        
        existing_questions = [q['id'] for q in questions if q.get('id')]
        
        if existing_questions:
            supabase.from_('questions')\
                .delete()\
                .eq('test_id', test_id)\
                .not_.in_('id', existing_questions)\
                .execute()
        else:
            supabase.from_('questions')\
                .delete()\
                .eq('test_id', test_id)\
                .execute()
        
        # Update or insert questions
        for question in questions:
            clean_question = {
                'test_id': test_id,
                'question_text': question['question_text'],
                'answer_type': question['answer_type'],
                'points': int(question.get('points', 0)),
                'order_number': question.get('order_number', 1),
                'is_required': question.get('is_required', True),
                'image': question.get('image')
            }
            
            if question['answer_type'] == 'SALARY':
                numeric_value = question.get('correct_answer_numeric')
                clean_question['correct_answer_numeric'] = float(numeric_value) if numeric_value is not None else None
            else:
                answer_field = f'correct_answer_{question["answer_type"].lower()}'
                if answer_field in question and question[answer_field] is not None:
                    clean_question[answer_field] = question[answer_field]
            
            if question.get('id'):
                supabase.from_('questions')\
                    .update(clean_question)\
                    .eq('id', question['id'])\
                    .execute()
            else:
                supabase.from_('questions')\
                    .insert(clean_question)\
                    .execute()
        
        return jsonify({
            'success': True,
            'message': 'Test został zaktualizowany pomyślnie'
        })
    
    except Exception as e:
        print(f"Error editing test: {str(e)}")
        return jsonify({
            'success': False, 
            'error': str(e)
        })

@test_bp.route('/tests/<int:test_id>/delete', methods=['POST'])
def delete(test_id):
    try:
        campaigns = supabase.from_('campaigns')\
            .select('id')\
            .or_(f'po1_test_id.eq.{test_id},po2_test_id.eq.{test_id},po3_test_id.eq.{test_id}')\
            .execute()
        
        if campaigns.data:
            return jsonify({
                'success': False, 
                'error': 'Test nie może zostać usunięty, ponieważ jest używany w kampanii'
            })
        
        supabase.from_('tests')\
            .delete()\
            .eq('id', test_id)\
            .execute()
        
        return jsonify({'success': True})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@test_bp.route('/test/complete')
def complete():
    """Show test completion page"""
    return render_template('tests/complete.html')