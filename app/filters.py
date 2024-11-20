from datetime import datetime

def format_datetime(dt_str):
    if not dt_str:
        return None
    try:
        if '.' in dt_str:
            dt_str = dt_str.split('.')[0]
        dt = datetime.fromisoformat(dt_str.replace('Z', ''))
        return dt.strftime('%Y-%m-%d %H:%M')
    except Exception as e:
        print(f"Error formatting datetime {dt_str}: {str(e)}")
        return dt_str