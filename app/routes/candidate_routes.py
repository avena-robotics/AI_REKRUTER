from flask import Blueprint, render_template, request, jsonify
from database import supabase

candidate_bp = Blueprint('candidate', __name__, url_prefix='/candidates')

@candidate_bp.route('/')
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
    # Get candidate with campaign data
    candidate = supabase.table('candidates')\
        .select('*, campaigns(*)')\
        .eq('id', id)\
        .single()\
        .execute()
    
    # Get answers with questions and test data
    answers = supabase.table('candidate_answers')\
        .select('*, questions(*, tests(*))')\
        .eq('candidate_id', id)\
        .execute()
    
    return render_template('candidates/view.html', 
                         candidate=candidate.data, 
                         answers=answers.data)

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