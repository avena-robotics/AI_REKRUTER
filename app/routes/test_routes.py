import json
from flask import Blueprint, render_template, request, jsonify, session
from database import supabase
from datetime import datetime
from routes.auth_routes import login_required
from services.group_service import GroupService

test_bp = Blueprint('test', __name__, url_prefix='/tests')

@test_bp.route('/')
@login_required
def list():
    try:
        # Get user's test IDs and available groups
        user_id = session.get('user_id')
        allowed_test_ids = GroupService.get_user_test_ids(user_id)
        available_groups = GroupService.get_user_available_groups(user_id)
        
        print(f"User ID: {user_id}")  # Debug log
        print(f"Available groups: {available_groups}")  # Debug log
        
        # Get tests filtered by user's access
        tests = supabase.from_('tests')\
            .select('*, created_at')\
            .in_('id', allowed_test_ids)\
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
            # Get groups for test that user has access to
            test['groups'] = GroupService.get_test_groups(test['id'], user_id)
            print(f"Test {test['id']} groups: {test['groups']}")  # Debug log
        
        return render_template('tests/list.html', 
                             tests=tests.data or [],
                             available_groups=available_groups)
    except Exception as e:
        print(f"Error in test list: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Wystąpił błąd podczas pobierania testów: {str(e)}'
        }), 500

@test_bp.route('/add', methods=['POST'])
def add():
    try:
        # Sprawdź czy wybrano grupy
        groups = request.form.getlist('groups[]')
        if not groups:
            return jsonify({
                'success': False,
                'error': 'Wybierz przynajmniej jedną grupę'
            }), 400
        
        # Sprawdź limit czasu
        time_limit = request.form.get('time_limit_minutes')
        if not time_limit or not time_limit.strip() or int(time_limit) < 1:
            return jsonify({
                'success': False,
                'error': 'Podaj prawidłowy limit czasu (minimum 1 minuta)'
            }), 400
            
        passing_threshold = request.form.get('passing_threshold')
        
        passing_threshold = int(passing_threshold) if passing_threshold and passing_threshold.strip() else 0
        time_limit = int(time_limit)
        
        test_data = {
            'test_type': request.form.get('test_type'),
            'stage': request.form.get('stage'),
            'description': request.form.get('description'),
            'passing_threshold': passing_threshold,
            'time_limit_minutes': time_limit
        }
        
        result = supabase.from_('tests').insert(test_data).execute()
        test_id = result.data[0]['id']
        
        # Handle group assignments
        if groups:
            group_links = [{'test_id': test_id, 'group_id': int(group_id)} 
                         for group_id in groups]
            supabase.from_('link_groups_tests').insert(group_links).execute()
        
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
        
        return jsonify({'success': True})
    
    except ValueError as e:
        print(f"Error adding test (value error): {str(e)}")
        return jsonify({'success': False}), 400
    except Exception as e:
        print(f"Error adding test: {str(e)}")
        return jsonify({'success': False}), 500

@test_bp.route('/<int:test_id>/data')
def get_test_data(test_id):
    try:
        test = supabase.from_('tests')\
            .select('*')\
            .eq('id', test_id)\
            .single()\
            .execute()
        
        if not test.data:
            return jsonify({'error': 'Test not found'}), 404
        
        # Get questions
        questions = supabase.from_('questions')\
            .select('*')\
            .eq('test_id', test_id)\
            .execute()
        
        # Get groups for this test
        user_id = session.get('user_id')
        test_groups = GroupService.get_test_groups(test_id, user_id)
        
        test_data = test.data
        test_data['questions'] = sorted(
            questions.data,
            key=lambda x: x.get('order_number', 0)
        )
        test_data['groups'] = test_groups
            
        return jsonify(test_data)
    
    except Exception as e:
        print(f"Debug - Error in get_test_data: {str(e)}")
        return jsonify({'error': str(e)}), 500

@test_bp.route('/<int:test_id>/edit', methods=['POST'])
def edit(test_id):
    try:
        # Sprawdź czy wybrano grupy
        groups = request.form.getlist('groups[]')
        if not groups:
            return jsonify({
                'success': False,
                'error': 'Wybierz przynajmniej jedną grupę'
            }), 400
        
        # Sprawdź limit czasu
        time_limit = request.form.get('time_limit_minutes')
        if not time_limit or not time_limit.strip() or int(time_limit) < 1:
            return jsonify({
                'success': False,
                'error': 'Podaj prawidłowy limit czasu (minimum 1 minuta)'
            }), 400
            
        test_data = {
            'test_type': request.form.get('test_type'),
            'stage': request.form.get('stage'),
            'description': request.form.get('description'),
            'passing_threshold': int(request.form.get('passing_threshold', 0)),
            'time_limit_minutes': int(time_limit)
        }
        
        supabase.from_('tests')\
            .update(test_data)\
            .eq('id', test_id)\
            .execute()
        
        # Update group assignments
        # Delete existing group links
        supabase.from_('link_groups_tests')\
            .delete()\
            .eq('test_id', test_id)\
            .execute()
        
        # Insert new group links
        if groups:
            group_links = [{'test_id': test_id, 'group_id': int(group_id)} 
                         for group_id in groups]
            supabase.from_('link_groups_tests').insert(group_links).execute()
        
        # Update questions
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
        
        return jsonify({'success': True})
    
    except Exception as e:
        print(f"Error editing test: {str(e)}")
        return jsonify({'success': False}), 500

@test_bp.route('/<int:test_id>/delete', methods=['POST'])
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