from flask import Blueprint, render_template, request, redirect, url_for, jsonify
from common.logger import Logger
from services.test_public_service import TestPublicService, TestPublicException
from services.timer_service import TimerService
from database import supabase
from datetime import datetime, timezone
from filters import format_datetime

test_public_bp = Blueprint('test_public', __name__)
logger = Logger.instance()

@test_public_bp.route('/test/<token>')
def landing(token):
    """Landing page for universal test"""
    try:
        # Check token status
        token_status = TestPublicService.check_token_status(token)
        
        # Handle invalid token
        if not token_status['candidate']:
            return render_template('tests/error.html',
                                title="Nieprawidłowy token",
                                message="Podany link jest nieprawidłowy.",
                                error_type="token_not_found")
        
        # Handle inactive campaign
        if token_status['stage'] == 'PO1' and token_status['is_inactive']:
            return render_template('tests/inactive.html')
        
        # Get test info
        test_info = TestPublicService.get_universal_test_info(token)
        if not test_info:
            return render_template('tests/error.html',
                                title="Test nie został znaleziony",
                                message="Nie znaleziono testu dla podanego linku.",
                                error_type="test_not_found")
        
        # Dodaj nazwę etapu
        stage_name = "Ankieta wstępna"
        
        return render_template('tests/landing.html',
                            campaign=test_info['campaign'],
                            test=test_info['test'],
                            token=token,
                            stage_name=stage_name)
                            
    except TestPublicException as e:
        logger.error(f"Error in landing page: {str(e)}")
        return render_template('tests/error.html',
                            title="Wystąpił błąd",
                            message=e.message,
                            error_type=e.error_type)
    except Exception as e:
        logger.error(f"Unexpected error in landing page: {str(e)}")
        return render_template('tests/error.html',
                            title="Wystąpił błąd",
                            message="Nieoczekiwany błąd podczas ładowania strony.",
                            error_type="unexpected_error")

@test_public_bp.route('/test/<token>/start', methods=['POST'])
def start_test(token):
    """Start universal test"""
    try:
        test_info = TestPublicService.get_universal_test_info(token)
        if not test_info:
            return render_template('tests/error.html',
                                title="Test nie został znaleziony",
                                message="Nie znaleziono testu dla podanego linku.",
                                error_type="test_not_found")
        
        if not test_info['campaign'].get('is_active', False):
            return render_template('tests/inactive.html')
        
        questions = supabase.table('questions')\
            .select('*')\
            .eq('test_id', test_info['test']['id'])\
            .order('order_number')\
            .execute()
        
        # Create timer token if test has time limit
        timer_token = None
        time_limit = test_info['test'].get('time_limit_minutes', 0)
        logger.debug(f"Test time limit: {time_limit} minutes")
        
        if time_limit > 0:
            timer_token = TimerService.create_timer_token(
                test_info['test']['id'],
                time_limit
            )
            logger.debug(f"Created timer token: {timer_token}")
        
        # Check if test has auto-progression to PO2
        has_next_stage = (test_info['test'].get('passing_threshold', 1) == 0 and 
                        test_info['campaign'].get('po2_test_id'))
        
        return render_template('tests/survey.html',
                            campaign=test_info['campaign'],
                            test=test_info['test'],
                            questions=questions.data,
                            token=token,
                            timer_token=timer_token,
                            has_next_stage=has_next_stage)
    
    except Exception as e:
        logger.error(f"Error starting test: {str(e)}")
        return render_template('tests/error.html',
                            title="Wystąpił błąd",
                            message="Nie udało się rozpocząć testu.",
                            error_type="unexpected_error")

@test_public_bp.route('/test/<token>/submit', methods=['POST'])
def submit_test(token):
    """Submit the universal test"""
    try:
        success, po2_token, error = TestPublicService.submit_universal_test(token, request.form)
        
        if not success:
            if error == "duplicate":
                return redirect(url_for('test_public.duplicate'))
            return render_template('tests/error.html',
                                title="Wystąpił błąd",
                                message="Nie udało się zapisać testu.",
                                error_type="unexpected_error")
        
        # If PO2 token was generated, redirect directly to PO2 landing page
        if po2_token:
            return redirect(url_for('test_public.candidate_landing', token=po2_token))
        
        return redirect(url_for('test_public.complete'))
        
    except TestPublicException as e:
        logger.error(f"Error submitting test: {str(e)}")
        return render_template('tests/error.html',
                            title="Wystąpił błąd",
                            message=e.message,
                            error_type=e.error_type)
    except Exception as e:
        logger.error(f"Unexpected error submitting test: {str(e)}")
        return render_template('tests/error.html',
                            title="Wystąpił błąd",
                            message="Nieoczekiwany błąd podczas zapisywania testu.",
                            error_type="unexpected_error")

@test_public_bp.route('/test/complete')
def complete():
    """Show test completion page"""
    return render_template('tests/complete.html')

