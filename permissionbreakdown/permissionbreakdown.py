import discord
from discord.ext import commands
from .utils.chat_formatting import *
import os
from __main__ import send_cmd_help
from math import ceil
from cogs.utils.dataIO import dataIO
from __main__ import settings
from urllib.parse import urlparse
import datetime

class PermissionsBreakdown:
    """Get a breakdown of a user's permissions, including channel overwrites"""

    def __init__(self, bot):
        self.bot = bot
        self.permission_dict = {
            "administrator": "Administrator",
            "view_audit_logs": "View Audit Logs",
            "manage_roles": "Manage Roles",
            "manage_server": "Manage Server",
            "manage_emojis": "Manage Emojis",
            "manage_webhooks": "Manage Webhooks",
            "manage_channels": "Manage Channels",
            "manage_messages": "Manage Messages",
            "manage_nicknames": "Manage Nicknames",
            "read_messages": "Read Messages",
            "read_message_history": "Read Message History",
            "send_messages": "Send Messages",
            "send_tts_messages": "Send TTS Messages",
            "create_instant_invite": "Create Instant Invite",
            "move_members": "Move Members",
            "mention_everyone": "Mass Mention",
            "ban_members": "Ban Members",
            "kick_members": "Kick Members",
            "deafen_members": "Voice Deafen Others",
            "mute_members": "Voice Mute Others",
            "use_voice_activation": "Use Voice Activation",
            "embed_links": "Embed Links",
            "attach_files": "Attach Files",
            "speak": "Speak in Voice",
            "connect": "Connect to Voice",
            "external_emojis": "Use External Emoji",
            "change_nickname": "Change Nickname",
            "add_reactions": "Add Reactions"
        }

    async def get_overwrite(self, channel : discord.Channel = None, role_or_user = None, permission = None):
        # The channel variable is optional simply because I'm too lazy to care
        # And because it was the easiest way to get this working in the intended way
        if channel is None or role_or_user is None:
            return None
        if permission is None:
            return channel.overwrites_for(role_or_user)
        # return discord.utils.find(lambda perm: perm == permission, channel.overwrites_for(role_or_user))
        for perm, overwrite in channel.overwrites_for(role_or_user):
            if perm == permission:
                return overwrite

    @commands.command(name="permissionbreakdown", aliases=["permissions", "perms"], pass_context=True)
    async def _permissionbreakdown(self, ctx, user: discord.User = None, channel: discord.Channel = None, page: int = 1):
        """Returns a breakdown of your (or the specified user)'s permissions.

        This is based off of the user's roles, and optionally also channel overwrites.

        If a channel is provided, it's overwrites will be factored in
        Otherwise, the server permissions will be used instead"""

        if not user: # default to the message author
            user = ctx.message.author

        color = discord.Colour.grey() if not user.color else user.color

        # Check if the user is the server owner
        if int(user.id) == int(ctx.message.server.owner.id):
            msg = discord.Embed(description="{} is the Server Owner, and thus has all permissions by default".format(user.display_name), color=color)
            if user.avatar_url:
                msg.set_author(name="Permissions for {}".format(user.display_name), icon_url=user.avatar_url)
            else:
                msg.set_author(name="Permissions for {}".format(user.display_name))
            return await self.bot.say(embed=msg)

        # Check for Administrator permissions
        if ctx.message.server.default_channel.permissions_for(user).administrator is True:
            msg = discord.Embed(description="{} has the Administrator permission, and thus has all permissions by default".format(user.display_name), color=color)
            if user.avatar_url:
                msg.set_author(name="Permissions for {}".format(user.display_name), icon_url=user.avatar_url)
            else:
                msg.set_author(name="Permissions for {}".format(user.display_name))
            return await self.bot.say(embed=msg)

        # Raw permission data
        permissions = {}

        # Permissions granted to @everyone
        everyone_permissions = []
        # Channel overwrites
        channel_permissions = {
            "grant": [],
            "revoke": []
        }
        # Role permissions
        role_permissions = {}
        # Avoid showing permissions more than twice
        shown_permissions = []

        # I'm not sure how the following works; but somehow it does

        # Get the user's role permissions
        for role in user.roles:
            roleperms = role.permissions
            for perm, grants in roleperms:
                # Check if we have the permission in our perms dataset
                if perm not in permissions:
                    permissions[perm] = {
                        "granted": False,
                        "roles": [],
                        # channelOverwrite is for per-user channel overwrites
                        "channelOverwrite": None,
                        # roleOverwrite is used for channel role overwrites
                        # Currently, this isn't displayed anywhere
                        "roleOverwrite": None
                    }
                # Check if the role actually has this permission in the channel
                cr = await self.get_overwrite(channel, role, perm)
                # Check if the permission is granted by the channel for this role
                if cr is True:
                    permissions[perm]["granted"] = True
                    permissions[perm]["roleOverwrite"] = True
                    permissions[perm]["roles"].append(role.name)
                    continue
                # Check if the permission is already denied by a role
                if permissions[perm]["roleOverwrite"] is False:
                    continue
                # Check if the permission is denied by the channel for this role
                if cr is False and permissions[perm]["roleOverwrite"] is not True:
                    permissions[perm]["granted"] = False
                    permissions[perm]["roleOverwrite"] = False
                    permissions[perm]["roles"] = []
                    continue
                # Lastly, check if the permission is granted by the server
                if grants is True:
                    permissions[perm]["granted"] = True
                    permissions[perm]["roles"].append(role.name)

        if channel is not None:
            # Get the user's channel overwrite permissions
            for overwrite, grants in await self.get_overwrite(channel, user):
                if permissions[overwrite]["roleOverwrite"] is True:
                    continue
                permissions[overwrite]["channelOverwrite"] = grants

        for perm in permissions:
            breakdown = permissions[perm]
            # Try to get a friendly name
            friendly_name = perm
            if perm in self.permission_dict:
                friendly_name = self.permission_dict[perm]
            # Check channel overwrites
            if breakdown["channelOverwrite"] == False:
                channel_permissions["revoke"].append(friendly_name)
                continue
            elif breakdown["channelOverwrite"] == True:
                channel_permissions["grant"].append(friendly_name)
                continue
            # Check if the everyone role has the permission
            if "@everyone" in breakdown["roles"]:
                everyone_permissions.append(friendly_name)
                continue
            # Check roles
            for r in breakdown["roles"]:
                if perm in shown_permissions:
                    continue
                shown_permissions.append(perm)
                if r not in role_permissions:
                    role_permissions[r] = []
                role_permissions[r].append(friendly_name)

        # Build the message
        desc = "Displaying server permissions"
        if channel is not None:
            desc = "Displaying permissions for channel {}".format(channel.mention)
        msg = discord.Embed(description=desc, color=color)
        if user.avatar_url:
            msg.set_author(name="Permissions for {}".format(user.display_name), icon_url=user.avatar_url)
        else:
            msg.set_author(name="Permissions for {}".format(user.display_name))

        default_perms_txt = "These are permissions that everyone has by default\n```{}```".format(", ".join(everyone_permissions).rstrip())

        if len(everyone_permissions) > 0:
            msg.add_field(inline=False, name="Default Permissions", value=default_perms_txt)
        if len(channel_permissions["grant"]) > 0:
            msg.add_field(inline=False, name="Granted in Channel", value="These are permissions granted to **{}** in this channel\n```{}```".format(user.display_name, ", ".join(channel_permissions["grant"]).rstrip()))
        if len(channel_permissions["revoke"]) > 0:
            msg.add_field(inline=False, name="Denied in Channel", value="These are permissions denied from **{}** in this channel\n```{}```".format(user.display_name, ", ".join(channel_permissions["revoke"]).rstrip()))

        added_roles = 0
        skip = (page - 1) * 4
        for role in role_permissions:
            if skip > 0:
                skip = skip - 1
                continue
            if added_roles >= 4:
                break
            msg.add_field(inline=False, name="Role: `{}`".format(role), value="```{}```".format(", ".join(role_permissions[role]).rstrip()))
            added_roles = added_roles + 1

        if len(role_permissions) > 4:
            embed.set_footer(text="Page {} out of {}".format(page, ceil(len(role_permissions) / 4)))

        await self.bot.say(embed=msg)


def setup(bot):
    bot.add_cog(PermissionsBreakdown(bot))
