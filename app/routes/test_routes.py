from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from database import supabase
import json

test_bp = Blueprint('test', __name__)

@test_bp.route('/tests')
def list():
    try:
        # Get all tests with their basic information
        tests = supabase.table('tests')\
            .select('id, test_type, stage, description, passing_threshold, time_limit_minutes, weight')\
            .order('stage')\
            .order('test_type')\
            .execute()
        
        return render_template('tests/list.html', tests=tests.data)
    
    except Exception as e:
        flash(f'Wystąpił błąd podczas pobierania testów: {str(e)}', 'error')
        return redirect(url_for('main.index'))

@test_bp.route('/tests/add', methods=['POST'])
def add():
    try:
        # Get test data from form
        test_data = {
            'test_type': request.form.get('test_type'),
            'stage': request.form.get('stage'),
            'description': request.form.get('description'),
            'passing_threshold': request.form.get('passing_threshold'),
            'time_limit_minutes': request.form.get('time_limit_minutes'),
            'weight': request.form.get('weight')
        }
        
        # Insert test
        result = supabase.table('tests').insert(test_data).execute()
        test_id = result.data[0]['id']
        
        # Handle questions if any
        questions = json.loads(request.form.get('questions', '[]'))
        for question in questions:
            question['test_id'] = test_id
            supabase.table('questions').insert(question).execute()
        
        return jsonify({'success': True})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@test_bp.route('/tests/<int:test_id>/data')
def get_test_data(test_id):
    try:
        # Get test with questions
        test = supabase.table('tests')\
            .select("""
                *,
                questions (*)
            """)\
            .eq('id', test_id)\
            .single()\
            .execute()
        
        if not test.data:
            return jsonify({'error': 'Test not found'}), 404
            
        return jsonify(test.data)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@test_bp.route('/tests/<int:test_id>/edit', methods=['POST'])
def edit(test_id):
    try:
        # Update test data
        test_data = {
            'test_type': request.form.get('test_type'),
            'stage': request.form.get('stage'),
            'description': request.form.get('description'),
            'passing_threshold': request.form.get('passing_threshold'),
            'time_limit_minutes': request.form.get('time_limit_minutes'),
            'weight': request.form.get('weight')
        }
        
        supabase.table('tests')\
            .update(test_data)\
            .eq('id', test_id)\
            .execute()
        
        # Handle questions
        questions = json.loads(request.form.get('questions', '[]'))
        existing_questions = [q['id'] for q in questions if q.get('id')]
        
        # Delete questions not in the update
        if existing_questions:
            supabase.table('questions')\
                .delete()\
                .eq('test_id', test_id)\
                .not_.in_('id', existing_questions)\
                .execute()
        else:
            supabase.table('questions')\
                .delete()\
                .eq('test_id', test_id)\
                .execute()
        
        # Update or insert questions
        for question in questions:
            question['test_id'] = test_id
            if question.get('id'):
                supabase.table('questions')\
                    .update(question)\
                    .eq('id', question['id'])\
                    .execute()
            else:
                supabase.table('questions')\
                    .insert(question)\
                    .execute()
        
        return jsonify({'success': True})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@test_bp.route('/tests/<int:test_id>/delete', methods=['POST'])
def delete(test_id):
    try:
        # Check if test is used in any campaign
        campaigns = supabase.table('campaigns')\
            .select('id')\
            .or_(f'po1_test_id.eq.{test_id},po2_test_id.eq.{test_id},po3_test_id.eq.{test_id}')\
            .execute()
        
        if campaigns.data:
            return jsonify({
                'success': False, 
                'error': 'Test nie może zostać usunięty, ponieważ jest używany w kampanii'
            })
        
        # Delete test (questions will be deleted automatically due to CASCADE)
        supabase.table('tests')\
            .delete()\
            .eq('id', test_id)\
            .execute()
        
        return jsonify({'success': True})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})