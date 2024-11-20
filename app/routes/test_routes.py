import json
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for, abort
from database import supabase
from datetime import datetime, timedelta
import secrets

test_bp = Blueprint('test', __name__)

def get_test_info(token):
    """Get test information based on token type"""
    # Try universal access token first
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
    
    # Try PO2 token
    candidate = supabase.table('candidates')\
        .select('*, campaign:campaigns(*), test:tests(*)')\
        .eq('access_token_po2', token)\
        .single()\
        .execute()
    
    if candidate.data and not candidate.data.get('access_token_po2_is_used'):
        return {
            'campaign': candidate.data['campaign'],
            'test': candidate.data['test'],
            'stage': 'PO2',
            'candidate': candidate.data
        }
    
    # Try PO3 token
    candidate = supabase.table('candidates')\
        .select('*, campaign:campaigns(*), test:tests(*)')\
        .eq('access_token_po3', token)\
        .single()\
        .execute()
    
    if candidate.data and not candidate.data.get('access_token_po3_is_used'):
        return {
            'campaign': candidate.data['campaign'],
            'test': candidate.data['test'],
            'stage': 'PO3',
            'candidate': candidate.data
        }
    
    return None

@test_bp.route('/test/<token>')
def landing(token):
    """Landing page for test"""
    test_info = get_test_info(token)
    if not test_info:
        abort(404)
    
    return render_template('tests/landing.html',
                         campaign=test_info['campaign'],
                         test=test_info['test'],
                         token=token)

@test_bp.route('/test/<token>/start', methods=['POST'])
def start_test(token):
    """Start the test"""
    test_info = get_test_info(token)
    if not test_info:
        abort(404)
    
    # Get questions for the test
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
                         token=token)

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
    """Submit the test"""
    if not token:
        abort(400, description="Token is required")
        
    test_info = get_test_info(token)
    if not test_info:
        abort(404, description="Invalid token")
    
    try:
        # For PO1, create candidate first
        candidate_id = None
        if test_info['stage'] == 'PO1':
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
        else:
            candidate_id = test_info['candidate']['id']

        if not candidate_id:
            raise ValueError("No candidate ID available")

        # Calculate score based on answers
        total_score = 0
        saved_answers = []  # Keep track of saved answers for verification
        
        for key, value in request.form.items():
            if key.startswith('answer_'):
                # Skip salary min/max fields, they'll be handled with the main salary field
                if '_min' in key or '_max' in key:
                    continue
                    
                question_id = int(key.split('_')[1])
                # Get question details with test info
                question = supabase.table('questions')\
                    .select('*, tests(*)')\
                    .eq('id', question_id)\
                    .single()\
                    .execute()
                
                if not question.data:
                    raise ValueError(f"Question {question_id} not found")
                
                if question.data['test_id'] != test_info['test']['id']:
                    raise ValueError(f"Question {question_id} does not belong to the current test")
                
                # Prepare base answer data
                answer_data = {
                    'candidate_id': candidate_id,
                    'question_id': question_id,
                    'created_at': datetime.now().isoformat()
                }
                
                # Set appropriate answer field and calculate score based on type
                answer_type = question.data['answer_type']
                
                if answer_type == 'TEXT':
                    answer_data['text_answer'] = value
                    if value == question.data['correct_answer_text']:
                        total_score += question.data['points']
                        answer_data['score'] = question.data['points']
                        
                elif answer_type == 'BOOLEAN':
                    bool_value = value.lower() == 'true'
                    answer_data['boolean_answer'] = bool_value
                    if bool_value == question.data['correct_answer_boolean']:
                        total_score += question.data['points']
                        answer_data['score'] = question.data['points']
                        
                elif answer_type == 'SCALE':
                    scale_value = int(value)
                    answer_data['scale_answer'] = scale_value
                    if scale_value == question.data['correct_answer_scale']:
                        total_score += question.data['points']
                        answer_data['score'] = question.data['points']
                        
                elif answer_type == 'SALARY':
                    min_value = float(request.form.get(f'answer_{question_id}_min', 0))
                    max_value = float(request.form.get(f'answer_{question_id}_max', 0))
                    answer_data['numeric_answer'] = (min_value + max_value) / 2
                    correct_value = question.data['correct_answer_numeric']
                    if correct_value and min_value <= correct_value <= max_value:
                        total_score += question.data['points']
                        answer_data['score'] = question.data['points']
                        
                elif answer_type == 'DATE':
                    date_value = datetime.strptime(value, '%Y-%m-%d').date()
                    answer_data['date_answer'] = value
                    if date_value == question.data['correct_answer_date']:
                        total_score += question.data['points']
                        answer_data['score'] = question.data['points']
                        
                elif answer_type == 'ABCD':
                    answer_data['abcd_answer'] = value
                    if value == question.data['correct_answer_abcd']:
                        total_score += question.data['points']
                        answer_data['score'] = question.data['points']
                
                # Save the answer
                result = supabase.table('candidate_answers').insert(answer_data).execute()
                saved_answers.append(result.data[0])
        
        # Update candidate with score
        update_data = {
            f'{test_info["stage"].lower()}_score': total_score,
            f'{test_info["stage"].lower()}_completed_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        if test_info['stage'] != 'PO1':
            update_data[f'access_token_{test_info["stage"].lower()}_is_used'] = True
            
        supabase.table('candidates')\
            .update(update_data)\
            .eq('id', candidate_id)\
            .execute()
        
        return """
            <script>
                localStorage.removeItem('remainingSeconds');
                window.location.href = '{}';
            </script>
        """.format(url_for('test.complete'))
        
    except Exception as e:
        print(f"Error submitting test: {str(e)}")
        # Try to rollback by deleting saved answers and candidate if PO1
        try:
            if saved_answers:
                for answer in saved_answers:
                    supabase.table('candidate_answers')\
                        .delete()\
                        .eq('id', answer['id'])\
                        .execute()
            if test_info['stage'] == 'PO1' and candidate_id:
                supabase.table('candidates')\
                    .delete()\
                    .eq('id', candidate_id)\
                    .execute()
        except:
            pass
        abort(500, description="Error submitting test")

@test_bp.route('/test/<token>/cancel', methods=['GET'])
def cancel_test(token):
    """Cancel the test"""
    test_info = get_test_info(token)
    if not test_info:
        abort(404)
    
    # Mark token as used if it's PO2 or PO3
    if test_info.get('candidate'):
        update_data = {
            f'access_token_{test_info["stage"].lower()}_is_used': True
        }
        supabase.table('candidates')\
            .update(update_data)\
            .eq('id', test_info['candidate']['id'])\
            .execute()
    
    return render_template('tests/cancelled.html')

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
                'answer_a': question.get('answer_a'),
                'answer_b': question.get('answer_b'),
                'answer_c': question.get('answer_c'),
                'answer_d': question.get('answer_d')
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
                'image': question.get('image'),
                'answer_a': question.get('answer_a'),
                'answer_b': question.get('answer_b'),
                'answer_c': question.get('answer_c'),
                'answer_d': question.get('answer_d')
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