@test_public_bp.route('/test/candidate/<token>')
def candidate_landing(token):
    """Landing page for candidate test"""
    try:
        # Check if token is used or expired
        token_status = TestPublicService.check_token_status(token)
        
        # Handle invalid token
        if not token_status['candidate']:
            return render_template('tests/error.html',
                                title="Nieprawidłowy token",
                                message="Podany link jest nieprawidłowy.",
                                error_type="token_not_found")
        
        # Handle PO2/PO3 specific checks
        if token_status['stage'] in ['PO2', 'PO3']:
            # Check if test was already completed
            if token_status['completed_at']:
                return render_template('tests/completed.html',
                                    completed_at=format_datetime(token_status['completed_at']))
            
            # Check if token was already used
            if token_status['is_used']:
                return render_template('tests/used.html')
            
            # Check if token is expired
            if token_status['is_expired']:
                expires_at = format_datetime(token_status['expires_at'])
                return render_template('tests/error.html',
                                    title="Link wygasł",
                                    message=f"Link do testu wygasł {expires_at} i nie jest już aktywny.",
                                    error_type="test_expired")
        
        # Get test info
        test_info = TestPublicService.get_candidate_test_info(token)
        if not test_info:
            return render_template('tests/error.html',
                                title="Test nie został znaleziony",
                                message="Nie znaleziono testu dla podanego linku.",
                                error_type="test_not_found")
        
        # Dodaj nazwę etapu w zależności od typu testu i stage
        stage_name = ""
        if test_info['stage'] == 'PO2':
            if test_info['test']['test_type'] == 'IQ':
                stage_name = "Ankieta nr 2 - Test zdolności poznawczych"
            elif test_info['test']['test_type'] == 'EQ':
                stage_name = "Ankieta nr 2 - Kwestionariusz Samooceny"
        elif test_info['stage'] == 'PO3':
            stage_name = "Ankieta nr 3 - Test końcowy"
        
        return render_template('tests/landing.html',
                            campaign=test_info['campaign'],
                            test=test_info['test'],
                            token=token,
                            candidate=test_info.get('candidate'),
                            stage_name=stage_name)
                            
    except TestPublicException as e:
        logger.error(f"Error in candidate landing: {str(e)}")
        return render_template('tests/error.html',
                            title="Wystąpił błąd",
                            message=e.message,
                            error_type=e.error_type)
    except Exception as e:
        logger.error(f"Unexpected error in candidate landing: {str(e)}")
        return render_template('tests/error.html',
                            title="Wystąpił błąd",
                            message="Nieoczekiwany błąd podczas ładowania strony.",
                            error_type="unexpected_error")

@test_public_bp.route('/test/duplicate')
def duplicate():
    """Show test duplicate page"""
    return render_template('tests/duplicate.html')

@test_public_bp.route('/test/<token>/cancel')
def cancel_test(token):
    """Cancel the universal test"""
    try:
        return redirect(url_for('test_public.cancelled'))
    except Exception as e:
        logger.error(f"Error cancelling test: {str(e)}")
        return render_template('tests/error.html',
                            title="Wystąpił błąd",
                            message="Nie udało się anulować testu.",
                            error_type="unexpected_error")

@test_public_bp.route('/test/candidate/<token>/cancel')
def cancel_candidate_test(token):
    """Cancel the candidate test"""
    try:
        return redirect(url_for('test_public.cancelled'))
    except Exception as e:
        logger.error(f"Error cancelling test: {str(e)}")
        return render_template('tests/error.html',
                            title="Wystąpił błąd",
                            message="Nie udało się anulować testu.",
                            error_type="unexpected_error")

@test_public_bp.route('/test/cancelled')
def cancelled():
    """Show test cancelled page"""
    return render_template('tests/cancelled.html')

