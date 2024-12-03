from datetime import datetime, timezone
from zoneinfo import ZoneInfo

def format_datetime(dt_str):
    if not dt_str:
        return None
    try:
        if '.' in dt_str:
            dt_str = dt_str.split('.')[0]
        dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        local_dt = dt.astimezone(ZoneInfo("Europe/Warsaw"))
        return local_dt.strftime('%Y-%m-%d %H:%M')
    except Exception as e:
        print(f"Error formatting datetime {dt_str}: {str(e)}")
        return dt_str