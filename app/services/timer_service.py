from datetime import datetime, timezone, timedelta
import jwt
from typing import Dict, Optional
from common.logger import Logger
from common.config import Config

logger = Logger.instance()
config = Config.instance()

class TimerService:
    @staticmethod
    def create_timer_token(test_id: int, time_limit_minutes: int) -> str:
        """Create a JWT token containing timer information"""
        # Don't create token if time limit is 0 or None
        if not time_limit_minutes:
            return None
            
        current_time = datetime.now(timezone.utc)
        payload = {
            'test_id': test_id,
            'start_time': current_time.isoformat(),
            'time_limit_minutes': time_limit_minutes,
            'exp': current_time + timedelta(minutes=time_limit_minutes + 5)  # Add 5 min buffer
        }
        
        return jwt.encode(payload, config.SECRET_KEY, algorithm='HS256')
    
    @staticmethod
    def validate_timer_token(token: str) -> Dict:
        """Validate and decode timer token"""
        try:
            payload = jwt.decode(token, config.SECRET_KEY, algorithms=['HS256'])
            start_time = datetime.fromisoformat(payload['start_time'])
            time_limit = timedelta(minutes=payload['time_limit_minutes'])
            current_time = datetime.now(timezone.utc)
            
            elapsed_time = current_time - start_time
            remaining_time = time_limit - elapsed_time
            
            return {
                'valid': True,
                'remaining_seconds': max(0, int(remaining_time.total_seconds())),
                'expired': remaining_time.total_seconds() <= 0,
                'test_id': payload['test_id']
            }
        except jwt.ExpiredSignatureError:
            return {'valid': False, 'expired': True}
        except Exception as e:
            logger.error(f"Error validating timer token: {str(e)}")
            return {'valid': False, 'expired': False}
    
    @staticmethod
    def get_remaining_time(token: str) -> Optional[int]:
        """Get remaining time in seconds from token"""
        validation = TimerService.validate_timer_token(token)
        if validation['valid']:
            return validation['remaining_seconds']
        return None 