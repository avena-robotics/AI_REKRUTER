from flask import Blueprint, render_template, request, jsonify
from database import supabase
from datetime import datetime, timedelta
from routes.auth_routes import login_required

candidate_bp = Blueprint('candidate', __name__, url_prefix='/candidates')

@candidate_bp.route('/')
@login_required
def list():
    campaign_code = request.args.get('campaign_code')
    status = request.args.get('status')
    sort_by = request.args.get('sort_by', 'created_at')  # Default sort by created_at
    sort_order = request.args.get('sort_order', 'desc')  # Default order desc
    
    # Get all campaigns for the dropdown
    campaigns = supabase.table('campaigns').select('code, title').execute()
    
    # Get candidates with filters and join with campaigns
    query = supabase.table('candidates')\
        .select('*, campaigns!inner(*)')
    
    if campaign_code:
        query = query.eq('campaigns.code', campaign_code)
    if status:
        query = query.eq('recruitment_status', status)
        
    # Apply sorting
    query = query.order(sort_by, desc=(sort_order == 'desc'))
    
    candidates = query.execute()
    
    return render_template('candidates/list.html', 
                         candidates=candidates.data,
                         campaigns=campaigns.data)

@candidate_bp.route('/<int:id>')
def view(id):
    # Get candidate with campaign data - Modified query to use proper join
    candidate = supabase.table('candidates')\
        .select('*, campaign:campaigns(*)')\
        .eq('id', id)\
        .single()\
        .execute()
    
    # Get all tests for this candidate
    tests_data = {}
    for stage in ['PO1', 'PO2', 'PO3']:
        # Get test ID from campaign based on stage - Updated to use correct path
        test_id = candidate.data['campaign'].get(f'{stage.lower()}_test_id')
        if test_id:
            # Get test details
            test = supabase.table('tests')\
                .select('*')\
                .eq('id', test_id)\
                .single()\
                .execute()
            
            if test.data:
                # Get questions for this test
                questions = supabase.table('questions')\
                    .select('*')\
                    .eq('test_id', test_id)\
                    .execute()
                
                # Get candidate's answers for this test
                answers = supabase.table('candidate_answers')\
                    .select('*')\
                    .eq('candidate_id', id)\
                    .execute()
                
                # Match answers with questions
                questions_with_answers = []
                for question in questions.data:
                    question_data = dict(question)
                    # Find answer for this question
                    answer = next((a for a in answers.data if a['question_id'] == question['id']), None)
                    if answer:
                        question_data['answer'] = answer
                    questions_with_answers.append(question_data)
                
                tests_data[stage] = {
                    'test': test.data,
                    'questions': questions_with_answers,
                    'question_count': len(questions_with_answers),
                    'total_points': sum(q.get('points', 0) for q in questions_with_answers),
                    'score': candidate.data.get(f'{stage.lower()}_score'),
                    'completed_at': candidate.data.get(f'{stage.lower()}_completed_at')
                }
    
    return render_template('candidates/view.html', 
                         candidate=candidate.data, 
                         tests=tests_data)

@candidate_bp.route('/<int:id>/reject', methods=['POST'])
def reject(id):
    try:
        # Update candidate status to REJECTED
        result = supabase.table('candidates')\
            .update({'recruitment_status': 'REJECTED'})\
            .eq('id', id)\
            .execute()
        
        return jsonify({'success': True}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@candidate_bp.route('/<int:id>/accept', methods=['POST'])
def accept(id):
    try:
        # Update candidate status to ACCEPTED
        result = supabase.table('candidates')\
            .update({'recruitment_status': 'ACCEPTED'})\
            .eq('id', id)\
            .execute()
        
        return jsonify({'success': True}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@candidate_bp.route('/<int:id>/delete', methods=['POST'])
def delete(id):
    try:
        # First delete all candidate answers
        supabase.table('candidate_answers')\
            .delete()\
            .eq('candidate_id', id)\
            .execute()
        
        # Then delete the candidate
        result = supabase.table('candidates')\
            .delete()\
            .eq('id', id)\
            .execute()
        
        return jsonify({'success': True}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@candidate_bp.route('/<int:id>/extend-token/<stage>', methods=['POST'])
def extend_token(id, stage):
    try:
        if stage not in ['PO2', 'PO3']:
            return jsonify({
                'success': False,
                'error': 'Nieprawidłowy etap rekrutacji'
            }), 400

        # Get candidate data
        candidate = supabase.table('candidates')\
            .select('*')\
            .eq('id', id)\
            .single()\
            .execute()

        if not candidate.data:
            return jsonify({
                'success': False,
                'error': 'Nie znaleziono kandydata'
            }), 404

        # Check if token exists and is not used
        token_field = f'access_token_{stage.lower()}'
        is_used_field = f'{token_field}_is_used'
        expires_field = f'{token_field}_expires_at'

        if not candidate.data.get(token_field):
            return jsonify({
                'success': False,
                'error': 'Brak tokenu do przedłużenia'
            }), 400

        if candidate.data.get(is_used_field):
            return jsonify({
                'success': False,
                'error': 'Token został już wykorzystany'
            }), 400

        # Calculate new expiration date (current expiration + 7 days)
        current_expires = candidate.data.get(expires_field)
        if current_expires:
            current_expires = datetime.fromisoformat(current_expires.replace('Z', ''))
        else:
            current_expires = datetime.now()

        new_expires = current_expires + timedelta(days=7)

        # Update expiration date
        result = supabase.table('candidates')\
            .update({expires_field: new_expires.isoformat()})\
            .eq('id', id)\
            .execute()

        return jsonify({
            'success': True,
            'message': 'Token został przedłużony o tydzień'
        })

    except Exception as e:
        print(f"Error extending token: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Wystąpił błąd podczas przedłużania tokenu'
        }), 500 