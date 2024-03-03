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


_C = ["", "C", "CC", "CCC", "CD", "D", "DC", "DCC", "DCCC", "CM"]
_X = ["", "X", "XX", "XXX", "XL", "L", "LX", "LXX", "LXXX", "XC"]
_I = ["", "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX"]
def roman(num):
    if not (0 < num < 1000):
        return str(num)

    hundreds = _C[(num % 1000) // 100]
    tens = _X[(num % 100) // 10]
    ones = _I[num % 10]
    return hundreds + tens + ones
