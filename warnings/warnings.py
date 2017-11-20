import discord
from discord.ext import commands
from .utils import checks
from .utils.chat_formatting import *
from __main__ import settings
from cogs.utils.dataIO import fileIO
from cogs.utils.dataIO import dataIO
from __main__ import send_cmd_help
import os
import logging
import datetime


class Warnings:
    def __init__(self, bot):
        self.bot = bot
        self.settings = fileIO("data/warnings/settings.json", "load")
        self.settings_loc = "data/warnings/settings.json"
        self.warnings = fileIO("data/warnings/warnings.json", "load")
        self.warnings_loc = "data/warnings/warnings.json"
        self.logger = logging.getLogger("red.warnings")
        if self.logger.level == 0:
            self.logger.setLevel(logging.INFO)
            handler = logging.FileHandler(
                filename="data/warnings/warn.log",
                encoding="utf-8",
                mode="a"
            )

    def save_json(self):
        dataIO.save_json(self.warnings_loc, self.warnings)

    # stackoverflow:
    # let other people do your work for you[tm]
    # https://stackoverflow.com/a/23148997
    async def split_list(self, arr, size):
        arrs = []
        while len(arr) > size:
            pice = arr[:size]
            arrs.append(pice)
            arr   = arr[size:]
        arrs.append(arr)
        return arrs

    #
    # ----- Internals -----
    #

    async def mod_log(self, server: discord.Server, **args):
        """
        This is a somewhat terrible workaround for the Mod cog not properly supporting custom mod-log cases.

        You probably shouldn't use this.
        """
        user = args.get('user')
        moderator = args.get('moderator')
        reason = args.get('reason', 'No reason specified')
        action = args.get('action', False)
        # Check for the existance of the mod cog
        mod_cog = self.bot.get_cog('Mod')
        if not mod_cog:
            return
        # Verify that mod logging is setup
        mod_settings = mod_cog.settings
        if server.id not in mod_settings:
            return
        mod_settings = mod_settings[server.id]
        if mod_settings["mod-log"] == None:
            return

        # Attempt to find the mod log channel
        mod_channel = None
        for channel in server.channels:
            if int(channel.id) == int(mod_settings["mod-log"]):
                mod_channel = channel
                break
        if not mod_channel:
            return

        action_desc = "Warning"
        if action == "kicked":
            action_desc = "Warning w/ Automatic Kick"
        elif action == "banned":
            action_desc = "Warning w/ Automatic Ban"

        # Create an embed
        embed = discord.Embed(title="{}".format(action_desc), color=discord.Colour.red(), description="**Reason:** {}".format(reason), timestamp=datetime.datetime.utcnow())

        embed.add_field(name="Moderator", value="{} (ID: {})".format(moderator.mention, moderator.id))
        embed.add_field(name="Warned User", value="{} (ID: {})".format(user.mention, user.id))

        embed.set_footer(text="This is warning #{} for {} (User ID {})".format(len(self.warnings[server.id][user.id]), user.display_name, user.id))

        await self.bot.send_message(mod_channel, embed=embed)

    async def send_message(self, server : discord.Server, user : discord.User, moderator : discord.User, reason : str, automated : bool = False, action : str = None):
        """
        [Internal API] Sends a private warning message to a user

        This is already called from add_warning, so you really shouldn't use this.
        """
        if user.bot:
            # Don't attempt to send messages to bot accounts
            return
        warntype = "a manual"
        if automated is True:
            warntype = "an automated"
        msg = (
            "```diff\n"
            "*** Warning ***\n\n"
            "+ Reason: {reason}\n"
            "+ Warned by: {moderator}\n"
            "+ Server: {server}\n"
            "".format(reason=reason, moderator=moderator.name, server=server.name)
        )
        if action == "kicked":
            msg += "\n- You have been automatically kicked from the server due to this warning\n"
        elif action == "banned":
            msg += "\n- You have been automatically banned from the server due to this warning\n"
        msg += "\n*** This is an automated message from {} warning\n*** Responses are not monitored".format(warntype)
        msg += "\n```"
        await self.bot.send_message(user, msg)

    #
    # ------- API -------
    #

    async def get_warning_count(self, server : discord.Server, user : discord.User):
        """
        Returns the specified user's warning count in the specified server
        """
        if server.id not in self.warnings:
            self.warnings[server.id] = {}
        if user.id not in self.warnings[server.id]:
            self.warnings[server.id][user.id] = []
        return len(self.warnings[server.id][user.id])

    async def get_warnings(self, server : discord.Server, user : discord.User, paginate : bool = False):
        """
        Gets a user's warnings

        Returns None if the specified user has no warnings
        Returns an unindexed array of warning pages with 10 warnings each if paginate is set to True

        Otherwise, returns an unindexed array of warnings
        """
        if server.id not in self.warnings:
            self.warnings[server.id] = {}
        if user.id not in self.warnings[server.id]:
            self.warnings[server.id][user.id] = []
        data = None
        if len(self.warnings[server.id][user.id]) == 0:
            return None
        if paginate is True:
            data = await self.split_list(self.warnings[server.id][user.id], 10)
        else:
            data = self.warnings[server.id][user.id]
        return data

    async def add_warning(self, server : discord.Server, user : discord.Member, moderator : discord.User, reason : str, automated : bool = False):
        """
        Adds a warning to a user in the specified server

        If the moderator in question is a bot, automated is defaulted to true
        """
        if moderator.bot:
            automated = True
        reason = escape_mass_mentions(reason)
        # Setup server warnings data if they don't exist
        if server.id not in self.warnings:
            self.warnings[server.id] = {}
        if user.id not in self.warnings[server.id]:
            self.warnings[server.id][user.id] = []
        self.warnings[server.id][user.id].append({
            "reason": reason,
            "by": moderator.name
        })
        autoaction = None
        actionemoji = None
        if server.id in self.settings and len(self.warnings[server.id][user.id]) >= self.settings[server.id]["ban"] and self.settings[server.id]["ban"] > 0:
            autoaction = "banned"
            actionemoji = ":hammer:"
        elif server.id in self.settings and len(self.warnings[server.id][user.id]) >= self.settings[server.id]["kick"] and self.settings[server.id]["kick"] > 0:
            autoaction = "kicked"
            actionemoji = ":boot:"
        # Attempt to send the warned user a warning message
        try:
            await self.send_message(server=server, user=user, moderator=moderator, reason=reason, automated=automated, action=autoaction)
        except:
            # Don't let a failed message prevent us from adding warnings
            pass
        # Automatic kick / ban
        try:
            # Try to automatically do the specified action
            if autoaction is "kicked":
                await self.bot.kick(user)
            elif autoaction is "banned":
                await self.bot.ban(user, delete_message_days=self.settings[server.id]["delete_message_days"])
        except:
            pass
        try:
            # Mod log
            await self.mod_log(server=server, user=user, moderator=moderator, reason=reason, action=autoaction)
        except:
            pass
        # Finally, save the warning
        self.save_json()
        if autoaction is not None:
            return autoaction
        else:
            return "warned"

    async def remove_warning(self, server : discord.Server, user : discord.User, warning : int):
        """Removes a specific warning from a user"""
        if server.id not in self.warnings or user.id not in self.warnings[server.id] or len(self.warnings[server.id][user.id]) == 0:
            raise ValueError("That user hasn't been warned yet")
        if warning < 1:
            raise IndexError("Warning cannot be less than one")
        if warning > len(self.warnings[server.id][user.id]):
            raise IndexError("Warning #{} doesn't exist for the specified user".format(warning))
        del self.warnings[server.id][user.id][warning - 1]
        self.save_json()

    async def clear_warnings(self, server : discord.Server, user : discord.User, moderator : discord.User):
        """Clears warnings for a user"""
        if server.id not in self.warnings or user.id not in self.warnings[server.id]:
            raise ValueError("That user hasn't been warned yet")
        self.warnings[server.id][user.id] = []
        self.save_json()

    #
    # ------- [p]warn / [p]warnings / [p]warning -------
    #

    def is_mod(self, user : discord.Member, server : discord.Server):
        if int(user.id) == int(server.owner.id):
            return True
        sadmin = settings.get_server_admin(server)
        smod = settings.get_server_mod(server)
        for i in user.roles:
            if i.name.lower() == sadmin.lower():
                return True
            elif i.name.lower() == smod.lower():
                return True

    @commands.group(pass_context=True, invoke_without_command=True, no_pm=True, aliases=["warnings", "warning"])
    @checks.mod_or_permissions(manage_messages=True)
    async def warn(self, ctx, user : discord.User, *reason : str):
        """Gives a user a warning"""
        if ctx.message.server.id not in self.settings:
            self.settings[ctx.message.server.id] = { "kick": 0, "ban": 0, "delete_message_days": 0 }
            self.save_json()
        if user.id == self.bot.user.id:
            await self.bot.say("What did *I* do to hurt you?")
            return
        if user.id == ctx.message.author.id:
            await self.bot.say("If you have to warn yourself, you must be a miserable excuse of a moderator.")
            return
        if self.is_mod(user, ctx.message.server):
            await self.bot.say("Sorry, but I can't let you warn other moderators.")
            return
        result = await self.add_warning(server=ctx.message.server, user=user, moderator=ctx.message.author, reason=reason, automated=False)
        embed = discord.Embed(title="Warning successfully recorded", colour=discord.Colour.red())
        embed.add_field(name="Warning #{}".format(len(self.warnings[ctx.message.server.id][user.id])), value=escape_mass_mentions(reason))
        self.logger.info("Moderator {} gave a warning to {} for '{}'".format(ctx.message.author.name, user.name, reason))
        # If this warning resulted in an automatic action, add it to the footer
        if result == "kicked":
            embed.set_footer(text=":boot: This warning resulted in an automatic kick")
            self.logger.info("Automatically kicked {}".format(user.name))
        elif result == "banned":
            embed.set_footer(text=":hammer: This warning resulted in an automatic ban")
            self.logger.info("Automatically banned {}".format(user.name))
        await self.bot.say(embed=embed)

    @warn.command(pass_context=True, no_pm=True, name="list")
    async def warn_list(self, ctx, user : discord.User = None, page : int = 1):
        """Gets the list of warnings for a user"""
        server = ctx.message.server
        if user is None:
            user = ctx.message.author
        if server.id not in self.warnings:
            self.warnings[server.id] = {}
            self.save_json()
        if user.id not in self.warnings[server.id] or len(self.warnings[server.id][user.id]) < 1:
            await self.bot.say("{user} has no warnings!".format(user=user.display_name))
            return
        warningid = 1
        warnings = await self.get_warnings(server=ctx.message.server, user=user, paginate=True)
        if page > len(warnings):
            await self.bot.say("That page doesn't exist!")
            return
        try:
            embed = discord.Embed(title="{warnings} warnings for {user}".format(user=user.display_name, warnings=len(self.warnings[server.id][user.id])),
                colour=discord.Colour.red())
            for warning in warnings[page - 1]:
                # break after 10 warnings
                if warningid > 10:
                    embed.set_footer(text="Page {} out of {}".format(page, len(warnings)))
                    break
                embed.add_field(name="Warning #{id}".format(id=warningid), value="{warning} **(warned by {moderator})**".format(warning=warning["reason"], moderator=warning["by"]), inline=False)
                warningid = warningid + 1
            await self.bot.say(embed=embed)
        except:
            await self.bot.say("I need the `Embed Links` permission to list warnings.")

    @warn.command(pass_context=True, no_pm=True, name="clear")
    @checks.mod_or_permissions(manage_messages=True)
    async def warn_clear(self, ctx, user : discord.User):
        """Clears all warnings on record for the specified user"""
        amount = len(self.warnings[ctx.message.server.id][user.id])
        await self.clear_warnings(server=ctx.message.server, user=user, moderator=ctx.message.author)
        await self.bot.say("Cleared **{amt}** warning(s) from {user}.".format(amt=amount, user=user.display_name))
        self.logger.info("Moderator {} cleared {}'s warnings".format(ctx.message.author.name, user.name))

    @warn.command(pass_context=True, no_pm=True, name="remove", aliases=["delete"])
    @checks.mod_or_permissions(manage_messages=True)
    async def delwarn(self, ctx, user : discord.User, warning : int):
        """Removes a single warning from a user"""
        if warning < 1:
            await self.bot.say("Warning ID cannot be less than one!")
            return
        if ctx.message.server.id not in self.warnings or user.id not in self.warnings[ctx.message.server.id]:
            await self.bot.say("That user hasn't been warned yet!")
            return
        if warning > len(self.warnings[ctx.message.server.id][user.id]):
            await self.bot.say("That warning doesn't exist!")
            return
        try:
            await self.remove_warning(server=ctx.message.server, user=user, warning=warning)
        except:
            await self.bot.say("Failed to remove warning")
            return
        await self.bot.say("Removed warning **#{warning}** from **{user}**.".format(warning=warning, user=user.display_name))
        self.logger.info("Moderator {} removed warning #{} from {}".format(ctx.message.author.name, warning, user.name))

    #
    # ------- [p]warnset -------
    #

    @commands.group(pass_context=True, no_pm=True)
    @checks.admin_or_permissions(administrator=True)
    async def warnset(self, ctx):
        """Warnings management"""
        if ctx.message.server.id not in self.settings:
            self.settings[ctx.message.server.id] = { "kick": 0, "ban": 0, "delete_message_days": 0 }
            self.save_json()
        if ctx.invoked_subcommand is None:
            await send_cmd_help(ctx)
            msg = ""
            _settings = self.settings[ctx.message.server.id]
            if _settings["kick"] < 1:
                msg += "Autokick threshold: Disabled"
            else:
                msg += "Autokick threshold: {} warnings".format(_settings["kick"])
            if _settings["ban"] < 1:
                msg += "\nAutoban threshold: Disabled\nMessage deletion: Disabled"
            else:
                msg += "\nAutoban threshold: {} warnings".format(_settings["ban"])
                if _settings["delete_message_days"] < 1:
                    msg += "\nMessage deletion: Disabled"
                else:
                    msg += "\nMessage deletion: {} days".format(_settings["delete_message_days"])
            await self.bot.say(box(msg))

    @warnset.command(pass_context=True, no_pm=True, name="kick", aliases=["autokick"])
    @checks.admin_or_permissions(administrator=True)
    async def warnset_kick(self, ctx, warnings : int = 0):
        """Set the amount of warnings needed to automatically kick"""
        if warnings < 0:
            await self.bot.say("Warnings amount must be either one warning, or zero to disable")
            return
        self.settings[ctx.message.server.id]["kick"] = warnings
        self.save_json()
        if warnings < 1:
            await self.bot.say("Disabled autokicking")
        else:
            await self.bot.say("Now autokicking after {} warnings".format(warnings))

    @warnset.command(pass_context=True, no_pm=True, name="ban", aliases=["autoban"])
    @checks.admin_or_permissions(administrator=True)
    async def warnset_ban(self, ctx, warnings : int = 0):
        """Set the amount of warnings needed to automatically ban"""
        if warnings < 0:
            await self.bot.say("Warnings amount must be either one warning, or zero to disable")
            return
        self.settings[ctx.message.server.id]["ban"] = warnings
        self.save_json()
        if warnings < 1:
            await self.bot.say("Disabled autobanning")
        else:
            await self.bot.say("Now autobanning after {} warnings, deleting {} day(s) worth of messages".format(warnings, self.settings[ctx.message.server.id]["delete_message_days"]))

    @warnset.command(pass_context=True, no_pm=True, name="delete")
    @checks.admin_or_permissions(administrator=True)
    async def warnset_ban_delete(self, ctx, days : int = 0):
        """Set how many days worth of messages should be deleted upon autobanning"""
        if days < 0 or days > 7:
            await self.bot.say("The amount of days must be between zero and seven days")
            return
        self.settings[ctx.message.server.id]["delete_message_days"] = days
        self.save_json()
        if days < 1:
            await self.bot.say("Disabled deleting messages upon autobanning.")
        else:
            if self.settings[ctx.message.server.id]["ban"] < 1:
                await self.bot.say("Now deleting {} days worth of messages upon autobanning (this won't take effect until you set the autoban threshold)".format(days))
            else:
                await self.bot.say("Now autobanning after {} warnings, deleting {} day(s) worth of messages".format(self.settings[ctx.message.server.id]["ban"], days))

def check_folder():
    if not os.path.exists("data/warnings"):
        self.logger.info("Creating data/warnings folder...")
        os.makedirs("data/warnings")

def check_file():
    warnings = {}
    f = "data/warnings/warnings.json"
    if not fileIO(f, "check"):
        self.logger.info("Creating default warnings data file...")
        fileIO(f, "save", warnings)

def setup(bot):
    check_folder()
    check_file()
    n = Warnings(bot)
    bot.add_cog(n)
