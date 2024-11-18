from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from database import supabase
import uuid
from datetime import datetime

campaign_bp = Blueprint('campaign', __name__, url_prefix='/campaigns')

# Helper function for datetime formatting
def format_datetime(dt_str):
    if not dt_str:
        return None
    try:
        # Parse the datetime string
        if '.' in dt_str:
            # Remove microseconds if present
            dt_str = dt_str.split('.')[0]
        
        # Convert to datetime object
        dt = datetime.fromisoformat(dt_str.replace('Z', ''))
        
        # Format without milliseconds
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    except Exception as e:
        print(f"Error formatting datetime {dt_str}: {str(e)}")
        return dt_str

@campaign_bp.route('/')
def list():
    campaigns = supabase.table('campaigns').select('*').execute()
    # Format datetime for each campaign
    for campaign in campaigns.data:
        if campaign.get('created_at'):
            campaign['created_at'] = format_datetime(campaign['created_at'])
        if campaign.get('updated_at'):
            campaign['updated_at'] = format_datetime(campaign['updated_at'])
    return render_template('campaigns/list.html', campaigns=campaigns.data)

@campaign_bp.route('/<int:id>/generate-link', methods=['POST'])
def generate_link(id):
    try:
        # Generate a unique token
        token = str(uuid.uuid4())
        
        # Update campaign with the new token
        supabase.table('campaigns')\
            .update({'universal_access_token': token})\
            .eq('id', id)\
            .execute()
            
        flash('Link został wygenerowany pomyślnie', 'success')
    except Exception as e:
        flash(f'Wystąpił błąd podczas generowania linku: {str(e)}', 'danger')
    
    return redirect(url_for('campaign.list'))

@campaign_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
def edit(id):
    if request.method == 'POST':
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
            
            # Update campaign
            supabase.table('campaigns')\
                .update(campaign_data)\
                .eq('id', id)\
                .execute()
            
            # Delete all existing tests for this campaign
            supabase.table('tests')\
                .delete()\
                .eq('campaign_id', id)\
                .execute()
            
            # Add new and updated tests
            if 'tests' in request.form:
                for test_data in request.form.getlist('tests'):
                    if isinstance(test_data, str):
                        import json
                        test_data = json.loads(test_data)
                    
                    test = {
                        'campaign_id': id,
                        'test_type': test_data['test_type'],
                        'stage': test_data['stage'],
                        'weight': int(test_data['weight']),
                        'description': test_data.get('description', ''),
                        'passing_threshold': int(test_data.get('passing_threshold', 0)),
                        'time_limit_minutes': int(test_data.get('time_limit_minutes', 0))
                    }
                    
                    # Insert test
                    supabase.table('tests').insert(test).execute()
                
            flash('Kampania została zaktualizowana pomyślnie', 'success')
            return redirect(url_for('campaign.list'))
        except Exception as e:
            flash(f'Wystąpił błąd: {str(e)}', 'danger')
            print(f"Error details: {str(e)}")
    
    campaign = supabase.table('campaigns')\
        .select('*, tests(*)')\
        .eq('id', id)\
        .single()\
        .execute()
        
    return render_template('campaigns/edit.html', campaign=campaign.data)

@campaign_bp.route('/<int:id>/delete', methods=['POST'])
def delete(id):
    try:
        # First delete all tests associated with the campaign
        supabase.table('tests')\
            .delete()\
            .eq('campaign_id', id)\
            .execute()
            
        # Then delete the campaign
        supabase.table('campaigns')\
            .delete()\
            .eq('id', id)\
            .execute()
            
        return jsonify({'message': 'Kampania została usunięta pomyślnie'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@campaign_bp.route('/add', methods=['GET', 'POST'])
def add():
    if request.method == 'POST':
        try:
            print("Form data:", request.form)
            
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # First, create the campaign
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
            
            print("Campaign data to insert:", campaign_data)
            
            # Insert campaign and get the response
            campaign_response = supabase.table('campaigns').insert(campaign_data).execute()
            campaign_id = campaign_response.data[0]['id']
            
            print("Campaign response:", campaign_response.data)
            
            # Process tests and questions
            if 'tests' in request.form:
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
                    
                    # Process questions for this test
                    if 'questions' in test_data:
                        for question_data in test_data['questions']:
                            question = {
                                'test_id': test_id,
                                'question_text': question_data['question_text'],
                                'answer_type': question_data['answer_type'],
                                'points': int(question_data['points']),
                                'order_number': int(question_data.get('order', 1)),
                                'is_required': question_data.get('is_required', True)
                            }
                            
                            # Add answer fields based on type
                            if question_data['answer_type'] == 'ABCD':
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
                            else:
                                question['correct_answer_text'] = question_data.get('correct_answer_text', '')
                            
                            supabase.table('questions').insert(question).execute()
            
            flash('Kampania została dodana pomyślnie', 'success')
            return redirect(url_for('campaign.list'))
            
        except Exception as e:
            flash(f'Wystąpił błąd: {str(e)}', 'danger')
            print(f"Error details: {str(e)}")
    
    return render_template('campaigns/add.html')

@campaign_bp.route('/<int:id>/data')
def get_campaign_data(id):
    try:
        # Get campaign with its tests
        campaign = supabase.table('campaigns')\
            .select('*, tests(*)')\
            .eq('id', id)\
            .single()\
            .execute()
            
        if not campaign.data:
            return jsonify({'error': 'Campaign not found'}), 404
            
        # Format dates for response
        if campaign.data.get('created_at'):
            campaign.data['created_at'] = format_datetime(campaign.data['created_at'])
        if campaign.data.get('updated_at'):
            campaign.data['updated_at'] = format_datetime(campaign.data['updated_at'])
            
        return jsonify(campaign.data), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500 