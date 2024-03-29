import random
from datetime import datetime
from fractions import Fraction
from io import BytesIO

import discord as d
from discord.ext import tasks

from config import *
from database import Database
from upgrades import ClickUpgrade, PassiveUpgrade, SwindleUpgrade, Upgrade
from util import *

# --- Bot --- #

log = logging.getLogger('bot')
log.setLevel(LOG_LEVEL)
dt_fmt = '%Y-%m-%d %H:%M:%S'
log_handler = logging.FileHandler(filename='data/bot.log', encoding='utf-8', mode='w')
log_handler.setFormatter(logging.Formatter('[{asctime}] [{levelname:<8}] {name}: {message}', dt_fmt, style='{'))
log.addHandler(log_handler)

class CookieBot(d.Client):
    def __init__(self):
        self.db = Database('data/db.json')

        f = 60 # price scale factor
        shell = '<:blueshell:1222371607784198215>'
        self.upgrades: list[Upgrade] = [
            ClickUpgrade  ('👍', 'Facebook Like Button',         exp(100, 8),            exp(2*100, 8)),
            ClickUpgrade  ('🧗‍♀️', 'Girl Scouts Ad Campaign',      exp(10**6, 6000),       exp(2*10**6, 6000)),
            PassiveUpgrade('👨‍🍳', 'Chef Freako',                  exp(1, 1.75),           cap(exp(f*1, 1.75), 25)),
            PassiveUpgrade('🔥', 'Oven Eat the Food',            exp(50, 2),             cap(exp(f*50, 2), 25)),
            PassiveUpgrade('🎤', 'Astley Automator',             exp(5000, 8),           cap(exp(f*5000, 8), 25)),
            PassiveUpgrade('🛠️', 'Home Depot Bakery',            exp(150000, 75),        cap(exp(f*150000, 75), 25)),
            PassiveUpgrade('🏰', 'Crypto Cookie Castle',         exp(500*10**6, 1500),   cap(exp(f*500*10**6, 1500), 25)),
            PassiveUpgrade('🏗️', 'Cookie Construction Company',  exp(25*10**12, 250000), cap(exp(f*25*10**12, 250000), 25)),
            PassiveUpgrade('🐢', 'Blurbot ver.1.22474487139...', lambda l: l+2 if l < 10 else -10**96, lambda _: 69*10**68, hide=True),
            SwindleUpgrade(shell, 'Blue Shell',                  lin(0.05, 0.025),       cap(exp(10**6, 10**5), 15), hide=True)
        ]

        intents = d.Intents.default()
        # intents.message_content = True
        intents.members = True

        super().__init__(intents=intents)
        self.tree = d.app_commands.CommandTree(self)
        self.prev_cookie_count = 0
        self.prev_cooldown_remaining = 0

    async def on_ready(self):
        log.info(f'Logged in as {self.user}!')
        activity = d.Activity(type=d.ActivityType.watching, name='the oven')
        await self.change_presence(activity=activity)
        await self.init_clicker_message()

    async def setup_hook(self):
        # Sync slash commands
        self.tree.copy_global_to(guild=GUILD)
        await self.tree.sync(guild=GUILD)
        if GUILD != DEV_GUILD:
            await self.tree.sync(guild=DEV_GUILD)
        log.debug('Commands synced.')

        # Add persistent views
        async with self.db:
            clicker_msg_id = self.db.get_clicker_message_id()
            self.add_view(CookieClicker(), message_id=clicker_msg_id)
            log.info(f'Added persistent clicker view for message {clicker_msg_id}')

        # Start cookie updater task
        self.cookie_updater.start()

    async def set_clicker_message(self, msg: d.Message):
        async with self.db:
            self.db.set_clicker_message_id(msg.id)
            self.db.set_clicker_channel_id(msg.channel.id)

            self.message = msg
            if not self.clicker_message_updater.is_running():
                self.clicker_message_updater.start()

            log.info(f'Updated cookie message to {msg.id}')

    async def init_clicker_message(self):
        async with self.db:
            channel_id = self.db.get_clicker_channel_id()
            msg_id = self.db.get_clicker_message_id()

        if msg_id is not None:
            try:
                channel = bot.get_channel(channel_id)
                self.message = await channel.fetch_message(msg_id)
                self.clicker_message_updater.start()
                log.info(f'Initialized cookie message {msg_id}')
            except d.NotFound:
                log.warning('Clicker message was deleted!')
                async with bot.db:
                    bot.db.set_clicker_message_id(None)
                    bot.db.set_clicker_channel_id(None)

    @tasks.loop(seconds=COOKIE_UPDATE_RATE)
    async def cookie_updater(self):
        """ Updates the database cookie count. Does not use discord api. """
        async with self.db:
            for user_id in self.db.get_participants_user_ids():
                cps = self.db.get_cookies_per_second(self.upgrades, user_id)
                self.db.add_cookies(user_id, cps * COOKIE_UPDATE_RATE)

    @cookie_updater.before_loop
    async def before_cookie_updater(self):
        log.debug(f'Cookie updater started. ({COOKIE_UPDATE_RATE}s)')

    @cookie_updater.after_loop
    async def after_cookie_updater(self):
        log.debug('Cookie updater stopped.')

    @tasks.loop(seconds=DISCORD_UPDATE_RATE)
    async def clicker_message_updater(self):
        log.debug('Updating clicker')
        msg = await make_clicker_message()
        if msg is not None:
            try:
                await self.message.edit(**msg)
            except d.NotFound:
                log.warning('Clicker message was deleted!')
                self.clicker_message_updater.stop()
                self.message = None
                async with bot.db:
                    bot.db.set_clicker_channel_id(None)
                    bot.db.set_clicker_message_id(None)

    @clicker_message_updater.before_loop
    async def before_cookie_updater(self):
        await self.wait_until_ready()
        log.debug(f'Clicker message updater started. ({DISCORD_UPDATE_RATE}s)')

    @clicker_message_updater.after_loop
    async def after_cookie_updater(self):
        log.debug('Clicker message updater stopped.')

