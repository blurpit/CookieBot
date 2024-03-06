import math
from config import BIGNUM_PLACES


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

_numnames = [
    'million', 'billion', 'trillion', 'quadrillion', 'quintillion',
    'sextillion', 'septillion', 'octillion', 'nonillion', 'decillion',
    'undecillion', 'duodecillion', 'tredecillion', 'quattuordecillion',
    'quindecillion', 'sexdecillion', 'septendecillion', 'octodecillion',
    'novemdecillion', 'vigintillion'
]
def bignum(n):
    if not isinstance(n, int):
        return n
    neg = '-' if n < 0 else ''
    n = abs(n)
    if n < 10_000_000:
        return f'{n:,}'

    exp = int(math.log10(n))
    mag = exp // 3
    index = mag - 2
    if index < len(_numnames):
        num = n / (1000 ** mag)
        num_str = f'{num:.{BIGNUM_PLACES}f}'.rstrip('0').rstrip('.')
        return f'{neg}{num_str} {_numnames[index]}'
    else:
        num = n / (10 ** exp)
        num_str = f'{num:.{BIGNUM_PLACES}f}'.rstrip('0').rstrip('.')
        return f'{neg}{num_str}e+{exp}'

_C = ["", "C", "CC", "CCC", "CD", "D", "DC", "DCC", "DCCC", "CM"]
_X = ["", "X", "XX", "XXX", "XL", "L", "LX", "LXX", "LXXX", "XC"]
_I = ["", "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX"]
def roman(n: int):
    if n == 0:
        return ''
    elif not (0 < n < 1000):
        return str(n)

    hundreds = _C[(n % 1000) // 100]
    tens = _X[(n % 100) // 10]
    ones = _I[n % 10]
    return hundreds + tens + ones
