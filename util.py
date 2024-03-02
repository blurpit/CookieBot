import math


def time_str(seconds):
    seconds = math.ceil(seconds)
    if seconds > 3600:
        return f'{seconds // 3600} hour'
    elif seconds > 60:
        return f'{seconds // 60} minute'
    else:
        return f'{seconds} second'

def short_time_str(seconds):
    seconds = math.ceil(seconds)
    if seconds > 3600:
        return f'{seconds // 3600}h'
    elif seconds > 60:
        return f'{seconds // 60}m'
    else:
        return f'{seconds}s'
