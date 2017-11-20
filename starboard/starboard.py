import discord
from .utils.chat_formatting import escape_mass_mentions
from discord.ext import commands
import asyncio
from __main__ import send_cmd_help
from __main__ import settings
from .utils import checks
import re
import math
try:
    from pymongo import MongoClient
except:
    raise RuntimeError("Can't load pymongo. Do 'pip3 install pymongo'.")

try:
    client = MongoClient()
    db = client["starboard"]
except:
    print("Can't load database; is MongoDB running?")


class Starboard:
    """Another generic starboard"""

    def __init__(self, bot):
        self.bot = bot
        self.queue = {}

    async def is_mod(self, user: discord.Member, server: discord.Server):
        if str(user.id) == str(server.owner.id):
            return True
        sadmin = settings.get_server_admin(server)
        smod = settings.get_server_mod(server)
        for i in user.roles:
            if i.name.lower() == sadmin.lower():
                return True
            elif i.name.lower() == smod.lower():
                return True

    async def get_mod_log(self, server: discord.Server):
        # Check for the existance of the mod cog
        mod_cog = self.bot.get_cog('Mod')
        if not mod_cog:
            return None
        # Verify that mod logging is setup
        mod_settings = mod_cog.settings
        if server.id not in mod_settings:
            return None
        mod_settings = mod_settings[server.id]
        if mod_settings["mod-log"] == None:
            return None

        # Attempt to find the mod log channel
        mod_channel = None
        for channel in server.channels:
            if int(channel.id) == int(mod_settings["mod-log"]):
                return channel
        if not mod_channel:
            return None

    async def get_or_create_star(self, message: discord.Message):
        """Internal API to create a starboard entry"""
        server = message.server
        star = db.stars.find_one({'message_id': message.id})
        if not star:
            star = {
                'message_id': message.id,
                'channel_id': message.channel.id,
                'server_id': message.server.id,
                'starboard_message': None,
                'stars': 0,
                'starrers': [],
                'removed': False
            }
            db.stars.insert_one(star)
        return star

    async def validate_star(self, message: discord.Message, user: discord.User):
        """Internal API to validate an attempted star or unstar"""
        server = message.server
        serv = db.servers.find_one({'server_id': server.id})
        # Verify that this server's starboard is setup
        if not serv or not serv["starboard"]:
            return False
        # Check blacklist status
        bl = await self.is_blacklisted(user, server)
        if bl:
            return False
        bl = await self.is_blacklisted(message.author, server)
        if bl:
            return False
        # Check for selfstarring
        selfstar = False
        if "selfstar" in serv:
            selfstar = serv["selfstar"]
        if not selfstar and user.id is message.author.id:
            return False
        # Verify the starboard channel exists
        channel = self.bot.get_channel(serv["starboard"])
        if not channel or str(channel.id) == str(message.channel.id):
            return False
        # Verify that there's some content we can embed (attachments or text)
        return (message.content and len(message.content) > 0) or (message.attachments and len(message.attachments) > 0)

    #######################################################################
    #                               API                                   #
    #######################################################################

    async def get_user_stats(self, user: discord.User):
        userstats = db.users.find_one({'user_id': user.id})
        if not userstats:
            userstats = {
                'user_id': user.id,
                'stars_given': 0,
                'stars_received': 0
            }
            db.users.insert_one(userstats)
        return userstats

    async def update_star_statistic(self, starred_user: discord.User, starred_by: discord.User, message: discord.Message, increment: bool = True):
        """
        Increment or decrement star statistics for the specified users

        If increment is False, this decrements; otherwise increments
        """
        if starred_user.id == starred_by.id:
            return
        op = 1
        if increment is False:
            op = -1
        starred = await self.get_user_stats(starred_user)
        by = await self.get_user_stats(starred_by)
        db.users.update_one({'user_id': starred_user.id}, {'$set': {
            'stars_received': starred['stars_received'] + op
        }})
        db.users.update_one({'user_id': starred_by.id}, {'$set': {
            'stars_given': by['stars_given'] + op
        }})

    async def add_star(self, message: discord.Message, user: discord.User):
        """
        Adds a user's star.

        Most errors are silently swallowed; for instance:

        - If a user is the message author, and the server settings does not allow self-starring
        - The server does not have a starboard setup
        - Or the user already starred the message
        """
        server = message.server
        serv = db.servers.find_one({'server_id': server.id})
        can_continue = await self.validate_star(message, user)
        if not can_continue:
            return
        # Get the data for this message's stars
        star = await self.get_or_create_star(message)
        if 'removed' in star and star['removed'] is True:
            return
        # Add the user to the starrers data
        starrers = [] if "starrers" not in star else star["starrers"]
        if user.id in starrers:
            return
        starrers.append(user.id)
        await self.update_star_statistic(message.author, user, True)
        # Increment the star count
        star_count = star["stars"] + 1
        # Handle the starboard message
        msg = await self.starboard_msg(message, star, serv, star_count)
        # Update the database entry
        db.stars.update_one({'message_id': message.id}, {'$set': {
            'stars': star_count,
            'starboard_message': msg,
            'starrers': starrers
        }})

    async def remove_star(self, message: discord.Message, user: discord.User):
        """
        Removes a user's star.

        If the user never starred the message, or the server doesn't have a starboard,
        the removal attempt is silently ignored.
        """
        server = message.server
        serv = db.servers.find_one({'server_id': server.id})
        can_continue = await self.validate_star(message, user)
        if not can_continue:
            return
        # Get the data for this message's stars
        star = db.stars.find_one({'message_id': message.id})
        if not star:
            return
        if 'removed' in star and star['removed'] is True:
            return
        # Check if the user is in the starrers array
        starrers = [] if not star["starrers"] else star["starrers"]
        if user.id not in starrers:
            return
        starrers.pop(starrers.index(user.id))
        # Decrease the star count
        await self.update_star_statistic(message.author, user, False)
        star_count = star["stars"] - 1
        if star_count < 0:
            print("Star count for message ID {} is a negative number ({})".format(
                message.id, star_count))
            raise ValueError("star count is a negative value")
        # Handle the starboard message
        msg = await self.starboard_msg(message, star, serv, star_count)
        # Update the database entry
        db.stars.update_one({'message_id': message.id}, {'$set': {
            'stars': star_count,
            'starboard_message': msg,
            'starrers': starrers
        }})

    async def remove_starboard_msg(self, message_id: str):
        """
        Removes a message from the starboard, and prevents it from appearing on the starboard again
        """
        star = await self.get_star(message_id)
        if not star:
            return
        if 'removed' in star and star['removed'] is True:
            return
        # Try to find the server's starboard
        if 'server_id' not in star:
            return
        serv = db.servers.find_one({'server_id': star['server_id']})
        if not serv or not serv['starboard']:
            return
        try:
            starboard_channel = self.bot.get_channel(serv['starboard'])
        except discord.NotFound:
            return
        # Try to find the starboard message if it exists
        if star['starboard_message']:
            try:
                starboard_msg = await self.bot.get_message(starboard_channel, star['starboard_message'])
                if starboard_msg.author.id == self.bot.user.id:
                    await self.bot.delete_message(starboard_msg)
            except discord.NotFound:
                pass
            except discord.Forbidden:
                pass
        db.stars.update_one({'message_id': message_id}, {'$set': {
            'removed': True
        }})

    async def has_starred(self, message: discord.Message, user: discord.User):
        """
        Checks if a user has starred a message.
        """
        star = db.stars.find_one({'message_id': message.id})
        if not star:
            return False
        if "starrers" not in star:
            return False
        return user.id in star["starrers"]

    async def is_blacklisted(self, user: discord.User, server: discord.Server):
        serv = db.servers.find_one({'server_id': server.id})
        # Verify that this server's starboard is setup
        if not serv or not serv["starboard"]:
            return False
        server_blacklist = [] if 'blacklist' not in serv else serv['blacklist']
        global_blacklist = self.bot.get_cog("Owner").global_ignores["blacklist"]
        return user.id in global_blacklist or user.id in server_blacklist:

    async def mod_log_remove(self, server: discord.Server, moderator: discord.User, message: discord.Message):
        mod_channel = await self.get_mod_log(server)
        if not mod_channel:
            return

        embed = discord.Embed(
            title="Starboard Message Removed", color=discord.Colour.red())

        embed.add_field(name="Author", value="{} (ID: {})".format(
            message.author.mention, message.author.id))
        embed.add_field(name="Moderator", value="{} (ID: {})".format(
            moderator.mention, moderator.id))
        if(len(message.content) > 0):
            embed.add_field(
                name="Content", value=message.content, inline=False)
        if message.attachments and len(message.attachments) > 0:
            embed.set_image(url=message.attachments[0]["url"])

        await self.bot.send_message(mod_channel, embed=embed)

    async def mod_log_blacklist(self, server: discord.Server, user: discord.User, moderator: discord.User, act: bool, reason: str = None):
        mod_channel = await self.get_mod_log(server)
        if not mod_channel:
            return

        action_desc = "Blacklist"
        if not act:
            action_desc = "Unblacklist"

        # Create an embed
        embed = discord.Embed(title="Starboard {}".format(action_desc), color=discord.Colour.red(
        ), description="**Reason:** {}".format(reason if reason else "No reason given"))

        embed.add_field(name="Moderator", value="{} (ID: {})".format(
            moderator.mention, moderator.id), inline=False)
        embed.add_field(name="{}ed User".format(
            action_desc), value="{} (ID: {})".format(user.mention, user.id), inline=False)

        await self.bot.send_message(mod_channel, embed=embed)

    async def get_star(self, message_id: str):
        return db.stars.find_one({'message_id': message_id})

    #######################################################################
    #                             STARBOARD                               #
    #######################################################################

    async def starboard_msg(self, message: discord.Message, star_data, serv, scount):
        # Ensure the starboard channel exists
        channel = self.bot.get_channel(serv["starboard"])
        if not channel:
            return None
        msg = None
        if star_data["starboard_message"]:
            try:
                msg = await self.bot.get_message(channel, star_data["starboard_message"])
            except discord.NotFound:
                pass
        # Check if we're at or above the minimum stars required for a starboard message
        if scount < serv["min_stars"]:
            if star_data["starboard_message"] and msg:
                # Delete the starboard message
                await self.bot.delete_message(msg)
            return None
        embed = discord.Embed(color=discord.Colour.gold(),
                              description=escape_mass_mentions(
                                  message.content),
                              timestamp=message.timestamp)
        embed.set_footer(text=str(message.id))
        if message.author.avatar_url:
            embed.set_author(
                name="{}".format(message.author.display_name),
                icon_url=message.author.avatar_url
            )
        else:
            embed.set_author(name="{}".format(message.author.display_name))
        if message.attachments and len(message.attachments) > 0:
            embed.set_image(url=message.attachments[0]["url"])
        emoji = "⭐"
        if scount > math.ceil(serv["min_stars"] + (serv["min_stars"] * 2)):
            emoji = "🌟"
        elif scount > math.ceil(serv["min_stars"] + (serv["min_stars"] * 3.4)):
            emoji = "💫"
        elif scount > math.ceil(serv["min_stars"] + (serv["min_stars"] * 6.3)):
            emoji = "✨"
        if msg:
            await self.queue_edit(message.id, scount, {
                "starboard": msg,
                "embed": embed,
                "message": message,
                "emoji": emoji,
                "server": serv
            })
        else:
            content = "{} **{}** {}".format(emoji, scount,
                                            message.channel.mention)
            try:
                msg = await self.bot.send_message(channel, content=content, embed=embed)
                await asyncio.sleep(0.5)
                await self.bot.add_reaction(msg, "⭐")
            except discord.Forbidden:
                return None
            except discord.NotFound:
                pass
        return msg.id

    async def queue_edit(self, message_id: str, stars: int, data):
        if message_id in self.queue:
            self.queue[message_id]["stars"] = stars
            self.queue[message_id]["embed"] = data["embed"]
            self.queue[message_id]["emoji"] = data["emoji"]
            self.queue[message_id]["server"] = data["server"]
        else:
            self.queue[message_id] = {
                'stars': stars,
                'starboard': data['starboard'],
                'embed': data['embed'],
                'channel': data['message'].channel,
                'message': data['message'].channel,
                'emoji': data['emoji'],
                'server': data['server']
            }

    #######################################################################
    #                             COMMANDS                                #
    #######################################################################

    @commands.command(name='star', pass_context=True, no_pm=True)
    async def _star(self, ctx, message_id: int):
        """
        Star or unstar a message by ID. Must be run in the same channel with the message.
        """
        channel = ctx.message.channel
        server = ctx.message.server
        user = ctx.message.author
        serv = db.servers.find_one({'server_id': server.id})
        if not serv or "starboard" not in serv or serv["starboard"] is None:
            await self.bot.say("This server doesn't have a starboard setup yet!")
            return
        try:
            msg = await self.bot.get_message(channel, message_id)
        except discord.NotFound:
            pass
        if not msg:
            return await self.bot.say("That message doesn't exist in this channel!")
        is_blacklisted = await self.is_blacklisted(user, server)
        if is_blacklisted:
            return
        author_blacklisted = await self.is_blacklisted(msg.author, server)
        if author_blacklisted:
            return await self.bot.say(":no_entry_sign: The author of that message is blacklisted from using the starboard")
        if msg.author.id == user.id:
            if 'selfstar' not in serv or not serv['selfstar']:
                return await self.bot.say("You can't star your own messages!")
        hasstar = await self.has_starred(msg, user)
        if hasstar:
            await self.remove_star(msg, user)
            await self.bot.say(":ok_hand: Removed star for the message sent by {}".format(msg.author))
        else:
            await self.add_star(msg, user)
            await self.bot.say(":ok_hand: Added star for the message sent by {}".format(msg.author))

    @commands.group(name='starboard', pass_context=True, no_pm=True)
    async def _starboard(self, ctx):
        """
        Manage starboard settings
        """
        server = ctx.message.server
        serv = db.servers.find_one({'server_id': server.id})
        if not serv:
            new_server = {
                'server_id': server.id,
                'starboard': None,
                'min_stars': 1,
                'selfstar': False,
                'blacklist': []
            }
            db.servers.insert_one(new_server)
            serv = db.servers.find_one({'server_id': server.id})
        if ctx.invoked_subcommand is None:
            await send_cmd_help(ctx)

    @_starboard.command(name='stats', pass_context=True, no_pm=True)
    async def _starboard_stats(self, ctx, user: discord.User = None):
        """
        Get starboard statistics for the message author, or a specified user
        """
        user = ctx.message.author if not user else user
        embed = discord.Embed(colour=discord.Colour.gold())
        if user.avatar_url:
            embed.set_author(name="Starboard statistics for {}".format(
                user.display_name), icon_url=user.avatar_url)
        else:
            embed.set_author(
                name="Starboard statistics for {}".format(user.display_name))
        stats = await self.get_user_stats(user)
        embed.add_field(name="Stars Given", value=str(stats['stars_given']))
        embed.add_field(name="Stars Received",
                        value=str(stats['stars_received']))
        await self.bot.say(embed=embed)

    @_starboard.command(name='channel', pass_context=True, no_pm=True)
    @checks.admin_or_permissions(manage_channels=True)
    async def _starboard_channel(self, ctx, channel: discord.Channel = None):
        """
        Set the server's starboard channel
        """
        server = ctx.message.server
        db.servers.update_one({'server_id': server.id}, {'$set': {
            'starboard': None if channel is None else channel.id
        }})
        if not channel:
            await self.bot.say(":ok_hand: Cleared the starboard channel")
        else:
            await self.bot.say(":ok_hand: Set starboard channel to {}".format(channel.mention))

    @_starboard.command(name='minstars', aliases=['stars'], pass_context=True, no_pm=True)
    @checks.admin_or_permissions(manage_messages=True)
    async def _starboard_minstars(self, ctx, minimum: int):
        """
        Set the amount of stars required to send a message to the starboard

        The recommended value is between 2 and 10
        """
        server = ctx.message.server
        if minimum < 1:
            await self.bot.say("The minimum amount of stars must be at least one or more")
            return
        db.servers.update_one({'server_id': server.id}, {'$set': {
            'min_stars': minimum
        }})
        await self.bot.say(":ok_hand: Set minimum stars required to {}".format(minimum))

    @_starboard.command(name='selfstar', pass_context=True, no_pm=True)
    @checks.admin_or_permissions(manage_messages=True)
    async def _starboard_selfstar(self, ctx):
        """
        Toggles the ability to selfstar messages
        """
        server = ctx.message.server
        serv = db.servers.find_one({'server_id': server.id})
        selfstar = False
        if "selfstar" in serv:
            selfstar = serv["selfstar"]
        db.servers.update_one({'server_id': server.id}, {'$set': {
            'selfstar': not selfstar
        }})
        if selfstar:
            await self.bot.say(":ok_hand: Disabled self-starring")
        else:
            await self.bot.say(":ok_hand: Enabled self-starring")

    @_starboard.command(name='remove', pass_context=True, no_pm=True)
    @checks.admin_or_permissions(administrator=True)
    async def _starboard_remove(self, ctx, message_id: int):
        """
        Removes a message from the starboard

        Messages removed will not update to reflect any new stars received, nor grant any new stars given/received statistics
        """
        star = await self.get_star(str(message_id))
        if not star:
            return await self.bot.say(":x: That message hasn't been starred yet")
        if 'removed' in star and star['removed']:
            return await self.bot.say(":x: That starboard message has already been removed")
        if 'server_id' not in star:
            return await self.bot.say("❗ I'm missing data that I need to properly remove that message")
        if str(star['server_id']) != str(ctx.message.server.id):
            return await self.bot.say("❗ You can't remove starboard messages that are not in the same server")
        await self.remove_starboard_msg(str(message_id))
        msg = await self.bot.get_message(self.bot.get_channel(star['channel_id']), star['message_id'])
        await self.mod_log_remove(msg.server, ctx.message.author, msg)
        await self.bot.add_reaction(ctx.message, "✅")

    @_starboard.group(name='blacklist', pass_context=True, no_pm=True)
    @checks.admin_or_permissions(administrator=True)
    async def _starboard_blacklist(self, ctx):
        """
        Manage the Starboard blacklist.

        Users on this blacklist will not be able to have their messages starred or star other user's messages.
        """
        if str(ctx.invoked_subcommand) == "starboard blacklist" or str(ctx.invoked_subcommand) == "blacklist":
            await send_cmd_help(ctx)

    @_starboard_blacklist.command(name='add', pass_context=True, no_pm=True)
    @checks.admin_or_permissions(administrator=True)
    async def _blacklist_add(self, ctx, user: discord.User, *, reason: str = None):
        """
        Add a user to the server's Starboard blacklist.
        """
        server = ctx.message.server
        serv = db.servers.find_one({'server_id': server.id})
        blacklist = []
        if 'blacklist' in serv:
            blacklist = serv['blacklist']
        if user.id in blacklist:
            await self.bot.say("That user is already blacklisted!")
            return
        blacklist.append(user.id)
        db.servers.update_one({'server_id': server.id}, {'$set': {
            'blacklist': blacklist
        }})
        await self.bot.say(":ok_hand: User is now blacklisted from starring or being starred")
        await self.mod_log_blacklist(server, user, ctx.message.author, True, reason)

    @_starboard_blacklist.command(name='remove', aliases=['rm'], pass_context=True, no_pm=True)
    @checks.admin_or_permissions(administrator=True)
    async def _blacklist_rm(self, ctx, user: discord.User, *, reason: str = None):
        """
        Remove a user from the server's Starboard blacklist.
        """
        server = ctx.message.server
        serv = db.servers.find_one({'server_id': server.id})
        blacklist = []
        if 'blacklist' in serv:
            blacklist = serv['blacklist']
        if user.id not in blacklist:
            await self.bot.say("That user is not blacklisted!")
            return
        blacklist.pop(blacklist.index(user.id))
        db.servers.update_one({'server_id': server.id}, {'$set': {
            'blacklist': blacklist
        }})
        await self.bot.say(":ok_hand: User is no longer blacklisted from starring or being starred")
        await self.mod_log_blacklist(server, user, ctx.message.author, False, reason)

    #####
    # Debug commands
    #####

    @_starboard.group(name='debug', pass_context=True)
    @checks.is_owner()
    async def _starboard_debug(self, ctx):
        if ctx.invoked_subcommand is None:
            await send_cmd_help(ctx)

    @_starboard_debug.command(name='starinfo')
    async def _starboard_starinfo(self, message_id: int):
        """
        Returns the raw MongoDB data for a message's stars.

        This is mostly intended to be a debug utility.
        """
        _s = await self.get_star(str(message_id))
        if not _s:
            return await self.bot.say("```python\nNone```")
        if len(_s["starrers"]) > 20:
            _s["starrers"] = ["omitted due to length"]
        await self.bot.say("```python\n{}```".format(_s))

    @_starboard_debug.command(name='serverinfo')
    @checks.is_owner()
    async def _starboard_servinfo(self, server_id: int):
        """
        Returns the raw MongoDB data for a server.

        This is mostly intended to be a debug utility.
        """
        serv = db.servers.find_one({'server_id': str(server_id)})
        if not serv:
            return await self.bot.say("```python\nNone```")
        await self.bot.say("```python\n{}```".format(serv))

    @_starboard_debug.command(name='isblacklisted', pass_context=True)
    async def _starboard_isblacklisted(self, ctx, user: discord.User, serverid: int = None):
        """
        Returns a bool value of whether or not the specified user is blacklisted in the server specified
        """
        if ctx.message.channel.is_private and not serverid:
            await self.bot.say("Run this command with a server ID or in the server you want to check in")
            return
        server = ctx.message.server if not ctx.message.channel.is_private else None
        if serverid:
            server = self.bot.get_server(str(serverid))
        if server is None:
            await self.bot.say("That server doesn't exist")
            return
        bl = await self.is_blacklisted(user, server)
        await self.bot.say(str(bl))

    #######################################################################
    #                             LISTENERS                               #
    #######################################################################

    async def handle_reaction(self, reaction, user, act: bool):
        msg = reaction.message
        if (user.id == self.bot.user.id) or (msg.channel.is_private):
            return  # Ignore stars by the bot or in private channels
        server = msg.server
        serv = db.servers.find_one({'server_id': server.id})
        if not serv or 'starboard' not in serv or not serv['starboard']:
            return
        starboard = server.get_channel(serv['starboard'])
        if not starboard:
            return
        if msg.channel.id == starboard.id:
            if not msg.embeds or len(msg.embeds) == 0:
                return
            embed = msg.embeds[0]
            if "footer" not in embed or "text" not in embed["footer"]:
                return
            mid = embed["footer"]["text"]
            star = db.stars.find_one({"message_id": str(mid)})
            if not star:
                return
            if "channel_id" not in star or not star["channel_id"]:
                return
            try:
                msg = await self.bot.get_message(server.get_channel(star["channel_id"]), str(mid))
            except discord.NotFound:
                return
            # Refuse to act on messages outside of the current server
            if msg.server.id != reaction.message.server.id:
                return
        if reaction.emoji == "🚫":
            return await self.handle_remove_reaction(reaction, user, msg)
        if user.id == msg.author.id and ('selfstar' not in serv or not serv['selfstar']) and act is True:
            # Remove the reaction if we have permissions
            try:
                await self.bot.remove_reaction(reaction.message, "⭐", user)
            except discord.Forbidden:
                pass
            # Don't add/remove the star
            return
        if act is True:
            await self.add_star(msg, user)
        else:
            await self.remove_star(msg, user)

    async def handle_remove_reaction(self, reaction, user, message):
        if not await self.is_mod(user, reaction.message.server):
            return  # Ignore attempted removals by non-moderators
        if await self.is_blacklisted(user, reaction.message.server):
            return  # Ignore blacklisted moderators
        await self.remove_starboard_msg(message.id)
        await self.mod_log_remove(message.server, user, message)

    async def react_star_add(self, reaction, user):
        if reaction.emoji != "⭐" and reaction.emoji != "🚫":
            return  # Ignore the reaction if it isn't a star or a remove reaction
        await self.handle_reaction(reaction, user, True)

    async def react_star_rem(self, reaction, user):
        if reaction.emoji != "⭐":
            return  # Ignore the reaction if it isn't a star
        await self.handle_reaction(reaction, user, False)

    #######################################################################
    #                            EVENT LOOP                               #
    #######################################################################

    async def starboard_queue_loop(self):
        while self == self.bot.get_cog('Starboard'):
            if len(self.queue) > 0:
                # Copy and clear the queue
                queue = self.queue.copy()
                self.queue = {}
                # Slowly work through the queue
                for mid in queue:
                    item = queue[mid]
                    channel = item["channel"]
                    stars = item["stars"]
                    message = item["message"]

                    content = "{} **{}** {}".format(
                        item["emoji"], stars, channel.mention)
                    if stars < item["server"]["min_stars"]:
                        if item["starboard"].author.id == self.bot.user.id:
                            try:
                                await self.bot.delete_message(item["starboard"])
                            except discord.NotFound:
                                pass
                        continue
                    try:
                        await self.bot.edit_message(item["starboard"],
                                                    new_content=content,
                                                    embed=item["embed"])
                    except:
                        pass
                    await asyncio.sleep(1.5)
            # TODO: Add a way for the bot owner to specify this delay,
            # Or be able to disable it entirely
            await asyncio.sleep(15)


def setup(bot):
    cog = Starboard(bot)
    bot.add_listener(cog.react_star_add, "on_reaction_add")
    bot.add_listener(cog.react_star_rem, "on_reaction_remove")
    bot.loop.create_task(cog.starboard_queue_loop())
    bot.add_cog(cog)
