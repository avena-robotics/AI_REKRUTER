from flask import Blueprint, render_template, request, redirect, url_for, jsonify
from database import supabase
import uuid
from datetime import datetime
import json

campaign_bp = Blueprint('campaign', __name__, url_prefix='/campaigns')

# Helper function for datetime formatting
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

@campaign_bp.route('/')
def list():
    campaigns = supabase.table('campaigns').select('*').execute()
    for campaign in campaigns.data:
        if campaign.get('created_at'):
            campaign['created_at'] = format_datetime(campaign['created_at'])
        if campaign.get('updated_at'):
            campaign['updated_at'] = format_datetime(campaign['updated_at'])
    return render_template('campaigns/list.html', campaigns=campaigns.data)

@campaign_bp.route('/<int:id>/generate-link', methods=['POST'])
def generate_link(id):
    try:
        # Generate new token
        token = str(uuid.uuid4())
        
        # Update campaign with new token
        supabase.table('campaigns')\
            .update({'universal_access_token': token})\
            .eq('id', id)\
            .execute()
            
        # Return JSON response with success message
        return jsonify({
            'status': 'success',
            'message': 'Link został wygenerowany pomyślnie',
            'token': token
        }), 200
            
    except Exception as e:
        # Return JSON response with error message
        return jsonify({
            'status': 'error',
            'message': 'Wystąpił błąd podczas generowania linku',
            'error': str(e)
        }), 500

@campaign_bp.route('/<int:id>/edit', methods=['POST'])
def edit(id):
    try:
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
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
            'updated_at': current_time
        }
        
        supabase.table('campaigns')\
            .update(campaign_data)\
            .eq('id', id)\
            .execute()

        if 'deleted_questions' in request.form and request.form['deleted_questions']:
            try:
                deleted_questions = json.loads(request.form['deleted_questions'])
                if deleted_questions:
                    print("Deleting questions:", deleted_questions)
                    supabase.table('questions')\
                        .delete()\
                        .in_('id', deleted_questions)\
                        .execute()
            except Exception as e:
                print(f"Error deleting questions: {str(e)}")
                print(f"deleted_questions value: {request.form['deleted_questions']}")

        # Group questions by test index
        test_questions = {}
        for key, value in request.form.items():
            if key.startswith('tests[') and '[questions]' in key:
                test_idx = key.split('[')[1].split(']')[0]
                if test_idx not in test_questions:
                    test_questions[test_idx] = {}
                
                parts = key.split('[questions][')
                q_idx = parts[1].split(']')[0]
                field = parts[1].split('][')[1].split(']')[0]
                
                if q_idx not in test_questions[test_idx]:
                    test_questions[test_idx][q_idx] = {}
                test_questions[test_idx][q_idx][field] = value

        # Process each test
        for test_data in request.form.getlist('tests'):
            if isinstance(test_data, str):
                test_data = json.loads(test_data)
            
            if test_data.get('id'):  # Existing test
                test_id = test_data['id']
                # Update test
                supabase.table('tests')\
                    .update({
                        'test_type': test_data['test_type'],
                        'stage': test_data['stage'],
                        'weight': int(test_data['weight']),
                        'description': test_data.get('description', ''),
                        'passing_threshold': int(test_data.get('passing_threshold', 0)),
                        'time_limit_minutes': int(test_data.get('time_limit_minutes', 0))
                    })\
                    .eq('id', test_id)\
                    .execute()
            else:  # New test
                test_response = supabase.table('tests').insert({
                    'campaign_id': id,
                    'test_type': test_data['test_type'],
                    'stage': test_data['stage'],
                    'weight': int(test_data['weight']),
                    'description': test_data.get('description', ''),
                    'passing_threshold': int(test_data.get('passing_threshold', 0)),
                    'time_limit_minutes': int(test_data.get('time_limit_minutes', 0))
                }).execute()
                test_id = test_response.data[0]['id']

            # Process questions for this test
            test_idx = str(test_data.get('test_index', 0))
            if test_idx in test_questions:
                for q_idx, question_data in test_questions[test_idx].items():
                    question = {
                        'test_id': test_id,
                        'question_text': question_data['question_text'],
                        'answer_type': question_data['answer_type'],
                        'points': int(question_data.get('points', 0)),
                        'order_number': int(question_data.get('order_number', 0)),
                        'is_required': question_data.get('is_required') == 'on'
                    }

                    # Handle base64 image if present
                    if question_data.get('image'):
                        question['image'] = question_data['image']

                    # Add answer fields based on type
                    if question_data['answer_type'] in ['ABCD_TEXT', 'ABCD_IMAGE']:
                        question.update({
                            'answer_a': question_data.get('answer_a'),
                            'answer_b': question_data.get('answer_b'),
                            'answer_c': question_data.get('answer_c'),
                            'answer_d': question_data.get('answer_d'),
                            'correct_answer_abcd': question_data.get('correct_answer_abcd')
                        })
                    elif question_data['answer_type'] == 'BOOLEAN':
                        question['correct_answer_boolean'] = question_data.get('correct_answer_boolean') == 'true'
                    elif question_data['answer_type'] == 'SCALE':
                        question['correct_answer_scale'] = int(question_data.get('correct_answer_scale', 0))
                    elif question_data['answer_type'] == 'SALARY':
                        question['correct_answer_numeric'] = float(question_data.get('correct_answer_numeric', 0))
                    elif question_data['answer_type'] == 'DATE':
                        question['correct_answer_date'] = question_data.get('correct_answer_date')
                    else:  # TEXT
                        question['correct_answer_text'] = question_data.get('correct_answer_text', '')

                    if question_data.get('id'):  # Existing question
                        supabase.table('questions')\
                            .update(question)\
                            .eq('id', question_data['id'])\
                            .execute()
                    else:  # New question
                        supabase.table('questions').insert(question).execute()
        return jsonify({'message': 'Kampania została dodana pomyślnie', 'id': id}), 200
    except Exception as e:
        print(f"Error details: {str(e)}")
        return jsonify({'error': str(e)}), 500

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

