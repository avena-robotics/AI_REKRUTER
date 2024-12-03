from datetime import datetime, timezone
from zoneinfo import ZoneInfo

def format_datetime(dt):
    if not dt:
        return None
    try:
        # If input is string, convert to datetime
        if isinstance(dt, str):
            if '.' in dt:
                dt = dt.split('.')[0]
            dt = datetime.fromisoformat(dt.replace('Z', '+00:00'))
        
        # Ensure timezone info
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
            
        # Convert to local timezone
        local_dt = dt.astimezone(ZoneInfo("Europe/Warsaw"))
        return local_dt.strftime('%Y-%m-%d %H:%M:%S')
    except Exception as e:
        print(f"Error formatting datetime {dt}: {str(e)}")
        return str(dt)