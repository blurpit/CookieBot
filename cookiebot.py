import random

import discord as d
from discord.ext import tasks

from config import *
from database import Database
from util import *


# --- Bot --- #

class CookieBot(d.Client):
    def __init__(self):
        self.db = Database('data/db.json')

        intents = d.Intents.default()
        # intents.message_content = True
        intents.members = True

        super().__init__(intents=intents)
        self.tree = d.app_commands.CommandTree(self)
        self.prev_cookie_count = 0
        self.prev_cooldown_remaining = 0

    async def on_ready(self):
        print(f'Logged in as {self.user}!')
        activity = d.Activity(type=d.ActivityType.watching, name='the oven')
        await self.change_presence(activity=activity)
        await self.init_clicker_message()

    async def setup_hook(self):
        # Sync slash commands
        self.tree.copy_global_to(guild=GUILD)
        await self.tree.sync(guild=GUILD)
        await self.tree.sync(guild=DEV_GUILD)
        print('Commands synced.')

        # Add persistent views
        async with self.db:
            clicker_msg_id = self.db.get_clicker_message_id()
            self.add_view(CookieClicker(), message_id=clicker_msg_id)
            print(f'Added persistent clicker view for message {clicker_msg_id}')

        # Start cookie updater task
        self.cookie_updater.start()

    async def set_clicker_message(self, msg: d.Message):
        async with self.db:
            self.db.set_clicker_message_id(msg.id)
            self.db.set_clicker_channel_id(msg.channel.id)

            self.message = msg
            if not self.clicker_message_updater.is_running():
                self.clicker_message_updater.start()

            print(f'Updated cookie message to {msg.id}')

    async def init_clicker_message(self):
        async with self.db:
            channel_id = self.db.get_clicker_channel_id()
            msg_id = self.db.get_clicker_message_id()

        if msg_id is not None:
            try:
                channel = bot.get_channel(channel_id)
                self.message = await channel.fetch_message(msg_id)
                self.clicker_message_updater.start()
                print(f'Initialized cookie message {msg_id}')
            except d.NotFound:
                print('Clicker message was deleted!')
                async with bot.db:
                    bot.db.set_clicker_message_id(None)
                    bot.db.set_clicker_channel_id(None)

    @tasks.loop(seconds=1)
    async def cookie_updater(self):
        """ Updates the database cookie count. Does not use discord api. """
        async with self.db:
            for user_id in self.db.get_participants_user_ids():
                cps = self.db.get_cookies_per_second(user_id)
                self.db.add_cookies(user_id, cps)

    @cookie_updater.before_loop
    async def before_cookie_updater(self):
        print('Cookie updater started.')

    @cookie_updater.after_loop
    async def after_cookie_updater(self):
        print('Cookie updater stopped.')

    @tasks.loop(seconds=UPDATE_RATE)
    async def clicker_message_updater(self):
        print('Updating clicker')
        msg = await make_clicker_message()
        if msg is not None:
            try:
                await self.message.edit(**msg)
            except d.NotFound:
                print('Clicker message was deleted!')
                self.clicker_message_updater.stop()
                self.message = None
                async with bot.db:
                    bot.db.set_clicker_channel_id(None)
                    bot.db.set_clicker_message_id(None)

    @clicker_message_updater.before_loop
    async def before_cookie_updater(self):
        await self.wait_until_ready()
        print('Clicker message updater started.')

    @clicker_message_updater.after_loop
    async def after_cookie_updater(self):
        print('Clicker message updater stopped.')

bot = CookieBot()

# --- Views --- #

