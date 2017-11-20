import discord
from discord.ext import commands
import random

class Memes:
    """Random commands that probably shouldn't even exist."""

    def __init__(self, bot):
        self.bot = bot
        self.angrymsgs = [
            "When life gives you lemons, get mad!",
            # PORTAL REFERENCING INTENSIFIES
            "When life gives you lemons? Don't make lemonade. Make life take the lemons back! Get mad!\n*'I don't want your damn lemons! What am I supposed to do with these?'*\n\nDemand to speak to life's manager! Make life *rue the day* it thought it could give __Cave Johnson__ *lemons*! Do you know who I am? I'm the man who's going to *burn your house down! **With the lemons!*** I'm going to get my engineers to invent a combustible lemon that *burns your house down*!",
            "（｀ー´）",
            "***ANGERY INTENSIFIES***",
            ":angry: :angry: :angry: :angry:",
            # ANGRY K INTENSIFIES
            "😡          😡\n😡       😡\n😡    😡\n😡 😡\n😡😡\n😡   😡\n😡      😡\n😡         😡\n😡            😡"
        ]

    @commands.command()
    async def spacing(self, spacing: int, *, message: str):
        """Adds spacing to messages. Because why not, of course?"""
        if spacing > 50 or spacing < 1:
            message = "Spacing must be between 1 and 50"
            spacing = 1
        if len(message) > 500:
            message = "🤔 That message is a bit too long."
        output = (" " * spacing).join(list(message))
        if len(output) > 1500:
            await self.bot.say((" " * 2).join(list("🤔 That message is a bit too long.")))
        await self.bot.say(output)

    @commands.command(pass_context=True, aliases=["angery"])
    async def angry(self, ctx, user: discord.Member=None, intensity: int=None):
        """（｀ー´）"""
        u = user
        if user is None:
          await self.bot.say(random.choice(self.angrymsgs))
        else:
            if intensity == 1 or intensity == None:
                await self.bot.say("**（；¬＿¬)** " + u.display_name)
            elif intensity == 2:
                await self.bot.say("**( ಠ ಠ )** " + u.display_name)
            elif intensity == 3:
                await self.bot.say("**(」゜ロ゜)」** " + u.display_name)
            elif intensity == 4:
                await self.bot.say("**( #`⌂´)/┌┛** " + u.display_name)
            elif intensity in [5,6]:
                await self.bot.say(u.display_name + " **щ(ºДºщ)**")
            elif intensity in [7,8,9]:
                await self.bot.say(u.display_name + " **Щ(ಠ益ಠЩ)**")
            elif intensity >= 10:
                await self.bot.say(u.display_name + " **Щ(◣д◢)Щ**")

    @commands.command(pass_context=True)
    async def banana(self, ctx, user: discord.Member=None):
        """It's like banning, but with bananas! And also harmless."""
        if user is not None and user.id == self.bot.user.id:
            await self.bot.say("What did __I__ do to hurt you?")
            return
        if user is None:
            await self.bot.say(":banana: Somehow, {0} managed to slip on their own banana.".format(ctx.message.author.display_name))
        else:
            if random.randint(0, 100) <= 95:
                await self.bot.say(":banana: It appears that {0} managed to ban {1} with a *banana*, of all things. How they managed that, is well beyond me.".format(ctx.message.author.display_name, user.display_name))
            else:
                await self.bot.say(":banana: {0} tried to ban {1} with a banana, but seems to have failed whilst doing so, and accidentally slipped on it in the process. Good work, {0}.".format(ctx.message.author.display_name, user.display_name))

def setup(bot):
    bot.add_cog(Memes(bot))
