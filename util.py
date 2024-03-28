import functools
import math

import discord as d

from config import BIGNUM_PLACES


class DbBreak(Exception):
    """ If this exception is raised inside an `async with bot.db`, the database will be saved,
        unlike with other exceptions. """
    pass

class InteractionResponse(DbBreak):
    def __init__(self, message: str | dict):
        """ Raise this inside a function decorated by @catch_errors to respond to the interaction
            with the given message. Message can be a string or a dict passed to send_message() """
        self.message = message

def catch_errors(f):
    """ Decorator that catches errors and responds to interactions with the error message.
        If the raised error is not a util.InteractionResponse, the error will be raised again. """
    @functools.wraps(f)
    async def wrapper(*args, **kwargs):
        try:
            return await f(*args, **kwargs)
        except InteractionResponse as e:
            await _interaction_respond(args, e.message)
        except Exception as e:
            msg = f"```{type(e).__name__}: {str(e)}```"
            await _interaction_respond(args, msg)
            raise e from None
    return wrapper

async def _interaction_respond(args, msg):
    i: d.Interaction | None = None
    if len(args) > 0 and isinstance(args[0], d.Interaction):
        i = args[0]
    elif len(args) > 1 and isinstance(args[1], d.Interaction):
        i = args[1]

    if i is None:
        return
    if i.is_expired():
        raise d.DiscordException("Interaction expired")

    if isinstance(msg, str):
        msg = dict(content=msg)

    if i.response.is_done():
        await i.followup.send(**msg)
    else:
        await i.response.send_message(**msg)


def exp(coeff, base):
    """ returns an exponential function f(x) = coeff * base ^ (x-1) """
    @functools.cache
    def f(lvl):
        return round(coeff * pow(base, lvl - 1))
    return f

def lin(yint, slope):
    """ returns a linear function f(x) = yint + (x-1) * slope """
    @functools.cache
    def f(lvl):
        return yint + (lvl - 1) * slope
    return f

def cap(f, max_lvl):
    """ returns a function with an input cap on f """
    return lambda lvl: f(lvl) if lvl <= max_lvl else math.inf

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
    if isinstance(n, str):
        return n
    elif n == math.inf:
        return 'Infinity'
    elif not isinstance(n, int):
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

def percent(p):
    p = round(p * 100, 1)
    if p % 1 == 0:
        p = int(p)
    return f'{p}%'