class CookieClicker(d.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.button = self.children[0]

    @d.ui.button(label='Cookie!', style=d.ButtonStyle.blurple, emoji='<:emoji3:1218668546544894053>', custom_id='cookie-btn')
    async def click(self, interaction: d.Interaction, button: d.ui.Button):
        async with bot.db:
            cooldown = bot.db.get_cooldown_remaining(COOKIE_COOLDOWN)
            if cooldown > 0:
                msg = f"All out of cookies! Me bake more cookie in {time_str(cooldown)}!"
                ephemeral = True
                print(f'{interaction.user.name} tried to click but {cooldown}s is left on cooldown')
            else:
                user_id = interaction.user.id
                quote = random.choice(COOKIE_QUOTES)
                base_num = random.randint(*COOKIE_RANGE)

                num = base_num + bot.db.get_cookies_per_click(user_id)
                bot.db.add_cookies(user_id, num)
                bot.db.set_last_clicked_time()
                bot.db.set_last_clicked_user_id(user_id)
                bot.db.set_last_clicked_value(num)
                print(f'Click! {interaction.user.name} got {num} cookies')

                msg = f'{quote}\nYou got **{bignum(num)}** cookies! Om nom nom nom'
                ephemeral = True

        button.disabled = True
        bot.clicker_message_updater.restart() # force update after button press
        await interaction.response.send_message(msg, ephemeral=ephemeral)

    @d.ui.button(label='My upgrades', style=d.ButtonStyle.gray, emoji='⬆️', custom_id='upgrades-btn')
    async def upgrades(self, interaction: d.Interaction, button: d.ui.Button):
        user = interaction.user
        await interaction.response.send_message(**await make_upgrades_message(user))
        message: d.Message = await interaction.original_response()
        async with bot.db:
            bot.db.set_upgrade_message_owner_id(message.id, user.id)

    @d.ui.button(label='My progress', style=d.ButtonStyle.gray, emoji='📈', custom_id='progress-btn')
    async def progress(self, interaction: d.Interaction, button: d.ui.Button):
        user = interaction.user
        msg = await make_progess_message(user)
        await interaction.response.send_message(f"{user.mention} {msg['content']}")

class Shop(d.ui.View):
    def __init__(self, purchase_options):
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

    async def callback(self, interaction: d.Interaction):
        async with bot.db:
            owner_id = bot.db.get_upgrade_message_owner_id(interaction.message.id)
            if owner_id is None:
                return # Message isn't saved, just don't respond.
            user = bot.get_user(owner_id)

            # Check that this user owns the message
            if owner_id != interaction.user.id:
                fail = 'wrong_user'
                msg = None
            else:
                upgrade = UPGRADES[int(self.values[0])]
                level = bot.db.get_upgrade_level(user.id, upgrade.id) + 1
                price = upgrade.get_price(level)
                balance = bot.db.get_cookies(user.id)

                # Check that the user has enough cookies
                if balance < price:
                    fail = 'cant_afford'
                else:
                    bot.db.set_upgrade_level(user.id, upgrade.id, level)
                    bot.db.add_cookies(user.id, -price)
                    print(f'Purchased {upgrade.name} lv. {level}')
                    fail = None
                msg = await make_upgrades_message(user)

        if fail == 'wrong_user':
            await interaction.response.send_message(
                f"Hey those upgrades are for **{user.display_name}**! It not nice to take other people's cookies.",
                ephemeral=True
            )
        elif fail == 'cant_afford':
            await interaction.response.send_message(
                "Hey!! You no have enough cookie for that!",
                ephemeral=True
            )
        else:
            await interaction.response.send_message(
                f'Purchased **{upgrade.name} {roman(level)}**!\nThank for the cookies!! nom nom nom',
                ephemeral=True
            )
        if msg is not None:
            await interaction.message.edit(**msg)

    @staticmethod
    async def get_options(user_id: int) -> list[d.SelectOption]:
        async with bot.db:
            options = []
            for upgrade, level in zip(UPGRADES, bot.db.get_upgrade_levels(user_id)):
                price = upgrade.get_price(level + 1)
                num = upgrade.get_cookies_per_unit(level + 1)
                if upgrade.hide and not bot.db.does_someone_own(upgrade.id):
                    num = '???'

                options.append(d.SelectOption(
                    label=f'{upgrade.id + 1}. {upgrade.name} {roman(level + 1)}',
                    description=f'🍪 {bignum(price)} ⬆️ +{bignum(num)} / {upgrade.unit}',
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
                print('Skipping update')
                return None

        # Update prev counts
        bot.prev_cookie_count = total_cookies
        bot.prev_cooldown_remaining = cooldown

        # Total cookie count display
        content = f'# 🍪 {bignum(total_cookies)}'

        # Last clicked
        last_clicked_user_id = bot.db.get_last_clicked_user_id()
        if last_clicked_user_id is not None:
            user = bot.get_user(last_clicked_user_id)
            value = bot.db.get_last_clicked_value()
            content += f'\n👆 **+{bignum(value)}** {user.display_name}'

        # View and cookie button
        view = CookieClicker()
        if cooldown > 0:
            view.button.disabled = True
            view.button.label = f'{time_str(cooldown)} ...'

        # Leaderboard embed
        if len(bot.db.get_participants_user_ids()) == 0:
            embed = None
        else:
            embed = d.Embed(color=d.Color.blue())
            embed.set_footer(text=f'updates every {time_str(UPDATE_RATE)}')

            entries = []
            for user_id in bot.db.get_participants_user_ids():
                user = bot.get_user(user_id)
                cookies = bot.db.get_cookies(user_id)
                entries.append((cookies, user.display_name))
            entries.sort(reverse=True)

            for i, (cookies, name) in enumerate(entries[:25], 1):
                if i == 1:
                    name = '🥇 ' + name
                elif i == 2:
                    name = '🥈 ' + name
                elif i == 3:
                    name = '🥉 ' + name
                else:
                    name = f'{i}. {name}'
                embed.add_field(name=name, value=f'🍪 {bignum(cookies)}', inline=True)

        return dict(
            content=content,
            view=view,
            embed=embed
        )

async def make_upgrades_message(user: d.User | d.Member) -> dict:
    async with bot.db:
        balance = bot.db.get_cookies(user.id)
        content = f'## 🍪 {bignum(balance)}'

        embed = d.Embed(color=d.Color.blue())
        embed.title = f"{user.display_name}'s upgrades"

        cps = bot.db.get_cookies_per_second(user.id)
        cpc = bot.db.get_cookies_per_click(user.id)
        levels = bot.db.get_upgrade_levels(user.id)
        embed.description = f'**👆 +{bignum(cpc)} / click**\n**🕙 +{bignum(cps)} / sec**'

        for upgrade in UPGRADES:
            level = levels[upgrade.id]
            name = f'{upgrade.id + 1}. {upgrade.emoji} {upgrade.name} {roman(level)}'
            price = upgrade.get_price(level + 1)
            num = upgrade.get_cookies_per_unit(level)
            if upgrade.hide and not bot.db.does_someone_own(upgrade.id):
                num = '???'

            if level > 0:
                value = (f'**+{bignum(num)} / {upgrade.unit}**\n'
                         f'Cost: 🍪 {bignum(price)}')
            else:
                value = (f'Not purchased yet!\n'
                         f'Cost: 🍪 {bignum(price)}')

            embed.add_field(name=name, value=value, inline=True)

        view = Shop(await UpgradeSelect.get_options(user.id))

        return dict(
            content=content,
            embed=embed,
            view=view
        )

async def make_progess_message(user: d.User) -> dict:
    async with bot.db:
        cps = bot.db.get_cookies_per_second(user.id)
        cookies = bot.db.get_cookies(user.id)
        ranks = [
            (bot.db.get_cookies(user_id), user_id)
            for user_id in bot.db.get_participants_user_ids()
        ]

    # Time to reach 1 googol
    if cookies > 10 ** 100:
        # 1 Googol reached!
        msg = 'SO MANY COOKIES!!!! Remember cookie taste better when shared with friends!'
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
            msg += (
                ' Too long... Me no want to wait that long, you that patient? '
                'You should make cookie faster!')

    # Time to overtake next place
    ranks.sort(reverse=True)
    msg += '\n\n'
    i = 0
    for i, (_, user_id) in enumerate(ranks):
        if user_id == user.id:
            break
    if i == 0:
        # First place
        msg += "🏆 You're in first place! Me and everyone else very proud of you."
    else:
        cookies2, user_id2 = ranks[i - 1]
        user2 = bot.get_user(user_id2)
        cookie_diff = cookies2 - cookies + 1
        msg += (
            f"You're in **{i + 1}{num_suffix(i + 1)}** place! You need **🍪 {bignum(cookie_diff)}** "
            f"to overtake **{user2.display_name}** for {i}{num_suffix(i)} place!")
        if cps > 0:
            seconds = cookie_diff // cps
            msg += (
                f" At current cookie rate, it'll take only **{time_str(seconds)}** to get "
                f"that many cookies!")
        msg += " Keep going!"

    return dict(content=msg)

# --- Commands --- #

@bot.tree.command()
async def hello(interaction: d.Interaction):
    """ wake up babe its time for another april fools bot """
    await interaction.response.send_message(f'Hellooo {interaction.user.mention}', ephemeral=True)

@bot.tree.command()
async def jar(interaction: d.Interaction):
    """ how many cookies in your jar """
    async with bot.db:
        cookies = bot.db.get_cookies(interaction.user.id)

    if cookies == 0:
        msg = f"{interaction.user.mention} no have any cookie!"
    elif cookies < 1000:
        msg = f"{interaction.user.mention} has **🍪 {cookies:,}** cookies! not many cookie but better than no cookie!!"
    else:
        msg = f"{interaction.user.mention} has **🍪 {cookies:,}** cookies!! So many! om nom nom nom"
    await interaction.response.send_message(msg)

@bot.tree.command()
async def progress(interaction: d.Interaction):
    """ your cookie progress """
    msg = await make_progess_message(interaction.user)
    await interaction.response.send_message(**msg)

# --- Dev commands --- #

@bot.tree.command()
async def start_clicker(interaction: d.Interaction, channel_id: int):
    """ [Dev] send a new clicker message to the given channel ID. Old clicker messages will stop being updated """
    channel = bot.get_channel(channel_id)
    msg_data = await make_clicker_message(allow_skip=False)
    msg: d.Message = await channel.send(**msg_data)
    await bot.set_clicker_message(msg)
    await interaction.response.send_message(f'new clicker message sent in {channel}')

@bot.tree.command(guild=DEV_GUILD)
async def set_cookies(interaction: d.Interaction, user: d.Member, cookies: int):
    """ [Dev] set cookies for a given user. """
    async with bot.db:
        bot.db.set_cookies(user.id, cookies)
    await interaction.response.send_message(f'set {user} cookies to {cookies}')

@bot.tree.command(guild=DEV_GUILD)
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
async def kill(interaction: d.Interaction):
    """ [Dev] kill the bot """
    await interaction.response.send_message('killing...')
    await bot.close()


if __name__ == '__main__':
    with open('client_secret.txt') as file:
        token = file.read().strip()
    bot.run(token)