@campaign_bp.route('/add', methods=['POST'])
def add():
    try:
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
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
            'created_at': current_time,
            'updated_at': current_time
        }
        
        campaign_response = supabase.table('campaigns').insert(campaign_data).execute()
        campaign_id = campaign_response.data[0]['id']
        
        # Process tests and questions
        if 'tests' in request.form:
            # Group questions by test index
            test_questions = {}
            for key, value in request.form.items():
                if key.startswith('tests[') and '[questions]' in key:
                    # Extract test index and question data
                    test_idx = key.split('[')[1].split(']')[0]
                    if test_idx not in test_questions:
                        test_questions[test_idx] = {}
                    
                    # Extract question index and field
                    parts = key.split('[questions][')
                    q_idx = parts[1].split(']')[0]
                    field = parts[1].split('][')[1].split(']')[0]
                    
                    if q_idx not in test_questions[test_idx]:
                        test_questions[test_idx][q_idx] = {}
                    test_questions[test_idx][q_idx][field] = value

            # Process each test
            for test_data in request.form.getlist('tests'):
                if isinstance(test_data, str):
                    import json
                    test_data = json.loads(test_data)
                
                # Insert test
                test_response = supabase.table('tests').insert({
                    'campaign_id': campaign_id,
                    'test_type': test_data['test_type'],
                    'stage': test_data['stage'],
                    'weight': int(test_data['weight']),
                    'description': test_data.get('description', ''),
                    'passing_threshold': int(test_data.get('passing_threshold', 0)),
                    'time_limit_minutes': int(test_data.get('time_limit_minutes', 0))
                }).execute()
                
                test_id = test_response.data[0]['id']
                
                # Get questions for this test
                test_idx = str(test_data.get('test_index', 0))  # Default to 0 if not specified
                if test_idx in test_questions:
                    for q_idx, question_data in test_questions[test_idx].items():
                        question = {
                            'test_id': test_id,
                            'question_text': question_data['question_text'],
                            'answer_type': question_data['answer_type'],
                            'points': int(question_data.get('points', 0)),
                            'order_number': int(question_data.get('order_number', 0)),
                            'is_required': question_data.get('is_required') == 'on'
                        }
                        
                        # Handle base64 image if present
                        if question_data.get('image'):
                            question['image'] = question_data['image']
                        
                        # Add answer fields based on type
                        if question_data['answer_type'] in ['ABCD_TEXT', 'ABCD_IMAGE']:
                            question.update({
                                'answer_a': question_data.get('answer_a'),
                                'answer_b': question_data.get('answer_b'),
                                'answer_c': question_data.get('answer_c'),
                                'answer_d': question_data.get('answer_d'),
                                'correct_answer_abcd': question_data.get('correct_answer_abcd')
                            })
                        elif question_data['answer_type'] == 'BOOLEAN':
                            question['correct_answer_boolean'] = question_data.get('correct_answer_boolean') == 'true'
                        elif question_data['answer_type'] == 'SCALE':
                            question['correct_answer_scale'] = int(question_data.get('correct_answer_scale', 0))
                        elif question_data['answer_type'] == 'SALARY':
                            question['correct_answer_numeric'] = float(question_data.get('correct_answer_numeric', 0))
                        elif question_data['answer_type'] == 'DATE':
                            question['correct_answer_date'] = question_data.get('correct_answer_date')
                        else:  # TEXT
                            question['correct_answer_text'] = question_data.get('correct_answer_text', '')
                        
                        print("Inserting question:", question)
                        supabase.table('questions').insert(question).execute()
        
        return jsonify({'message': 'Kampania została dodana pomyślnie', 'id': campaign_id}), 200
        
    except Exception as e:
        print(f"Error details: {str(e)}")
        return jsonify({'error': str(e)}), 500

@campaign_bp.route('/<int:id>/data')
def get_campaign_data(id):
    try:
        campaign = supabase.table('campaigns')\
            .select('*, tests(*, questions(*))')\
            .eq('id', id)\
            .single()\
            .execute()
            
        if not campaign.data:
            return jsonify({'error': 'Campaign not found'}), 404
            
        if campaign.data.get('created_at'):
            campaign.data['created_at'] = format_datetime(campaign.data['created_at'])
        if campaign.data.get('updated_at'):
            campaign.data['updated_at'] = format_datetime(campaign.data['updated_at'])
            
        return jsonify(campaign.data), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500