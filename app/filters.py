from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from flask import app

def format_datetime(value):
    """Format a datetime to a pretty string."""
    if not value:
        return ''
    
    if isinstance(value, str):
        try:
            dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
        except ValueError:
            return value
    else:
        dt = value
        
    # Konwersja do strefy czasowej Warsaw
    local_dt = dt.astimezone(ZoneInfo("Europe/Warsaw"))
    # Zmiana formatu na dd.mm.yyyy HH:MM
    return local_dt.strftime('%d.%m.%Y %H:%M')