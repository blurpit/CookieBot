import random

import discord as d


GUILD = d.Object(id=913924123405729812)
cookie_quotes = [
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

class CookieBot(d.Client):
    def __init__(self, *, intents: d.Intents):
        super().__init__(intents=intents)
        self.tree = d.app_commands.CommandTree(self)

    async def on_ready(self):
        print(f'Logged in as {self.user}!')

    async def setup_hook(self):
        self.tree.copy_global_to(guild=GUILD)
        await self.tree.sync(guild=GUILD)
        print('Commands synced.')

intents = d.Intents.default()
intents.message_content = True
intents.members = True

client = CookieBot(intents=intents)

class CookieClicker(d.ui.View):
    @d.ui.button(label='Cookie!', style=d.ButtonStyle.red, emoji='🍪')
    async def click(self, interaction: d.Interaction, button: d.ui.Button):
        quote = random.choice(cookie_quotes)
        num = random.randint(1, 100)
        await interaction.response.send_message(
            f'{quote}\n{interaction.user.mention} got {num} cookie! Om nom nom nom'
        )

@client.tree.command()
async def hello(interaction: d.Interaction):
    """ Wake up babe its time for another april fools bot """
    await interaction.response.send_message(f'Hi, {interaction.user.mention}')

@client.tree.command()
async def cookie(interaction: d.Interaction):
    """ create cookie clicker message """
    view = CookieClicker()
    await interaction.response.send_message('CLICK FOR COOKIE!!!', view=view)


if __name__ == '__main__':
    with open('client_secret.txt') as file:
        client.run(file.read().strip())
