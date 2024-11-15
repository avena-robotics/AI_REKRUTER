from flask import Blueprint, render_template, request
from database import supabase

candidate_bp = Blueprint('candidate', __name__, url_prefix='/candidates')

@candidate_bp.route('/')
def list():
    campaign_code = request.args.get('campaign_code')
    status = request.args.get('status')
    
    # Get all campaigns for the dropdown
    campaigns = supabase.table('campaigns').select('code, title').execute()
    
    # Get candidates with filters
    query = supabase.table('candidates').select('*')
    
    if campaign_code:
        query = query.eq('campaign_id', campaign_code)
    if status:
        query = query.eq('recruitment_status', status)
        
    candidates = query.execute()
    
    return render_template('candidates/list.html', 
                         candidates=candidates.data,
                         campaigns=campaigns.data)

@candidate_bp.route('/<int:id>')
def view(id):
    candidate = supabase.table('candidates').select('*').eq('id', id).single().execute()
    answers = supabase.table('candidate_answers')\
        .select('*, questions(*)')\
        .eq('candidate_id', id)\
        .execute()
    return render_template('candidates/view.html', 
                         candidate=candidate.data, 
                         answers=answers.data) 