@test_public_bp.route('/test/candidate/<token>/start', methods=['POST'])
def start_candidate_test(token):
    """Start candidate test"""
    try:
        # Check if token is used or expired
        token_status = TestPublicService.check_token_status(token)
        
        # Handle invalid token
        if not token_status['candidate']:
            return render_template('tests/error.html',
                                title="Nieprawidłowy token",
                                message="Podany link jest nieprawidłowy.",
                                error_type="token_not_found")
        
        # Handle PO2/PO3 specific checks
        if token_status['stage'] in ['PO2', 'PO3']:
            # Check if test was already completed
            if token_status['completed_at']:
                return render_template('tests/completed.html',
                                    completed_at=format_datetime(token_status['completed_at']))
            
            # Check if token was already used
            if token_status['is_used']:
                return render_template('tests/used.html')
            
            # Check if token is expired
            if token_status['is_expired']:
                expires_at = format_datetime(token_status['expires_at'])
                return render_template('tests/error.html',
                                    title="Link wygasł",
                                    message=f"Link do testu wygasł {expires_at} i nie jest już aktywny.",
                                    error_type="test_expired")
            
            try:
                # Mark token as used and record start time
                current_time = datetime.now(timezone.utc)
                update_data = {
                    f'access_token_{token_status["stage"].lower()}_is_used': True,
                    f'{token_status["stage"].lower()}_started_at': current_time.isoformat(),
                    'updated_at': current_time.isoformat()
                }
                
                supabase.table('candidates')\
                    .update(update_data)\
                    .eq('id', token_status['candidate']['id'])\
                    .execute()
            except Exception as e:
                logger.error(f"Error marking token as used: {str(e)}")
                return render_template('tests/error.html',
                                    title="Wystąpił błąd",
                                    message="Nie udało się rozpocząć testu.",
                                    error_type="unexpected_error")
        
        # Get test info
        test_info = TestPublicService.get_candidate_test_info(token)
        if not test_info:
            return render_template('tests/error.html',
                                title="Test nie został znaleziony",
                                message="Nie znaleziono testu dla podanego linku.",
                                error_type="test_not_found")
        
        try:
            # Get questions
            questions = supabase.table('questions')\
                .select('*')\
                .eq('test_id', test_info['test']['id'])\
                .order('order_number')\
                .execute()
            
            if not questions.data:
                return render_template('tests/error.html',
                                    title="Brak pytań",
                                    message="Test nie zawiera żadnych pytań.",
                                    error_type="no_questions")
            
            # Create timer token if test has time limit
            timer_token = None
            time_limit = test_info['test'].get('time_limit_minutes', 0)
            logger.debug(f"Test time limit: {time_limit} minutes")
            
            if time_limit > 0:
                timer_token = TimerService.create_timer_token(
                    test_info['test']['id'],
                    time_limit
                )
                logger.debug(f"Created timer token: {timer_token}")
            
            # Choose template based on test type
            template = 'tests/survey.html'
            if test_info['test']['test_type'] in ['IQ', 'EQ']:
                template = 'tests/cognitive.html'
            
            return render_template(template,
                                campaign=test_info['campaign'],
                                test=test_info['test'],
                                questions=questions.data,
                                token=token,
                                timer_token=timer_token,
                                candidate=test_info.get('candidate'))
        
        except Exception as e:
            logger.error(f"Error getting questions: {str(e)}")
            return render_template('tests/error.html',
                                title="Wystąpił błąd",
                                message="Nie udało się pobrać pytań testu.",
                                error_type="unexpected_error")
                                
    except TestPublicException as e:
        logger.error(f"Error in start candidate test: {str(e)}")
        return render_template('tests/error.html',
                            title="Wystąpił błąd",
                            message=e.message,
                            error_type=e.error_type)
    except Exception as e:
        logger.error(f"Unexpected error in start candidate test: {str(e)}")
        return render_template('tests/error.html',
                            title="Wystąpił błąd",
                            message="Nieoczekiwany błąd podczas rozpoczynania testu.",
                            error_type="unexpected_error")

@test_public_bp.route('/test/candidate/<token>/submit', methods=['POST', 'GET'])
def submit_candidate_test(token):
    """Submit the candidate test"""
    if request.method == 'GET':
        # Redirect GET requests to error page
        return render_template('tests/error.html',
                            title="Nieprawidłowe żądanie",
                            message="Test został już zapisany lub wystąpił błąd podczas zapisu. Nie można ponownie przesłać odpowiedzi.",
                            error_type="invalid_request")

    try:
        # Get test info
        test_info = TestPublicService.get_candidate_test_info(token)
        if not test_info:
            return render_template('tests/error.html',
                                title="Test nie został znaleziony",
                                message="Nie znaleziono testu dla podanego linku.",
                                error_type="test_not_found")

        candidate_id = test_info['candidate']['id']
        stage = test_info['stage']
        current_time = datetime.now(timezone.utc)

        try:
            # Process answers
            TestPublicService.process_test_answers(candidate_id, test_info['test']['id'], request.form)
            
            # Update candidate with completion time and mark token as used
            update_data = {
                f'{stage.lower()}_completed_at': current_time.isoformat(),
                f'access_token_{stage.lower()}_is_used': True,
                'updated_at': current_time.isoformat()
            }
            
            supabase.table('candidates')\
                .update(update_data)\
                .eq('id', candidate_id)\
                .execute()
            
            return redirect(url_for('test_public.complete'))
            
        except TestPublicException as e:
            if "duplicate key value violates unique constraint" in str(e.original_error):
                return render_template('tests/error.html',
                                    title="Test został już zapisany",
                                    message="Ten test został już wcześniej zapisany w systemie. Nie można ponownie przesłać odpowiedzi.",
                                    error_type="duplicate_submission")
            raise e
        
    except TestPublicException as e:
        logger.error(f"Error submitting candidate test: {str(e)}")
        return render_template('tests/error.html',
                            title="Wystąpił błąd",
                            message=e.message,
                            error_type=e.error_type)
    except Exception as e:
        logger.error(f"Unexpected error submitting candidate test: {str(e)}")
        return render_template('tests/error.html',
                            title="Wystąpił błąd",
                            message="Nieoczekiwany błąd podczas zapisywania testu.",
                            error_type="unexpected_error")

@test_public_bp.route('/api/timer/validate', methods=['POST'])
def validate_timer():
    """Validate timer token and return remaining time"""
    try:
        timer_token = request.json.get('timer_token')
        if not timer_token:
            return jsonify({'error': 'No timer token provided'}), 400
            
        validation = TimerService.validate_timer_token(timer_token)
        return jsonify(validation)
        
    except Exception as e:
        logger.error(f"Error validating timer: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500
 