bot = CookieBot()

# --- Views --- #

class CookieClicker(d.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.button = self.children[0]

    @d.ui.button(label='Cookie!', style=d.ButtonStyle.blurple, emoji='🍪', custom_id='cookie-btn')
    @catch_errors
    async def click(self, interaction: d.Interaction, button: d.ui.Button):
        user = interaction.user
        async with bot.db:
            # Check clicker message ID (if someone clicks an old clicker message, just ignore it)
            clicker_message_id = bot.db.get_clicker_message_id()
            if clicker_message_id != interaction.message.id:
                return

            # Check cooldown
            cooldown = bot.db.get_cooldown_remaining(COOKIE_COOLDOWN)
            if cooldown > 0:
                log.warning(f'{user.name} tried to click but {cooldown}s left on cooldown')
                raise Break()

            # Give cookies
            clicker_user_id = user.id
            base_num = random.randint(*COOKIE_RANGE)
            num = base_num + bot.db.get_cookies_per_click(bot.upgrades, clicker_user_id)
            bot.db.add_cookies(clicker_user_id, num)
            bot.db.set_last_clicked_time()
            bot.db.set_last_clicked_user_id(clicker_user_id)
            bot.db.set_last_clicked_value(num)
            log.info(f'Click! {user.name} got {num} cookies')

            # Swindling
            swindle = random.random() < bot.db.get_swindle_probability(bot.upgrades, clicker_user_id)
            if swindle:
                ranks = bot.db.get_ranks(bot.upgrades)
                first_cookies, _, first_user_id = ranks[0]

                if clicker_user_id == first_user_id:
                    # Clicker is first. Choose another random swindler
                    num_swindled = int(first_cookies * Fraction(SWINDLE_BACKFIRE_AMOUNT))
                    participants = bot.db.get_participants_user_ids()
                    swindler_user_id = first_user_id
                    while swindler_user_id == first_user_id:
                        swindler_user_id = random.choice(participants)
                else:
                    # Clicker steals from first
                    swindler_user_id = clicker_user_id
                    num_swindled = int(first_cookies * Fraction(SWINDLE_AMOUNT))

                bot.db.add_cookies(first_user_id, -num_swindled)
                bot.db.add_cookies(swindler_user_id, num_swindled)

        # Build and send response
        if cooldown > 0:
            await interaction.response.send_message(
                f"All out of cookies! Me bake more cookie in {time_str(cooldown)}",
                ephemeral=True
            )
            return

        # Disable button and force leaderboard update
        button.disabled = True
        bot.clicker_message_updater.restart()

        # Make cookie quote
        quote = random.choice(COOKIE_QUOTES)
        msg = f'{quote}\nYou got 🍪 **{bignum(num)}** cookies! Om nom nom nom'
        await interaction.response.send_message(msg, ephemeral=True)

        # Build and send swindling message
        if swindle:
            if swindler_user_id == clicker_user_id:
                swindle_quote = random.choice(SWINDLE_QUOTES)
            else:
                # Backfired
                swindle_quote = random.choice(SWINDLE_BACKFIRE_QUOTES)

            # Fill in message template
            swindled_user = bot.get_user(first_user_id)
            swindler_user = bot.get_user(swindler_user_id)
            swindle_msg = swindle_quote \
                .replace('{a}', swindled_user.mention) \
                .replace('{b}', swindler_user.mention) \
                .replace('{n}', bignum(num_swindled))

            # Send
            await interaction.channel.send(swindle_msg)

    @d.ui.button(label='My upgrades', style=d.ButtonStyle.gray, emoji='⬆️', custom_id='upgrades-btn')
    @catch_errors
    async def upgrades(self, interaction: d.Interaction, button: d.ui.Button):
        user = interaction.user
        await interaction.response.send_message(**await make_upgrades_message(user))
        message: d.Message = await interaction.original_response()
        async with bot.db:
            bot.db.set_upgrade_message_owner_id(message.id, user.id)

    @d.ui.button(label='My progress', style=d.ButtonStyle.gray, emoji='📈', custom_id='progress-btn')
    @catch_errors
    async def progress(self, interaction: d.Interaction, button: d.ui.Button):
        user = interaction.user
        msg = await make_progess_message(user)
        await interaction.response.send_message(f"{user.mention} {msg['content']}")

class Shop(d.ui.View):
    def __init__(self, purchase_options: list[d.SelectOption]):
        super().__init__(timeout=None)
        self.add_item(UpgradeSelect(purchase_options))

    @d.ui.button(label='Refresh', style=d.ButtonStyle.gray, emoji='🔄', row=1)
    async def refresh(self, interaction: d.Interaction, button: d.ui.Button):
        async with bot.db:
            owner_id = bot.db.get_upgrade_message_owner_id(interaction.message.id)
        if owner_id == interaction.user.id:
            msg = await make_upgrades_message(interaction.user)
            await interaction.message.edit(**msg)
        await interaction.response.defer()

class UpgradeSelect(d.ui.Select):
    def __init__(self, options: list[d.SelectOption]):
        super().__init__(
            custom_id='upgrade-select',
            placeholder='Buy an upgrade...',
            options=options,
            row=0
        )

    @catch_errors
    async def callback(self, interaction: d.Interaction):
        async with bot.db:
            user_id = bot.db.get_upgrade_message_owner_id(interaction.message.id)

            # If the message isn't saved, just don't respond
            if user_id is None:
                return

            # Check that this user owns the message
            if user_id != interaction.user.id:
                raise Break()

            upgrade_id = int(self.values[0])
            upgrade = bot.upgrades[upgrade_id]
            level = bot.db.get_upgrade_level(user_id, upgrade_id) + 1
            price = upgrade.get_price(level)
            balance = bot.db.get_cookies(user_id)

            # Level up!
            if balance >= price:
                bot.db.set_upgrade_level(bot.upgrades, user_id, upgrade_id, level)
                bot.db.add_cookies(user_id, -price)

        # Build and send response
        if user_id != interaction.user.id:
            # wrong owner
            owner_user = bot.get_user(user_id)
            await interaction.response.send_message(
                f"Hey those upgrades are for **{owner_user.display_name}**! It not nice to take other people's cookies.",
                ephemeral=True
            )
            return

        if balance < price:
            # can't afford
            await interaction.response.send_message(
                "Hey!! You no have enough cookie for that!",
                ephemeral=True
            )
        else:
            # success
            await interaction.response.send_message(
                f'Purchased **{upgrade.name} {roman(level)}**!\nThank for the cookies!! nom nom nom',
                ephemeral=True
            )

        # Edit original message (to remove selected option)
        msg = await make_upgrades_message(interaction.user)
        await interaction.message.edit(**msg)

    @staticmethod
    def get_options(upgrade_levels: list[int]) -> list[d.SelectOption]:
        options = []
        for upgrade, level in zip(bot.upgrades, upgrade_levels):
            price = bignum(upgrade.get_price(level + 1))
            value = upgrade.get_value_str(level + 1, hide=True)

            options.append(d.SelectOption(
                label=f'{upgrade.id + 1}. {upgrade.name} {roman(level + 1)}',
                description=f'🍪 {price} ⬆️ {value}',
                emoji=upgrade.emoji,
                value=upgrade.id
            ))

        return options


# --- Complex message makers --- #

async def make_clicker_message(allow_skip=True) -> dict | None:
    async with bot.db:
        total_cookies = bot.db.get_total_cookies()
        cooldown = bot.db.get_cooldown_remaining(COOKIE_COOLDOWN)

        if allow_skip:
            # Don't update the message if nothing has changed (cookie count is the
            # same AND the cooldown did not expire)
            if total_cookies == bot.prev_cookie_count and cooldown == bot.prev_cooldown_remaining:
                log.debug('Skipping update')
                return None

        # Update prev counts
        bot.prev_cookie_count = total_cookies
        bot.prev_cooldown_remaining = cooldown

        # Last clicked
        last_clicked_user_id = bot.db.get_last_clicked_user_id()
        last_clicked_value = bot.db.get_last_clicked_value()
        last_clicked_time = bot.db.get_last_clicked_time()

        # Leaderboard
        participants = bot.db.get_participants_user_ids()
        ranks = bot.db.get_ranks(bot.upgrades)

    # Total cookie count display
    content = f'# 🍪 {bignum(total_cookies)}'

    # Last clicked
    if last_clicked_user_id is not None:
        last_clicked_user = bot.get_user(last_clicked_user_id)
        last_clicked_ago = int((datetime.utcnow() - last_clicked_time).total_seconds())
        content += f'\n👆 **+{bignum(last_clicked_value)}** - {last_clicked_user.display_name} {time_str(last_clicked_ago)} ago'

    # View and cookie button
    view = CookieClicker()
    if cooldown > 0:
        view.button.disabled = True
        view.button.label = f'{time_str(cooldown)} ...'

    # Leaderboard embed
    if len(participants) == 0:
        embed = None
    else:
        embed = d.Embed(color=d.Color.blue())
        embed.set_footer(text=f'updates every {time_str(DISCORD_UPDATE_RATE)}')
        for i, (cookies, cps, user_id) in enumerate(ranks[:25], 1):
            name = bot.get_user(user_id).display_name
            if i == 1:
                name = '🥇 ' + name
            elif i == 2:
                name = '🥈 ' + name
            elif i == 3:
                name = '🥉 ' + name
            else:
                name = f'{i}. {name}'
            embed.add_field(name=name, value=f'🍪 {bignum(cookies)}\n+{bignum(cps)} / sec', inline=True)

    return dict(
        content=content,
        view=view,
        embed=embed
    )

async def make_upgrades_message(user: d.User | d.Member) -> dict:
    user_id = user.id
    async with bot.db:
        balance = bot.db.get_cookies(user_id)
        cpc = bot.db.get_cookies_per_click(bot.upgrades, user_id)
        cps = bot.db.get_cookies_per_second(bot.upgrades, user_id)
        levels = bot.db.get_upgrade_levels(bot.upgrades, user_id)

    # Cookie balance
    content = f'## 🍪 {bignum(balance)}\n{user.mention}'

    # Upgrades embed
    embed = d.Embed(color=d.Color.blue())
    embed.title = f"{user.display_name}'s upgrades"

    # CPC/CPS totals
    embed.description = f'**👆 +{bignum(cpc)} / click**\n**🕙 +{bignum(cps)} / sec**'

    # Individual upgrades
    for upgrade in bot.upgrades:
        level = levels[upgrade.id]
        name = f'{upgrade.id + 1}. {upgrade.emoji} {upgrade.name} {roman(level)}'
        desc = upgrade.get_description(level)
        price = bignum(upgrade.get_price(level + 1))

        embed.add_field(
            name=name,
            value=f'{desc}\nCost: 🍪 {price}',
            inline=True
        )

    # Upgrade selector view
    view = Shop(UpgradeSelect.get_options(levels))

    return dict(
        content=content,
        embed=embed,
        view=view
    )

async def make_progess_message(user: d.User) -> dict:
    async with bot.db:
        cookies = bot.db.get_cookies(user.id)
        cps = bot.db.get_cookies_per_second(bot.upgrades, user.id)
        ranks = bot.db.get_ranks(bot.upgrades)

    # Time to reach 1 googol
    if cookies > 10 ** 100:
        # 1 Googol reached!
        msg = 'SO MANY COOKIES!!!! Remember cookie taste better when shared with friends!'
    elif cps < 0:
        # Oh no
        msg = 'Oh no... you losing cookie fast. I give some if you click button, maybe will help?'
    elif cps == 0:
        # Infinity time left
        msg = "You're not making any cookies! Click button and buy upgrades to make cookie faster!"
    else:
        seconds = (10 ** 100 - cookies) // cps
        msg = f"At current cookie rate, you will reach **🍪 1 googol** in **{time_str(seconds)}**!"
        if seconds < 60 * 60:
            # Less than 1 hour left
            msg += ' So many cookie so fast!! Almost there, keep going!!'
        elif seconds < 60 * 60 * 24:
            # Less than 1 day left
            msg += ' Be patient!'
        elif seconds < 60 * 60 * 24 * 7:
            # Less than 1 week left
            msg += " You making cookies so fast and still so long? Me think more upgrades!"
        else:
            # More than 1 week left
            msg += (' Too long... Me no want to wait that long, you that patient? '
                    'You should make cookie faster!')

    # Find this user's rank
    msg += '\n\n'
    for i, (_, _, user_id) in enumerate(ranks):
        if user_id == user.id:
            break
    else:
        i = -1

    if i == -1:
        # Not participating
        msg += "Make some cookies to get on the leaderboard!"
    elif i == 0:
        # First place
        msg += "🏆 You're in first place! Me and everyone else very proud of you."
    else:
        # Time to overtake the next player
        cookies2, cps2, user_id2 = ranks[i - 1]
        user2 = bot.get_user(user_id2)
        cookie_diff = cookies2 - cookies + 1
        msg += (f"You're in **{i + 1}{num_suffix(i + 1)}** place! You need **🍪 {bignum(cookie_diff)}** "
                f"to overtake **{user2.display_name}** for {i}{num_suffix(i)} place!")
        if cps > 0:
            seconds = cookie_diff // cps
            msg += f" At **+{bignum(cps)} / sec**, it'll take only **{time_str(seconds)}** to get that many cookies!"
        msg += " Keep going!"

    return dict(content=msg)


# --- Commands --- #

@bot.tree.command()
@catch_errors
async def hello(interaction: d.Interaction):
    """ wake up babe its time for another april fools bot """
    await interaction.response.send_message(f'Hellooo {interaction.user.mention}', ephemeral=True)

@bot.tree.command()
@catch_errors
async def jar(interaction: d.Interaction):
    """ how many cookies in your jar """
    async with bot.db:
        cookies = bot.db.get_cookies(interaction.user.id)

    if cookies < 0:
        msg = f"{interaction.user.mention} YOU OWE ME COOKIE! GIVE OR ill be sad >:("
    elif cookies == 0:
        msg = f"{interaction.user.mention} no have any cookie!"
    elif cookies < 1000:
        msg = f"{interaction.user.mention} has **🍪 {cookies:,}** cookies! not many cookie but better than no cookie!!"
    else:
        msg = f"{interaction.user.mention} has **🍪 {cookies:,}** cookies!! So many! om nom nom nom"
    await interaction.response.send_message(msg)

@bot.tree.command()
@catch_errors
async def upgrades(interaction: d.Interaction):
    """ view & purchase upgrades """
    user = interaction.user
    await interaction.response.send_message(**await make_upgrades_message(user))
    message: d.Message = await interaction.original_response()
    async with bot.db:
        bot.db.set_upgrade_message_owner_id(message.id, user.id)

@bot.tree.command()
@catch_errors
async def progress(interaction: d.Interaction):
    """ your cookie progress """
    msg = await make_progess_message(interaction.user)
    await interaction.response.send_message(**msg)


# --- Dev commands --- #

@bot.tree.command()
@catch_errors
async def clicker(interaction: d.Interaction, channel_id: str):
    """ [Dev] send a new clicker message to the given channel ID. Old clicker messages will stop being updated """
    try:
        channel_id = int(channel_id)
        channel = bot.get_channel(channel_id)
    except ValueError:
        channel = None

    if channel is None:
        interaction.response.send_message(f'channel id not found: {channel_id}')
        return

    msg_data = await make_clicker_message(allow_skip=False)
    msg: d.Message = await channel.send(**msg_data)
    await bot.set_clicker_message(msg)
    await interaction.response.send_message(f'New clicker message sent in #{channel}')

@bot.tree.command(guild=DEV_GUILD)
@catch_errors
async def set_cookies(interaction: d.Interaction, user: d.Member, cookies: str):
    """ [Dev] set cookies for a given user """
    cookies = int(cookies)
    async with bot.db:
        bot.db.set_cookies(user.id, cookies)
    await interaction.response.send_message(f'set {user} cookies to {cookies}')

@bot.tree.command(guild=DEV_GUILD)
@catch_errors
async def give_upgrade(interaction: d.Interaction, user: d.Member, upgrade_id: int, level: int | None):
    """ [Dev] set the upgrade level for a given user. If level is not given, increase by 1 """
    if upgrade_id < 0 or upgrade_id >= len(bot.upgrades):
        await interaction.response.send_message('invalid upgrade id')
        return

    async with bot.db:
        if level is None:
            level = bot.db.get_upgrade_level(user.id, upgrade_id) + 1
        level = max(level, 0)
        bot.db.set_upgrade_level(bot.upgrades, user.id, upgrade_id, level)

    upgrade = bot.upgrades[upgrade_id]
    await interaction.response.send_message(f'set {upgrade_id} ({upgrade.name}) for {user} to lv.{level}')

@bot.tree.command(guild=DEV_GUILD)
@catch_errors
async def reset(interaction: d.Interaction, user: d.Member | None = None):
    """ [Dev] reset all data for a given user, or everyone if a user is not provided """
    async with bot.db:
        user_ids = [user.id] if user else bot.db.get_participants_user_ids()
        for user_id in user_ids:
            bot.db.delete_participant(user_id)
        bot.db.set_last_clicked_user_id(None)
        bot.db.set_last_clicked_value(0)
    await interaction.response.send_message(f"reset {user or 'everyone'}")

@bot.tree.command(guild=DEV_GUILD)
@catch_errors
async def clear_upgrade_message_storage(interaction: d.Interaction):
    """ [Dev] clears all associations between upgrade messages and their owners """
    async with bot.db:
        bot.db.clear_upgrade_message_owner_ids()
    await interaction.response.send_message('upgrade message owners deleted')

@bot.tree.command(guild=DEV_GUILD)
@catch_errors
async def clear_cached_cpc_cps(interaction: d.Interaction):
    """ [Dev] clear cpc & cps cache. Only necessary if upgrade config changes """
    async with bot.db:
        bot.db.clear_cpc_cps_caches()
    await interaction.response.send_message('cpc & cps cache cleared')

@bot.tree.command(guild=DEV_GUILD)
@catch_errors
async def print_db(interaction: d.Interaction):
    """ [Dev] print the entire database """
    async with bot.db:
        j = bot.db.get_json()
    if len(j) > 1990:
        file = BytesIO()
        file.write(j.encode('utf-8'))
        file.seek(0)
        fn = f'db_{datetime.utcnow().isoformat()}.json'
        await interaction.response.send_message(file=d.File(file, filename=fn))
    else:
        await interaction.response.send_message(f"```\n{j}\n```")

@bot.tree.command(guild=DEV_GUILD)
@catch_errors
async def kill(interaction: d.Interaction):
    """ [Dev] kill the bot """
    await interaction.response.send_message('killing...')
    await bot.close()


if __name__ == '__main__':
    with open('client_secret.txt') as file:
        token = file.read().strip()
    bot.run(token, log_handler=log_handler)
