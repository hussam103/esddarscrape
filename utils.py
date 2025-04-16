"""
Utility functions for the Etimad Tenders application
"""
import datetime
import pytz

# Saudi Arabia timezone (Riyadh)
SAUDI_TIMEZONE = pytz.timezone('Asia/Riyadh')

def get_saudi_now():
    """
    Returns the current datetime in Saudi Arabia timezone (Riyadh)
    """
    return datetime.datetime.now(pytz.utc).astimezone(SAUDI_TIMEZONE)

def get_saudi_today_start():
    """
    Returns the start of the current day in Saudi Arabia timezone (Riyadh)
    """
    now = get_saudi_now()
    today_start = datetime.datetime.combine(now.date(), datetime.time.min)
    return SAUDI_TIMEZONE.localize(today_start)

def get_saudi_time_days_ago(days):
    """
    Returns a datetime object representing 'days' days ago from current Saudi time
    """
    now = get_saudi_now()
    past_datetime = now - datetime.timedelta(days=days)
    return past_datetime

def get_saudi_time_hours_ago(hours):
    """
    Returns a datetime object representing 'hours' hours ago from current Saudi time
    """
    now = get_saudi_now()
    past_datetime = now - datetime.timedelta(hours=hours)
    return past_datetime

def saudi_time_to_utc(saudi_time):
    """
    Convert a Saudi Arabia timezone aware datetime to UTC
    """
    if saudi_time.tzinfo is None:
        saudi_time = SAUDI_TIMEZONE.localize(saudi_time)
    return saudi_time.astimezone(pytz.utc)

def format_saudi_datetime(dt, include_time=True):
    """
    Format a datetime object to Saudi Arabia timezone
    """
    if dt is None:
        return None
        
    # If the datetime is naive (has no timezone), assume it's in UTC
    if dt.tzinfo is None:
        dt = pytz.utc.localize(dt)
        
    # Convert to Saudi timezone
    saudi_dt = dt.astimezone(SAUDI_TIMEZONE)
    
    # Format with or without time
    if include_time:
        return saudi_dt.strftime('%Y-%m-%d %H:%M:%S')
    else:
        return saudi_dt.strftime('%Y-%m-%d')