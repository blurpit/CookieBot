import logging

from discord import Object

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
SWINDLE_AMOUNT = 0.5
# Percentage of cookies given away when first place blue shells themselves
SWINDLE_BACKFIRE_AMOUNT = 0.25
# Number of decimal places to show bignums
BIGNUM_PLACES = 3
# Logger level
LOG_LEVEL = logging.INFO

COOKIE_QUOTES = [
    "C is for cookie, and cookie is for me.",
    # "Om nom nom nom.",
    "Home is where heart is. Heart where cookie is. Math clear: home is cookie.",
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

SWINDLE_QUOTES = [
    "<:blueshell:1222371607784198215> {a} dropped their cookie jar and {b} picked up **{n}** cookies!",
    "<:blueshell:1222371607784198215> {b} snuck past {a}'s security system and stole **{n}** cookies!",
    "<:blueshell:1222371607784198215> {b} successfully pickpocketed **{n}** cookies from {a}!",
    "<:blueshell:1222371607784198215> {a} was feeling extra generous and gave {b} **{n}** cookies!",
    "<:blueshell:1222371607784198215> {a} was feeling guilty for being in first place and gave {b} **{n}** cookies!",
    "<:blueshell:1222371607784198215> {a} will surely miss the **{n}** cookies that {b} just took!",
    "<:blueshell:1222371607784198215> Cookie monster say stealing cookie is wrong. {b}, apologize to {a} for taking **{n}** cookies!",
    "<:blueshell:1222371607784198215> {a} gave away **{n}** cookies! {b} was very persuasive.",
]
SWINDLE_BACKFIRE_QUOTES = [
    "<:blueshell:1222371607784198215> {a} tried to swindle from themselves and lost **{n}** cookies! Luckily, {b} was there to pick them up.",
    "<:blueshell:1222371607784198215> {a} used **swindle**! It hurt itself in its confusion! {b} gained **{n}** cookies.",
    "<:blueshell:1222371607784198215> {a} hit themselves with a blue shell and gave **{n}** cookies to {b}!",
]
