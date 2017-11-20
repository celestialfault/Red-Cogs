import discord
from discord.ext import commands
import random

class Memes:
    """Random commands that probably shouldn't even exist."""

    def __init__(self, bot):
        self.bot = bot
        self.isshitmsgs = [
            "Knock knock, open the door, {user}! Your {obj} is garbage.",
            "Frankly, your {obj} is completely and utterly disgusting to even *be near*, {user}.",
            "If I had to be honest, {user}'s {obj} is probably the worst thing I've seen in my entire life. And I'm a *bot*, damnit. So that's probably saying something.",
            "Open 'ye ole eyes, {user}! Yer little {obj} there is pure rubbish! I wouldn't even wash *'ye old poopdeck with it*! Be better to just chuck it into the sea.",
            "Look around you, {user}. That {obj} is **pure trash**.",
            "Take a hint, {user}. Your {obj} isn't really bold and brash, but instead belongs in the trash.",
            "{user}, you still believe that a world where your {obj} isn't awful *exists?* Quite the dream-worthy material there. Namely, because that world would only ever exist in a dream.",
            "{user}: Your {obj} is rather plain, and doesn't watch Star Wars!",
            "{user}! Listen to me, nerd! That {obj} is awful, and it should only be able to exist in the vacuum of space, but here you are with it on Planet Earth!",
            "Oi! {user}! Your {obj} is completely worthless! Not even your rubbish bin would want it! I mean, look at it! It's **awful!**",
            "Maybe someone expects the Spanish Inquisition, but the Spanish Inquisition themselves would never *never* expect something as awful as {user}'s {obj}!",
            "Hey {user}: your {obj} is awful. I mean, just look around you - no one likes it.",
            "That {obj} is disliked by even your grandmother, {user}. And I'm sure she even loves the dirt you dig out of the back garden.",
            "Your {obj}? Actually *good*? Don't get me started, {user}. I could go on for days about how absolutely **disgusting, repulsive and abhorrent** it is.",
            "Dear {user},\n\nYour {obj} is actually the worst thing I've seen in my entire life.\nPlease, for the love of all that is holy, throw it in a volcano for me.\n\nSincerely,\n{author}",
            "Hello {user},\n\nWe have recieved your request of a small loan of a million dollars, but it is unfortunate to us to tell you that we have rejected your request due to your {obj} being so utterly atrocious.\n\nSorry, and thank you for choosing The Bank of {author}.",
            "{user}, your {obj} is an *actual laughingstock*. Probably a safer bet to save yourself trouble down the road, and just throw it in the trash.",
            "Hey everyone! {user} thinks their {obj} is good! What a nerd!",
            "I-It's not like I ever liked your {obj} anyways, b-**baka..!**", # [TSUNDERE BOT INTENSIFIES]
            "I can't *wait* to see {user}'s face when I throw their {obj} into a volcano~!",
            "*Hahahahaha~!*\n{user} thinks {author} actually *likes* their {obj}? What a *nerd~!*",
            "{user}'s {obj} in the current year? *Hahahaha~!*",
            "I'm sorry, what was that, {user}? I couldn't hear you over the sound of everyone in this room gagging over the mere sight of your {obj}."
        ]
        self.deleteyourmsgs = [
            # is this too harsh?
            "Delete your account {user}, you uncultured excuse of a human being.",
            "{user}'s account should really be dipped in sewage, flash-frozen, kicked to the sun, burned in an incinerator, and finally, deleted.",
            "{user}, I'm gonna count to 3, and your account better be deleted.",
            "Not even your grandma would appreciate your worthless excuse of an account, {user}.",
            "Hahahaha~!\n{user}'s account in [CURRENT YEAR]? What a *joke~!*",
            "What a fascinating story, {user}, in which chapter do you delete your account?",
            "The fact that {user} *still* hasn't deleted their account proves that there is no God.",
            # ok yeah this one may actually be too harsh
            "Hello, {user}. This is Cave Johnson from Aperture Science, and I regret to inform you that it appears your account has reduced my total lifespan, and it wasn't the moon rocks after all. So thanks for that. I'm sure Caroline will appreciate the knowledge. *Why didn't those engineers invent that damned combustible lemon...*"
        ]
        self.deleteyourmsgs_self = [
            "{user} seems to have finally realized that no one appreciates their account existing, and is now deleting it. About time, too.",
            "{user}, you're just now deleting your account? I thought you would have deleted it a *loooong time ago*. But here you are, just now deleting it, because you just can't stay away. Until now. Good riddance.",
            "It seems {user} is now finally getting wiser, and thus, also deactivating their account for good. Goodbye~\n\nP.S. No one will miss your worthless excuse of an account.",
            "Oh? {user} is finally deleting their account? I guess there is a God after all."
        ]
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
        self.thinking_emotes = [
            "<:thinkblob:305913901373980672>",
            "<:thonk:278460799935315970>",
            "<:think:290937344624951296>",
            "<:thinkong:273484128588922880>",
            "<:thanking:274356126747983872>",
            "🤔"
        ]
        self.thisisfilth = [
            "https://s.odinair.xyz/xItZDpt.gif",
            "https://s.odinair.xyz/RVR341N.png"
        ]

    @commands.command()
    async def facepalm(self, user : discord.Member = None):
        """(ノ_<。)"""
        if user is not None:
            await self.bot.say("Please put your hands to your forehead for " + user.display_name + "! (ノ_<。)")
        else:
            await self.bot.say("(ノ_<。)")

    @commands.command()
    async def spacing(self, spacing: int, *, message: str):
        """Adds spacing to messages. Because why not, of course?"""
        if spacing > 50 or spacing < 1:
            message = "Spacing must be between 1 and 50"
            spacing = 1
        if len(message) > 500:
            message = "🤔 That message is a bit too long."
        output = (" " * (spacing + 1)).join(list(message))
        if len(output) > 1500:
            await self.bot.say((" " * 2).join(list("🤔 That message is a bit too long.")))
        await self.bot.say(output)

    @commands.command(pass_context=True, aliases=["tableflip"])
    async def fliptable(self, ctx, *, text = ""):
        """(╯°□°）╯︵ ┻━┻"""
        chance = random.randint(10,75)
        if chance is 15:
            await self.bot.say("┳━┳ ︵╯(.□.╯) In Soviet Russia, table flips " + ctx.message.author.display_name + ".")
        else:
            await self.bot.say("(ノ・∀・)ノ彡┻━┻ " + text)

    @commands.command(pass_context=True, aliases=["angery"])
    async def angry(self, ctx, user : discord.Member = None, intensity : int = None):
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
    async def banana(self, ctx, user : discord.Member = None):
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

    @commands.command(pass_context=True)
    async def insultobj(self, ctx, user : discord.Member, *, object):
        """Knock knock! Your hair is trash."""
        if user is not None and user.id == self.bot.user.id:
            await self.bot.say("What did __I__ do to hurt you?")
            return
        isShitMsg = random.choice(self.isshitmsgs)
        await self.bot.say(isShitMsg.format(user=user.display_name, obj=object, author=ctx.message.author.display_name))

    @commands.command(aliases=["deleteyouraccount"], pass_context=True)
    async def deactivate(self, ctx, user : discord.User = None):
        """Your account is a waste of server space. Delete it."""
        if user is not None and user.id == self.bot.user.id:
            await self.bot.say("What did __I__ do to hurt you?")
            return
        if user is None or user.id == ctx.message.author.id:
            random_string = random.choice(self.deleteyourmsgs_self)
            user = ctx.message.author
        else:
            random_string = random.choice(self.deleteyourmsgs)
        await self.bot.say(random_string.format(user=user.display_name))

    @commands.command(name="thisisfilth", aliases=["lewd", "filth"])
    async def _thisisfilth(self):
        """This is filth!"""
        await self.bot.say(random.choice(self.thisisfilth))

    @commands.command(aliases=["think"])
    async def thinking(self):
        """[thinking intensifies]"""
        await self.bot.say(random.choice(self.thinking_emotes))

def setup(bot):
    bot.add_cog(Memes(bot))
