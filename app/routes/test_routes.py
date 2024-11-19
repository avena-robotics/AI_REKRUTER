from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from database import supabase
from datetime import datetime, timedelta
import json


test_bp = Blueprint('test', __name__, url_prefix='/test')

@test_bp.route('/<token>', methods=['GET'])
def take_test(token):
    # Check if token is valid
    campaign = supabase.table('campaigns')\
        .select('*')\
        .eq('universal_access_token', token)\
        .single()\
        .execute()
    
    if not campaign.data:
        abort(404, description="Invalid or expired token")
    
    # Get test for the campaign
    test = supabase.table('tests')\
        .select('*')\
        .eq('campaign_id', campaign.data['id'])\
        .eq('stage', 'PO1')\
        .single()\
        .execute()
    
    if not test.data:
        abort(404, description="No test found for this campaign")
    
    # Get questions for the test
    questions = supabase.table('questions')\
        .select('*')\
        .eq('test_id', test.data['id'])\
        .order('order_number')\
        .execute()
    
    return render_template('tests/survey.html',
                         test=test.data,
                         questions=questions.data,
                         token=token)

@test_bp.route('/<token>/submit', methods=['POST'])
def submit(token):
    # Validate token and get campaign
    campaign = supabase.table('campaigns')\
        .select('*')\
        .eq('universal_access_token', token)\
        .single()\
        .execute()
    
    if not campaign.data:
        abort(404, description="Invalid or expired token")
    
    # Create candidate record
    candidate_data = {
        'campaign_id': campaign.data['id'],
        'first_name': request.form.get('first_name'),
        'last_name': request.form.get('last_name'),
        'email': request.form.get('email'),
        'phone': request.form.get('phone'),
        'recruitment_status': 'PO1',
        'po1_completed_at': datetime.now().isoformat()
    }
    
    candidate = supabase.table('candidates').insert(candidate_data).execute()
    
    # Process answers
    total_score = 0
    for key, value in request.form.items():
        if key.startswith('answer_'):
            question_id = int(key.split('_')[1])
            if '_min' in key or '_max' in key:
                continue  # Skip individual min/max fields, they'll be handled with the main salary field
                
            question = supabase.table('questions')\
                .select('*')\
                .eq('id', question_id)\
                .single()\
                .execute()
            
            answer_data = {
                'candidate_id': candidate.data[0]['id'],
                'question_id': question_id
            }
            
            # Process different answer types
            if question.data['answer_type'] == 'TEXT':
                answer_data['text_answer'] = value
            elif question.data['answer_type'] == 'BOOLEAN':
                answer_data['boolean_answer'] = value.lower() == 'true'
            elif question.data['answer_type'] == 'SCALE':
                answer_data['scale_answer'] = int(value)
            elif question.data['answer_type'] == 'SALARY':
                min_val = float(request.form.get(f'answer_{question_id}_min', 0))
                max_val = float(request.form.get(f'answer_{question_id}_max', 0))
                # Store the average as numeric_answer
                answer_data['numeric_answer'] = (min_val + max_val) / 2
                # Store the full range as text_answer for reference
                answer_data['text_answer'] = json.dumps({'min': min_val, 'max': max_val})
            elif question.data['answer_type'] == 'DATE':
                answer_data['date_answer'] = value
            elif question.data['answer_type'] in ['ABCD_TEXT', 'ABCD_IMAGE']:
                answer_data['abcd_answer'] = value
            
            # Calculate score
            score = calculate_score(question.data, answer_data)
            answer_data['score'] = score
            total_score += score
            
            # Save answer
            supabase.table('candidate_answers').insert(answer_data).execute()
    
    # Update candidate's score
    supabase.table('candidates')\
        .update({'po1_score': total_score, 'total_score': total_score})\
        .eq('id', candidate.data[0]['id'])\
        .execute()
    
    return render_template('tests/complete.html')

def calculate_score(question, answer):
    """Calculate score based on question type and correct answer"""
    if question['answer_type'] == 'TEXT':
        # For text answers, score will be calculated by AI later
        return 0
    elif question['answer_type'] == 'BOOLEAN':
        return question['points'] if answer['boolean_answer'] == question['correct_answer_boolean'] else 0
    elif question['answer_type'] == 'SCALE':
        return question['points'] if answer['scale_answer'] == question['correct_answer_scale'] else 0
    elif question['answer_type'] == 'SALARY':
        # For salary questions, check if the answer is within an acceptable range
        correct_value = float(question['correct_answer_numeric'])
        answer_value = float(answer['numeric_answer'])
        # Allow for a 10% deviation from the correct value
        tolerance = correct_value * 0.1
        return question['points'] if abs(answer_value - correct_value) <= tolerance else 0
    elif question['answer_type'] in ['ABCD_TEXT', 'ABCD_IMAGE']:
        return question['points'] if answer['abcd_answer'] == question['correct_answer_abcd'] else 0
    return 0