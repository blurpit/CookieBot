import functools
import logging

from discord import Object

from upgrades import ClickUpgrade, PassiveUpgrade, SwindleUpgrade, Upgrade

# Discord guilds
GUILD = Object(913924123405729812)
DEV_GUILD = Object(913924123405729812)

# How fast cookie counts are updated in the db
COOKIE_UPDATE_RATE = 5
# How fast the clicker/leaderboard message is updated on discord
DISCORD_UPDATE_RATE = 30
# Cookie button cooldown
COOKIE_COOLDOWN = 60
# Range of cookies obtainable from the button
COOKIE_RANGE = (1, COOKIE_COOLDOWN * 3 * 2)
# Percentage of cookies stolen when blue shelled
SWINDLE_AMOUNT = 0.8
# Number of decimal places to show bignums
BIGNUM_PLACES = 3
# Logger level
LOG_LEVEL = logging.INFO

def exp(coeff, base):
    @functools.cache
    def f(lvl):
        return round(coeff * pow(base, lvl - 1))
    return f

def blurbot_price(_):
    return 69 * 10 ** 68

def blurbot_cps(lvl):
    if lvl < 10:
        return lvl + 2
    else:
        return -10**96

PRICE_FACTOR = 200
shell = '<:blueshell:1222371607784198215>'
UPGRADES: list[Upgrade] = [
    ClickUpgrade  ('👍', 'Facebook Like Button',         exp(100, 4),            exp(4*100, 4)),
    ClickUpgrade  ('🧗‍♀️', 'Girl Scouts Ad Campaign',      exp(1000, 1000),        exp(8*1000, 1000)),
    PassiveUpgrade('👨‍🍳', 'Chef Freako',                  exp(1, 1.75),           exp(PRICE_FACTOR*1, 1.75)),
    PassiveUpgrade('🔥', 'Oven Eat the Food',            exp(50, 2),             exp(PRICE_FACTOR*50, 2)),
    PassiveUpgrade('🎤', 'Astley Automator',             exp(5000, 8),           exp(PRICE_FACTOR*5000, 8)),
    PassiveUpgrade('🛠️', 'Home Depot Bakery',            exp(150000, 75),        exp(PRICE_FACTOR*150000, 75)),
    PassiveUpgrade('🏰', 'Crypto Cookie Castle',         exp(500*10**6, 1500),   exp(PRICE_FACTOR*500*10**6, 1500)),
    PassiveUpgrade('🏗️', 'Cookie Construction Company',  exp(25*10**12, 250000), exp(PRICE_FACTOR*25*10**12, 250000)),
    PassiveUpgrade('🐢', 'Blurbot ver.1.22474487139...', blurbot_cps,            blurbot_price, hide=True),
    SwindleUpgrade(shell, 'Blue Shell',                  lambda l: 0.5,          lambda l: 0, hide=True)
]

COOKIE_QUOTES = [
    "C is for cookie, and cookie is for me.",
    # "Om nom nom nom.",
    "Home is here heart is. Heart where cookie is. Math clear: home is cookie.",
    "Sometimes me think, what is friend? And then me say: a friend is someone to share last cookie with.",
    "Chocolate chip important to me... It mean whole lot to me... Om nom nom nom.",
    "Fruit... or Cookie... Fruit... Cookie… Me Cookie Monster! This No-Brainer!",
    "Me love poetry... and cookies!",
    "Me wasn’t born with name Cookie Monster. It just nickname dat stuck. Me don’t remember me real name… Maybe it was Sidney?",
    "Today me will live in the moment, unless it’s unpleasant in which case me will eat a cookie.",
    "I’d give you another cookie, but I ate it.",
    "Me Love to Eat Cookies. Sometimes eat whole, sometimes me chew it.",
    "Keep Calm & Eat Cookies.",
    "No get upset, okay? Don’t get excited. Me not fussy - just give me box of cookies.",
    "Me lost me cookie at the disco.",
    "Me just met you and this is crazy, but you got cookie, so share it maybe?",
    "That what wrong with the media today. All they have is questions, questions, questions. They never have cookies.",
    "Me no cry because cookie is finished. Me smile because cookie happened!",
    "Early bird gets the worm. But cookie taste better than worm. So me sleep in.",
    "Cookie is like high five for stomach.",
    """Now what starts with the letter C?
    Cookie starts with C
    Let’s think of other things that starts with C
    Oh, who cares about the other things?
    C is for cookie, that’s good enough for me
    C is for cookie, that’s good enough for me 
    C is for cookie, that’s good enough for me 
    Oh, cookie, cookie, cookie starts with C
    C is for cookie, that’s good enough for me
    C is for cookie, that’s good enough for me 
    C is for cookie, that’s good enough for me 
    Oh, cookie, cookie, cookie starts with C""",
]
