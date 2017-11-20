import discord
from discord.ext import commands
from .utils.chat_formatting import *
import os
from __main__ import send_cmd_help
from cogs.utils.dataIO import dataIO
from __main__ import settings
from urllib.parse import urlparse
import datetime

class UserProfiles:
    """Create a custom user profile, and pretend it's Facebook"""

    def __init__(self, bot):
        self.bot = bot
        self.users_loc = "data/userprofiles/users.json"
        self.users = dataIO.load_json(self.users_loc)
        self.ignored_domains = [
            "adf.ly",
            "bit.ly",
            "goo.gl",
            "bitly.com"
        ]

    def verify_user_data(self, user):
        if user.id not in self.users:
            self.users[user.id] = {
                "about": None,
                "pcspecs": None,
                "country": None,
                "website": None,
                "websitename": None,
                "gender": None,
                "age": None
            }
        else:
            if "websitename" not in self.users[user.id]:
                if self.users[user.id]["website"] is not None:
                    self.users[user.id]["websitename"] = self.users[user.id]["website"]
                else:
                    self.users[user.id]["websitename"] = None
            if "pcspecs" not in self.users[user.id]:
                self.users[user.id]["pcspecs"] = None

    def save_json(self):
        dataIO.save_json(self.users_loc, self.users)

    # This was taken from audio.py
    # I really don't want to bother dealing with learning how to use urlparse
    def _match_any_url(self, url):
        url = urlparse(url)
        if url.scheme and url.netloc:
            return url.netloc
        return False

    def get_role(self, user : discord.Member, server : discord.Server):
        _msg = ""
        if user.id in self.bot.get_cog("Owner").global_ignores["blacklist"]:
            # Users who have been blacklisted via [p]blacklist add
            _msg += ":no_entry_sign: **Blacklisted**\n"
        if user.id == settings.owner:
            _msg += ":tools: **Bot Owner**\n"
        admin = False
        mod = False
        sadmin = settings.get_server_admin(server)
        smod = settings.get_server_mod(server)
        for i in user.roles:
            if i.name.lower() == sadmin.lower():
                admin = True
            elif i.name.lower() == smod.lower():
                mod = True
        if int(user.id) == int(server.owner.id):
            _msg += ":key: Server Owner"
        elif admin is True:
            _msg += ":hammer: Server Admin"
        elif mod is True:
            _msg += ":shield: Server Mod"
        else:
            _msg += ":bust_in_silhouette: Member"
        return _msg

    def user_status(self, user : discord.User):
        if user.status == discord.Status.online:
            return "Online"
        elif user.status == discord.Status.idle:
            return "Idle"
        elif user.status == discord.Status.dnd:
            return "Do Not Disturb"
        elif user.status == discord.Status.offline:
            return "Offline"
        else:
            return "*Unknown status*"

    def is_discord_anniversary(self, joined_on, ts):
        if joined_on.strftime("%b") == ts.strftime("%b"):
            if joined_on.strftime("%d") == ts.strftime("%d"):
                if joined_on.strftime("%Y") != ts.strftime("%Y"):
                    return True
        return False

    def get_warning_count(self, user : discord.User, server : discord.Server):
        """Util for integration with the warnings cog"""
        try:
            warnings_cog = self.bot.get_cog("Warnings")
            if not warnings_cog:
                return False
            return warnings_cog.get_warning_count(server, user)
        except:
            return False

    @commands.group(pass_context=True, aliases=["social"], invoke_without_command=True, no_pm=True)
    async def user(self, ctx, user : discord.Member = None):
        """User profiles"""
        user = ctx.message.author if not user else user
        server = ctx.message.server
        userinfo = self.users[user.id] if user.id in self.users else {}
        roles = [x.name for x in user.roles if x.name != "@everyone"]
        usercolour = None
        status = self.user_status(user)
        game = None
        game_type = "playing"
        joined_at = user.joined_at
        since_created = (ctx.message.timestamp - user.created_at).days
        since_joined = (ctx.message.timestamp - joined_at).days
        user_joined = joined_at.strftime("%d %b %Y** at %I:%M:%S %p")
        user_created = user.created_at.strftime("%d %b %Y** at %I:%M:%S %p")
        user_warnings = self.get_warning_count(user=user, server=server)

        discord_anniversary = ""
        server_anniversary = ""

        if self.is_discord_anniversary(user.created_at, ctx.message.timestamp):
            # Calculate the year the user was created
            years_on_discord = (datetime.datetime.now() - (ctx.message.timestamp - user.created_at)).year
            # Get the total amount of year(s) since the user's creation
            years_on_discord = datetime.datetime.now().year - years_on_discord
            discord_anniversary = " *{} year{}! :tada:*".format(years_on_discord, "s" if years_on_discord > 1 else "")

        if self.is_discord_anniversary(joined_at, ctx.message.timestamp):
            # Calculate the year the user joined
            years_on_server = (datetime.datetime.now() - (ctx.message.timestamp - user.created_at)).year
            # Get the total amount of year(s) since the user's join
            years_on_server = datetime.datetime.now().year - years_on_server
            server_anniversary = " *{} year{}! :tada:*".format(years_on_server, "s" if years_on_server > 1 else "")

        joined_stats = ""
        joined_stats += "**▶ Discord:**\n"
        joined_stats += "**{} days ago**{}, on **{}\n".format(since_created, discord_anniversary, user_created)
        joined_stats += "\n**▶ This server:**\n"
        joined_stats += "**{} days ago**{}, on **{}\n".format(since_joined, server_anniversary, user_joined)

        if user.colour:
            usercolour = user.colour

        # User game or streaming status
        if user.game is None:
            pass
        elif user.game.url is None:
            game = "{}".format(user.game)
        else:
            game = "[{}]({})".format(user.game, user.game.url)
            game_type = "streaming"

        status_text = status
        if game is not None:
            status_text += ", {} **{}**".format(game_type, game)

        embed = discord.Embed(colour=usercolour, description=status_text)
        name = "{1} ({0})".format(user.name, user.nick) if user.nick else user.name
        if user.avatar_url:
            embed.set_author(name="Profile for {}".format(name), icon_url=user.avatar_url)
        else:
            embed.set_author(name="Profile for {}".format(name))

        if roles:
            roles = sorted(roles, key=[x.name for x in server.role_hierarchy
                                       if x.name != "@everyone"].index)
            roles = ", ".join(roles)
        else:
            roles = "None"

        # Generic user info
        embed.add_field(name="Joined", value=joined_stats, inline=False)
        embed.add_field(name="Bot Roles", inline=False, value=self.get_role(user=user, server=ctx.message.server))
        embed.add_field(name="Server Roles", inline=False, value=roles)
        # Customized user profiles
        if "gender" in userinfo and userinfo["gender"] is not None:
            embed.add_field(name="Gender", value=userinfo["gender"])
        if "country" in userinfo and userinfo["country"] is not None:
            embed.add_field(name="Country", value=userinfo["country"])
        if "website" in userinfo and userinfo["website"] is not None:
            embed.add_field(name="Website", value="[{}]({})".format(userinfo["websitename"] if userinfo["websitename"] is not None else userinfo["website"], userinfo["website"]))
        if "age" in userinfo and userinfo["age"] is not None:
            embed.add_field(name="Age", value=str(userinfo["age"]))
        if "about" in userinfo and userinfo["about"] is not None:
            embed.add_field(name="About Me", value=userinfo["about"], inline=False)
        if "pcspecs" in userinfo and userinfo["pcspecs"] is not None:
            embed.add_field(name="PC Specs", value=userinfo["pcspecs"], inline=False)
        embed.set_footer(text="User ID: {}".format(user.id))
        await self.bot.say(embed=embed)

    @user.command(pass_context=True, name="avatar")
    async def user_avatar(self, ctx, user : discord.User = None):
        """Displays the command issuer or specified user's avatar"""
        user = ctx.message.author if not user else user
        if not user.avatar_url:
            await self.bot.say(":exclamation: {} has no avatar!".format(user.display_name))
            return
        embed = discord.Embed(title="{}'s avatar".format(user.display_name))
        embed.set_image(url=user.avatar_url)
        await self.bot.say(embed=embed)

    @user.command(pass_context=True, name="reset")
    async def user_reset(self, ctx, user : discord.User = None):
        """Reset your social profile"""
        _profile = "your"
        if user:
            if not settings.owner:
                # This likely won't ever happen, but probably worth checking for regardless
                await self.bot.say("I don't have an owner yet! (`{}set owner`)".format(ctx.prefix))
                return
            # I know this is utterly atrocious
            # But I don't really care, because It At Least Works[tm]
            if not (int(ctx.message.author.id) == int(settings.owner)):
                user = ctx.message.author
            else:
                _profile = "**{}**'s".format(user.display_name)
        else:
            user = ctx.message.author
        if user.id not in self.users:
            await self.bot.say("You have no profile to reset!")
            return
        await self.bot.say(":x: Type \"yes\" to confirm that you want to reset {} social profile\n\n**This action cannot be undone!**".format(_profile))
        answer = await self.bot.wait_for_message(timeout=15, author=ctx.message.author)
        if answer is None or "yes" not in answer.content.lower():
            await self.bot.say("Cancelling profile reset.")
            return
        del self.users[user.id]
        self.save_json()
        await self.bot.say("✅ Profile successfully reset.")

    @user.command(pass_context=True, name="about")
    async def user_about(self, ctx, *, about : str = None):
        """About me

        Max of 350 characters"""
        self.verify_user_data(ctx.message.author)
        if not about:
            self.users[ctx.message.author.id].update({ "about": None })
            self.save_json()
            await self.bot.say("✅ Cleared your about me.")
            return
        if len(about) > 350:
            await self.bot.say("That about me is a little too long. (max 350 characters - your about me was {} characters long)".format(len(about)))
            return
        about = escape_mass_mentions(about)
        self.users[ctx.message.author.id].update({ "about": about })
        self.save_json()
        await self.bot.say("✅ Updated your about me info to:\n```\n{}\n```".format(about))

    @user.command(pass_context=True, name="pcspecs", aliases=["specs"])
    async def user_pcspecs(self, ctx, *, specs : str = None):
        """Your PC specs

        Max of 300 characters"""
        self.verify_user_data(ctx.message.author)
        if not specs:
            self.users[ctx.message.author.id].update({ "pcspecs": None })
            self.save_json()
            await self.bot.say("✅ Cleared your specs list.")
            return
        specs = escape_mass_mentions(specs)
        if len(specs) > 300:
            await self.bot.say("That specs list is a little too long. (max 300 characters - your list was {} characters long)\nHint: Try a PC Part Picker list!".format(len(specs)))
            return
        self.users[ctx.message.author.id].update({ "pcspecs": specs })
        self.save_json()
        await self.bot.say("✅ Updated your specs list to:\n```\n{}\n```".format(specs))

    @user.command(pass_context=True, name="website")
    async def user_website(self, ctx, name : str = None, *, website : str = None):
        """A link to your website

        Wrap the website name in quotes if it contains spaces
        Otherwise, it'll be considered part of the website URL

        Max of 25 characters (Name)
        Max of 30 characters (URL)"""
        self.verify_user_data(ctx.message.author)
        if name is None:
            self.users[ctx.message.author.id].update({ "website": None, "websitename": None })
            self.save_json()
            await self.bot.say("✅ Cleared your website link.")
            return
        if name is not None:
            if website is None:
                await send_cmd_help(ctx)
                return
            if len(name) > 25:
                await self.bot.say("That website name is a little too long. (max 25 characters - your website name was {} characters long)".format(len(name)))
                return
            if len(website) > 30:
                await self.bot.say("That website URL is a little too long. (max 30 characters - your website URL was {} characters long)".format(len(website)))
                return
            website = website.strip("<>")
            webmatch = self._match_any_url(website)
            if webmatch is False:
                await self.bot.say("That doesn't seem like a valid website URL.")
                return
        # silently ignore adfly urls
        if webmatch not in self.ignored_domains:
            self.users[ctx.message.author.id].update({ "website": website, "websitename": name })
            self.save_json()
        else:
            print("[UserProfiles] Silently ignoring attempted website link to domain {} (full URL: {})".format(webmatch, website))
        await self.bot.say("✅ Updated your website to:\n```\n{} (displayed as {})\n```".format(website, name))

    @user.command(pass_context=True, name="country")
    async def user_country(self, ctx, *, country : str = None):
        """Which country you reside in

        Max of 75 characters"""
        self.verify_user_data(ctx.message.author)
        if country is not None and len(country) > 75:
            await self.bot.say("That country name is a little too long. (max 75 characters - your country name was {} characters long)".format(len(country)))
            return
        self.users[ctx.message.author.id].update({ "country": country })
        self.save_json()
        await self.bot.say("✅ Updated your country to:\n```\n{}\n```".format(country))

    @user.command(pass_context=True, name="gender")
    async def user_gender(self, ctx, *, gender : str = None):
        """Which gender you are"""
        self.verify_user_data(ctx.message.author)
        if gender is not None and len(gender) > 25:
            await self.bot.say("That gender is a little too long. (max 25 characters - your gender was {} characters long)".format(len(gender)))
            return
        self.users[ctx.message.author.id].update({ "gender": gender })
        self.save_json()
        await self.bot.say("✅ Updated your gender to:\n```\n{}\n```".format(gender))

    @user.command(pass_context=True, name="age")
    async def user_age(self, ctx, *, age : int = None):
        """How old you are"""
        self.verify_user_data(ctx.message.author)
        if age is not None and age >= 110:
            await self.bot.say("🤔 I find it hard to believe you're actually a supercentenarian.")
            return
        self.users[ctx.message.author.id].update({ "age": age })
        self.save_json()
        await self.bot.say("✅ Updated your age to:\n```\n{}\n```".format(age))

def check_folder():
    # Check for older social folders
    if os.path.exists('data/social') and dataIO.is_valid_json('data/social/users.json'):
        print("[UserProfiles] Moving data/social/ to data/userprofiles/")
        os.rename("data/social", "data/userprofiles")
    if not os.path.exists('data/userprofiles'):
        print("[UserProfiles] Creating data/userprofiles/")
        os.makedirs('data/userprofiles')

def check_file():
    f = 'data/userprofiles/users.json'
    if dataIO.is_valid_json(f) is False:
        print("[UserProfiles] Creating users.json file")
        dataIO.save_json(f, {})

def setup(bot):
    check_folder()
    check_file()
    bot.add_cog(UserProfiles(bot))
