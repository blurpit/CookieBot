import random

import discord as d
from discord.ext import tasks

from config import *
from database import Database
from util import *


class CookieBot(d.Client):
    def __init__(self):
        self.db = Database('data/db.json')

        intents = d.Intents.default()
        # intents.message_content = True
        intents.members = True

        super().__init__(intents=intents)
        self.tree = d.app_commands.CommandTree(self)
        self.prev_cookie_count = -1

    async def on_ready(self):
        print(f'Logged in as {self.user}!')
        await self.init_clicker_message()

    async def setup_hook(self):
        guild = d.Object(id=GUILD_ID)
        self.tree.copy_global_to(guild=guild)
        await self.tree.sync(guild=guild)
        print('Commands synced.')

        async with self.db:
            clicker_msg_id = self.db.get_clicker_message_id()
            self.add_view(CookieClicker(), message_id=clicker_msg_id)
            print(f'Added persistent clicker view for message {clicker_msg_id}')

    async def set_clicker_message(self, msg: d.Message):
        async with self.db:
            self.db.set_clicker_message_id(msg.id)
            self.db.set_clicker_channel_id(msg.channel.id)

            self.message = msg
            if not self.cookie_updater.is_running():
                self.cookie_updater.start()

            print(f'Updated cookie message to {msg.id}')

    async def init_clicker_message(self):
        async with self.db:
            channel_id = self.db.get_clicker_channel_id()
            msg_id = self.db.get_clicker_message_id()
            if msg_id is not None:
                channel = bot.get_channel(channel_id)
                self.message = await channel.fetch_message(msg_id)
                self.cookie_updater.start()
                print(f'Initialized cookie message {msg_id}')

    @tasks.loop(seconds=UPDATE_RATE)
    async def cookie_updater(self):
        print('Updating clicker')
        msg = await  make_clicker_message()
        if msg is not None:
            await self.message.edit(**msg)

    @cookie_updater.before_loop
    async def before_cookie_updater(self):
        await self.wait_until_ready()
        print('Cookie updater started.')

    @cookie_updater.after_loop
    async def after_cookie_updater(self):
        print('Cookie updater stopped.')

bot = CookieBot()

class CookieClicker(d.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.button = self.children[0]

    @d.ui.button(label='Cookie!', style=d.ButtonStyle.grey, emoji='🍪', custom_id='cookie-btn')
    async def click(self, interaction: d.Interaction, button: d.ui.Button):
        async with bot.db:
            cooldown = bot.db.get_cooldown_remaining(COOKIE_COOLDOWN)
            if cooldown > 0:
                msg = f"All out of cookies! Me bake more cookie in {time_str(cooldown)}!"
                ephemeral = True
                print(f'{interaction.user.name} tried to click but {cooldown}s is left on cooldown')
            else:
                quote = random.choice(COOKIE_QUOTES)
                num = random.randint(*COOKIE_RANGE)

                user_id = interaction.user.id
                bot.db.add_clicked_cookies(user_id, num)
                bot.db.update_last_clicked()
                bot.db.set_last_clicked_user_id(user_id)
                bot.db.set_last_clicked_value(num)
                print(f'Click! {interaction.user.name} got {num} cookies')

                msg = f'{quote}\nYou got {num} cookie! Om nom nom nom'
                ephemeral = True

        button.disabled = True
        bot.cookie_updater.restart()
        await interaction.response.send_message(msg, ephemeral=ephemeral)

async def make_clicker_message() -> dict | None:
    async with bot.db:
        # Don't update the message if the cookie count hasn't changed
        total_cookies = bot.db.get_total_cookies()
        if total_cookies == bot.prev_cookie_count:
            print('Skipping update (cookie count has not changed)')
            return None
        bot.prev_cookie_count = total_cookies

        # Total cookie count display
        content = f'# 🍪 {total_cookies}'

        # Last clicked
        last_clicked_user_id = bot.db.get_last_clicked_user_id()
        if last_clicked_user_id is not None:
            user = bot.get_user(last_clicked_user_id)
            value = bot.db.get_last_clicked_value()
            content += f'\n👆 **+{value}** {user.display_name}'

        # View and cookie button
        view = CookieClicker()
        cooldown = bot.db.get_cooldown_remaining(COOKIE_COOLDOWN)
        if cooldown > 0:
            view.button.disabled = True
            view.button.label = f'{short_time_str(cooldown)} ...'

        # Leaderboard embed
        embed = d.Embed(color=d.Color.blue())
        embed.set_footer(text=f'updates every {short_time_str(UPDATE_RATE)}')

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
            embed.add_field(name=name, value=f'🍪 {cookies}', inline=True)

        return dict(
            content=content,
            view=view,
            embed=embed
        )


@bot.tree.command()
async def hello(interaction: d.Interaction):
    """ Wake up babe its time for another april fools bot """
    await interaction.response.send_message(f'Hi, {interaction.user.mention}')

@bot.tree.command()
async def cookie(interaction: d.Interaction):
    """ create cookie clicker message """
    bot.prev_cookie_count = -1 # force update
    await interaction.response.send_message(**await make_clicker_message())
    msg: d.Message = await interaction.original_response()
    await bot.set_clicker_message(msg)

@bot.tree.command()
async def jar(interaction: d.Interaction):
    """ how many cookies in your jar """
    async with bot.db:
        cookies = bot.db.get_clicked_cookies(interaction.user.id)

    if cookies == 0:
        msg = f"{interaction.user.mention} no have any cookie!"
    elif cookies < 500:
        msg = f"{interaction.user.mention} has {cookies} cookies! not many cookie but better than no cookie!!"
    else:
        msg = f"{interaction.user.mention} has {cookies} cookies!! So many! om nom nom nom"
    await interaction.response.send_message(msg)

@bot.tree.command()
async def upgrades(interaction: d.Interaction):
    """ your upgrades """
    user = interaction.user
    embed = d.Embed(color=d.Color.blue())
    embed.title = f"{user.display_name}'s upgrades"

    async with bot.db:
        cps = bot.db.get_cookies_per_second(user.id)
        cpc = bot.db.get_cookies_per_click(user.id)
        embed.description = f'**👆 +{cpc} / click**\n**🕙 +{cps} / sec**'

        for upgrade, n, purchased in bot.db.iter_upgrades(user.id):
            embed.add_field(
                name=f'{upgrade.name} {n}',
                value=upgrade.get_description(n),
                inline=True
            )

    await interaction.response.send_message(embed=embed)


if __name__ == '__main__':
    with open('client_secret.txt') as file:
        token = file.read().strip()
    bot.run(token)
