from datetime import datetime, timezone, timedelta
from typing import Dict, Optional, Tuple, Union, Any
from common.logger import Logger
from database import supabase
import secrets

logger = Logger.instance()

class TestPublicException(Exception):
    """Exception for public test operations"""
    def __init__(self, message: str, error_type: str = "unexpected_error", original_error: Exception = None):
        self.message = message
        self.error_type = error_type
        self.original_error = original_error
        super().__init__(self.message)

class TestPublicService:
    @staticmethod
    def get_universal_test_info(token: str) -> Optional[Dict]:
        """Get test information for universal access token"""
        try:
            logger.debug(f"Pobieranie informacji o teście dla tokenu uniwersalnego")
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
        except Exception as e:
            logger.error(f"Błąd podczas pobierania informacji o teście: {str(e)}")
            raise TestPublicException(
                message="Nie udało się pobrać informacji o teście",
                error_type="test_not_found",
                original_error=e
            )
        return None

    # TODO: przemyslec to inaczej
    @staticmethod
    def get_candidate_test_info(token: str) -> Optional[Dict]:
        """Get test information for candidate-specific token"""
        try:
            logger.debug(f"Pobieranie informacji o teście kandydata")
            # Try PO2 token
            candidate = supabase.table('candidates')\
                .select('*, campaign:campaigns(*)')\
                .eq('access_token_po2', token)\
                .single()\
                .execute()
            
            if candidate.data:
                test = supabase.table('tests')\
                    .select('*')\
                    .eq('id', candidate.data['campaign']['po2_test_id'])\
                    .single()\
                    .execute()
                
                if test.data:
                    return {
                        'campaign': candidate.data['campaign'],
                        'test': test.data,
                        'stage': 'PO2',
                        'candidate': candidate.data
                    }
        except:
            pass
        
        try:
            # Try PO3 token
            candidate = supabase.table('candidates')\
                .select('*, campaign:campaigns(*)')\
                .eq('access_token_po3', token)\
                .single()\
                .execute()
            
            if candidate.data:
                test = supabase.table('tests')\
                    .select('*')\
                    .eq('id', candidate.data['campaign']['po3_test_id'])\
                    .single()\
                    .execute()
                
                if test.data:
                    return {
                        'campaign': candidate.data['campaign'],
                        'test': test.data,
                        'stage': 'PO3',
                        'candidate': candidate.data
                    }
        except Exception as e:
            logger.error(f"Błąd podczas pobierania informacji o teście kandydata: {str(e)}")
            raise TestPublicException(
                message="Nie udało się pobrać informacji o teście",
                error_type="test_not_found",
                original_error=e
            )
        
        return None

    @staticmethod
    def check_token_status(token: str) -> Dict[str, Any]:
        """Check if token is used or expired and get test info"""
        try:
            current_time = datetime.now(timezone.utc)
            
            # Try PO2 token first
            try:
                candidate = supabase.table('candidates')\
                    .select('*, campaign:campaigns(*)')\
                    .eq('access_token_po2', token)\
                    .single()\
                    .execute()
                
                if candidate.data:
                    is_used = candidate.data.get('access_token_po2_is_used', False)
                    expires_at = candidate.data.get('access_token_po2_expires_at')
                    
                    is_expired = TestPublicService._check_expiry(expires_at, current_time)
                    
                    stage = 'PO2'
                    completed_at = candidate.data.get('po2_completed_at')
                    
                    # Ensure dates are in ISO format
                    if expires_at and not isinstance(expires_at, str):
                        expires_at = expires_at.isoformat()
                    if completed_at and not isinstance(completed_at, str):
                        completed_at = completed_at.isoformat()
                        
                    return {
                        'candidate': candidate.data,
                        'is_used': is_used,
                        'is_expired': is_expired,
                        'stage': stage,
                        'completed_at': completed_at,
                        'expires_at': expires_at
                    }
            except:
                pass
            
            # Try PO3 token
            try:
                candidate = supabase.table('candidates')\
                    .select('*, campaign:campaigns(*)')\
                    .eq('access_token_po3', token)\
                    .single()\
                    .execute()
                
                if candidate.data:
                    is_used = candidate.data.get('access_token_po3_is_used', False)
                    expires_at = candidate.data.get('access_token_po3_expires_at')
                    
                    is_expired = TestPublicService._check_expiry(expires_at, current_time)
                    
                    stage = 'PO3'
                    completed_at = candidate.data.get('po3_completed_at')
                    
                    # Ensure dates are in ISO format
                    if expires_at and not isinstance(expires_at, str):
                        expires_at = expires_at.isoformat()
                    if completed_at and not isinstance(completed_at, str):
                        completed_at = completed_at.isoformat()
                        
                    return {
                        'candidate': candidate.data,
                        'is_used': is_used,
                        'is_expired': is_expired,
                        'stage': stage,
                        'completed_at': completed_at,
                        'expires_at': expires_at
                    }
            except:
                pass

            # Try universal token
            try:
                campaign = supabase.table('campaigns')\
                    .select('*')\
                    .eq('universal_access_token', token)\
                    .single()\
                    .execute()
                
                if campaign.data:
                    is_active = campaign.data.get('is_active', False)
                    return {
                        'candidate': campaign.data,
                        'is_used': False,
                        'is_expired': False,
                        'is_inactive': not is_active,
                        'stage': 'PO1',
                        'completed_at': None,
                        'expires_at': None
                    }
            except:
                pass

        except Exception as e:
            logger.error(f"Błąd podczas sprawdzania statusu tokenu: {str(e)}")
            raise TestPublicException(
                message="Nie udało się sprawdzić statusu tokenu",
                error_type="token_not_found",
                original_error=e
            )
        
        return {
            'candidate': None,
            'is_used': False,
            'is_expired': False,
            'stage': None,
            'completed_at': None,
            'expires_at': None
        }

    @staticmethod
    def _check_expiry(expires_at: str, current_time: datetime) -> bool:
        """Helper method to check if token is expired"""
        if not expires_at:
            return False
            
        try:
            if 'Z' in expires_at:
                expires_dt = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
            elif '+' in expires_at:
                expires_dt = datetime.fromisoformat(expires_at)
            else:
                expires_dt = datetime.fromisoformat(expires_at).replace(tzinfo=timezone.utc)
            
            return expires_dt < current_time
        except ValueError as e:
            logger.error(f"Błąd podczas parsowania daty: {str(e)}")
            return False

    @staticmethod
    def submit_universal_test(token: str, form_data: Dict[str, Any]) -> Tuple[bool, Optional[str], Optional[str]]:
        """Submit universal test and handle PO2 token generation"""
        try:
            test_info = TestPublicService.get_universal_test_info(token)
            if not test_info:
                raise TestPublicException(
                    message="Invalid token",
                    error_type="token_not_found"
                )

            # Check for existing submissions
            email = form_data.get('email')
            phone = form_data.get('phone')
            campaign_id = test_info['campaign']['id']
            
            logger.debug(f"Sprawdzanie istniejących wypełnień dla kampanii {campaign_id} email: {email}, phone: {phone}")
            
            existing_submissions = supabase.table('candidates')\
                .select('id')\
                .eq('campaign_id', campaign_id)\
                .or_(f'email.eq.{email},phone.eq.{phone}')\
                .execute()
                
            if existing_submissions.data:
                return False, None, "duplicate"

            # Process start time
            start_time = TestPublicService._parse_start_time(form_data.get('test_start_time'))
            current_time = datetime.now(timezone.utc)

            # Generate PO2 token if needed
            po2_token, po2_expires_at, recruitment_status = TestPublicService._generate_po2_token(
                test_info, current_time
            )

            # Create candidate
            candidate_data = TestPublicService._prepare_candidate_data(
                test_info, form_data, start_time, current_time,
                po2_token, po2_expires_at, recruitment_status
            )
            
            result = supabase.table('candidates').insert(candidate_data).execute()
            candidate_id = result.data[0]['id']

            # Process answers - always use PO1 for universal test submissions
            TestPublicService.process_test_answers(candidate_id, test_info['test']['id'], form_data, 'PO1')
            
            return True, po2_token, None

        except TestPublicException:
            raise
        except Exception as e:
            logger.error(f"Error submitting test: {str(e)}")
            raise TestPublicException(
                message="Error submitting test",
                error_type="unexpected_error",
                original_error=e
            )

    @staticmethod
    def _parse_start_time(start_time_str: Optional[str]) -> datetime:
        """Parse start time from form data"""
        if not start_time_str:
            return datetime.now(timezone.utc)
            
        try:
            start_time = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
            if start_time.tzinfo is None:
                start_time = start_time.replace(tzinfo=timezone.utc)
            return start_time
        except ValueError:
            return datetime.now(timezone.utc)

    @staticmethod
    def _generate_po2_token(
        test_info: Dict,
        current_time: datetime
    ) -> Tuple[Optional[str], Optional[datetime], str]:
        """Generate PO2 token if conditions are met"""
        po2_token = None
        po2_expires_at = None
        recruitment_status = 'PO1'
        
        if test_info['test'].get('passing_threshold', 1) == 0 and test_info['campaign'].get('po2_test_id'):
            po2_token = secrets.token_urlsafe(32)
            expiry_days = test_info['campaign'].get('po2_token_expiry_days', 7)
            po2_expires_at = current_time + timedelta(days=expiry_days)
            recruitment_status = 'PO2'
            
        return po2_token, po2_expires_at, recruitment_status

    @staticmethod
    def _prepare_candidate_data(
        test_info: Dict,
        form_data: Dict,
        start_time: datetime,
        current_time: datetime,
        po2_token: Optional[str],
        po2_expires_at: Optional[datetime],
        recruitment_status: str
    ) -> Dict:
        """Prepare candidate data for database insertion"""
        return {
            'campaign_id': test_info['campaign']['id'],
            'first_name': form_data.get('first_name'),
            'last_name': form_data.get('last_name'),
            'email': form_data.get('email'),
            'phone': form_data.get('phone'),
            'recruitment_status': recruitment_status,
            'po1_started_at': start_time.isoformat(),
            'po1_completed_at': current_time.isoformat(),
            'created_at': current_time.isoformat(),
            'updated_at': current_time.isoformat(),
            'access_token_po2': po2_token,
            'access_token_po2_expires_at': po2_expires_at.isoformat() if po2_expires_at else None
        }

    @staticmethod
    def process_test_answers(candidate_id: int, test_id: int, form_data: Dict[str, Any], stage: Optional[str] = None) -> None:
        """Process test answers"""
        try:
            if stage is None:
                # Determine stage based on test_id instead of recruitment_status
                result = supabase.table('candidates')\
                    .select('*, campaign:campaigns(*)')\
                    .eq('id', candidate_id)\
                    .single()\
                    .execute()
                
                if not result.data:
                    raise TestPublicException(
                        message="Could not find candidate",
                        error_type="unexpected_error"
                    )
                    
                # Determine stage based on which test_id matches
                campaign = result.data['campaign']
                if test_id == campaign['po1_test_id']:
                    stage = 'PO1'
                elif test_id == campaign['po2_test_id']:
                    stage = 'PO2'
                elif test_id == campaign['po2_5_test_id']:
                    stage = 'PO2_5'
                elif test_id == campaign['po3_test_id']:
                    stage = 'PO3'
                
                if not stage:
                    raise TestPublicException(
                        message="Could not determine stage for test",
                        error_type="unexpected_error"
                    )

                # Get all questions for this test
                questions = supabase.table('questions')\
                    .select('*')\
                    .eq('test_id', test_id)\
                    .execute()
                
                questions_lookup = {str(q['id']): q for q in questions.data}
                
                # Process answers
                answers_to_insert = []
                regular_answers = {}
                ah_points_answers = {}
                
                # First pass - organize the data
                for key, value in form_data.items():
                    if not key.startswith('answer_'):
                        continue
                        
                    if '_min' in key or '_max' in key:
                        continue
                        
                    # Handle AH_POINTS type answers
                    if any(suffix in key for suffix in ['_a', '_b', '_c', '_d', '_e', '_f', '_g', '_h']):
                        question_id = key.split('_')[1]
                        letter = key.split('_')[2]
                        
                        if question_id not in ah_points_answers:
                            ah_points_answers[question_id] = {}
                        
                        if value:  # Only store non-empty values
                            ah_points_answers[question_id][letter] = int(value or 0)
                    else:
                        question_id = key.split('_')[1]
                        regular_answers[question_id] = value

                # Process AH_POINTS answers
                for question_id, points in ah_points_answers.items():
                    if not points:  # Skip if no points recorded
                        continue
                        
                    question = questions_lookup.get(question_id)
                    if not question or question['test_id'] != test_id:
                        continue
                        
                    answer_data = {
                        'candidate_id': candidate_id,
                        'question_id': int(question_id),
                        'stage': stage,
                        'points_per_option': points,
                        'created_at': datetime.now(timezone.utc).isoformat()
                    }
                    answers_to_insert.append(answer_data)

                # Process regular answers
                for question_id, value in regular_answers.items():
                    question = questions_lookup.get(question_id)
                    if not question or question['test_id'] != test_id:
                        continue
                        
                    answer_data = {
                        'candidate_id': candidate_id,
                        'question_id': int(question_id),
                        'stage': stage,
                        'created_at': datetime.now(timezone.utc).isoformat()
                    }
                    
                    answer_type = question['answer_type']
                    
                    # Set the appropriate answer field based on type
                    if answer_type == 'TEXT':
                        answer_data['answer'] = str(value)
                    elif answer_type == 'BOOLEAN':
                        answer_data['answer'] = str(value.lower() == 'true')
                    elif answer_type == 'SCALE':
                        answer_data['answer'] = str(value)
                    elif answer_type == 'SALARY':
                        answer_data['answer'] = str(float(value) if value else 0)
                    elif answer_type == 'DATE':
                        answer_data['answer'] = str(value)
                    elif answer_type == 'ABCDEF':
                        answer_data['answer'] = str(value)
                    elif answer_type == 'NUMERIC':
                        answer_data['answer'] = str(float(value) if value else 0)
                        
                    answers_to_insert.append(answer_data)

                # Batch insert all answers
                if answers_to_insert:
                    supabase.table('candidate_answers').insert(answers_to_insert).execute()

        except Exception as e:
            logger.error(f"Error processing test answers: {str(e)}")
            raise TestPublicException(
                message="Error processing test answers",
                error_type="unexpected_error",
                original_error=e
            ) 