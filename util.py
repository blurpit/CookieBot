import math

from config import BIGNUM_PLACES, UPGRADES


def time_str(s):
    seconds = math.ceil(s)
    y = seconds // (60 * 60 * 24 * 365)
    d = seconds // (60 * 60 * 24) % 365
    h = seconds // (60 * 60) % 24
    m = seconds // 60 % 60
    s = seconds % 60

    strs = [f'{s}s']
    if m > 0:
        strs.append(f'{m}m')
    if h > 0:
        strs.append(f'{h}h')
    if d > 0:
        strs.append(f'{d}d')
    if y > 0:
        y = bignum(y)
        if not y[-1].isdigit():
            # add a space if there's a number label
            y += ' '
        strs.append(f'{y}yr')
    return ' '.join(reversed(strs))

def trunc_str(n, ndigits):
    p = 10**ndigits
    n = math.trunc(n * p) / p
    return f'{n:.{ndigits}f}'.rstrip('0').rstrip('.')

_numnames = [
    'million', 'billion', 'trillion', 'quadrillion', 'quintillion',
    'sextillion', 'septillion', 'octillion', 'nonillion', 'decillion',
    'undecillion', 'duodecillion', 'tredecillion', 'quattuordecillion',
    'quindecillion', 'sexdecillion', 'septendecillion', 'octodecillion',
    'novemdecillion', 'vigintillion'
]
def bignum(n):
    if not isinstance(n, int):
        raise TypeError(f"bignum requires int, not {type(n)}")
    neg = '-' if n < 0 else ''
    n = abs(n)
    if n < 10_000_000:
        return f'{n:,}'

    exp = len(str(n))-1
    mag = exp // 3
    index = mag - 2
    if index < len(_numnames):
        num = n // (10 ** (3*mag - BIGNUM_PLACES)) / 10**BIGNUM_PLACES
        num_str = trunc_str(num, BIGNUM_PLACES)
        return f'{neg}{num_str} {_numnames[index]}'
    else:
        num = n // (10 ** (exp - BIGNUM_PLACES)) / 10**BIGNUM_PLACES
        num_str = trunc_str(num, BIGNUM_PLACES)
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

def num_suffix(n: int):
    digit = str(n)[-1]
    if digit == '1':
        return 'st'
    elif digit == '2':
        return 'nd'
    elif digit == '3':
        return 'rd'
    return 'th'

def print_upgrade_values(to_level=20):
    for u in UPGRADES:
        print(u.name)
        print('{:<8} {:<25} {}'.format('Lv.', 'Cost', f'🍪/{u.unit}'))
        for lvl in range(1, to_level + 1):
            val = u.get_cookies_per_unit(lvl)
            price = u.get_price(lvl)
            print('{:<8} {:<25} {}'.format(lvl, bignum(price), bignum(val)))
        print()
