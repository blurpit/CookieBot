from upgrades import ClickUpgrade, PassiveUpgrade, Upgrade

GUILD_ID = 913924123405729812
UPDATE_RATE = 10
COOKIE_COOLDOWN = 60
COOKIE_RANGE = (1, 1)
BIGNUM_PLACES = 3

UPGRADES: list[Upgrade] = [
    ClickUpgrade  ('👍', 'Facebook Like Button',        1,    100),
    PassiveUpgrade('👨‍🍳', 'Chef Freako',                 1,    100),
    PassiveUpgrade('🔥', 'Oven Eat the Food',           5,    1000),
    PassiveUpgrade('🎤', 'Astley Automator',            50,   10000),
    PassiveUpgrade('🛠️', 'Home Depot Bakery',           300,  50000),
    PassiveUpgrade('🏰', 'Crypto Cookie Castle',        1500, 200000),
    PassiveUpgrade('🏗️', 'Cookie Construction Company', 5000, 500000),
    PassiveUpgrade('🐢', 'Blurbot v3.0',                3,    1000001),
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
