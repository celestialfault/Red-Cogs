import discord
from discord.ext import commands
import asyncio
from cogs.utils.dataIO import fileIO
from .utils.chat_formatting import *
from .utils import checks
from __main__ import send_cmd_help
import os
import time
from random import choice as randchoice
from random import randint

class Quotes:
    def __init__(self, bot):
        self.bot = bot
        self.quotes = fileIO("data/quotes/quotes.json", "load")

    # stackoverflow:
    # let other people do your work for you[tm]
    # https://stackoverflow.com/a/23148997
    def split_list(self, arr, size):
        arrs = []
        while len(arr) > size:
            pice = arr[:size]
            arrs.append(pice)
            arr  = arr[size:]
        arrs.append(arr)
        return arrs

    def _server_has_quotes(self, server):
        return not (server.id not in self.quotes or len(self.quotes[server.id]) == 0)

    def _get_random_quote(self, server):
        if server.id not in self.quotes or len(self.quotes[server.id]) == 0:
            return False
        _id = randint(0, len(self.quotes[server.id]) - 1)
        return {
            "_id": _id + 1,
            "quote": self.quotes[server.id][_id]
        }

    def _get_quote(self, server, num):
        if server.id not in self.quotes:
            return False
        if num > 0 and num <= len(self.quotes[server.id]) and self.quotes[server.id][num - 1]:
            return self.quotes[server.id][num - 1]
        else:
            return False

    def _add_quote(self, server, message, quoter : str = None):
        if server.id not in self.quotes:
            self.quotes[server.id] = []
        self.quotes[server.id].append(message)
        fileIO("data/quotes/quotes.json", "save", self.quotes)

    def _fmt_quotes(self, server, page : int = 1):
        if page < 1:
            page = 1
        per_page = 10
        data = self.split_list(self.quotes[server.id], per_page)
        if len(data) < page:
            page = len(data)
        ret = discord.Embed(color=discord.Colour.green(), description="Page {} out of {} *({} total quotes)*".format(page, len(data), len(self.quotes[server.id])))
        if server.icon_url:
            ret.set_author(name="Quotes for {}".format(server.name), icon_url=server.icon_url)
        else:
            ret.set_author(name="Quotes for {}".format(server.name))
        # there's probably a better way to do this, but, eh
        # it works; that's good enough for me
        start_from = (per_page * page) - per_page
        for num, quote in enumerate(data[page - 1]):
            # Truncate after 150 characters
            # That way we can reliably fit 10 quotes in a single list message
            if len(quote) > 150:
                quote = quote[:150] + " *(...)*"
            ret.add_field(name="Quote #{}".format(str(num + start_from + 1)), value=quote, inline=False)
        if len(data) > 1:
            ret.set_footer(text="You can view other pages with 'quote list [page]'")
        return ret

    @commands.group(pass_context=True, no_pm=True, name="quote", aliases=["quotes"], invoke_without_command=True)
    async def quote(self, ctx, quote : int = None):
        """Manage and get quotes

        If no subcommand is passed, a random quote is returned"""
        server = ctx.message.server
        if not self._server_has_quotes(server):
            em = discord.Embed(title="Error", description="This server doesn't have any quotes yet!", color=discord.Colour.red())
            await self.bot.say(embed=em)
            return
        if quote is None:
            q = self._get_random_quote(ctx.message.server)
        else:
            q = self._get_quote(ctx.message.server, quote)
            if isinstance(q, str) or not q:
                pass
            else:
                q["quote"] = q
                q["_id"] = quote
        if q == False:
            em = discord.Embed(title="Error", description="That quote doesn't exist", color=discord.Colour.red())
            await self.bot.say(embed=em)
            return
        # Check if the quote returned is a string
        if isinstance(q, str):
            em = discord.Embed(title="Quote #{}".format(quote), description=q, color=discord.Colour.green())
            await self.bot.say(embed=em)
            return
        # handle quote parsing
        em = discord.Embed(title="Quote #{num}".format(num=q["_id"]),
            description=q["quote"],
            color=discord.Colour.green()
        )
        try:
            await self.bot.say(embed=em)
        except:
            await self.bot.say("I don't have permissions to send embeds (I need the `Embed Links` permission)")

    @quote.command(name="add", pass_context=True)
    @checks.mod_or_permissions(manage_messages=True)
    async def quotes_add(self, ctx, *, quote : str):
        """Adds a quote - is that not simple enough?

        Example: [p]quotes add \"Don't trust something you read just because there's a quote next to it\" -Albert Einstein"""
        server = ctx.message.server
        self._add_quote(ctx.message.server, quote)
        try:
            em = discord.Embed(title="Added quote #{num}".format(
                num=len(self.quotes[server.id])),
                description=quote,
                color=discord.Color.green())
            await self.bot.say(embed=em)
        except:
            await self.bot.say("I don't have permissions to send embeds (I need the `Embed Links` permission)")

    @quote.command(name="remove", pass_context=True, aliases=['delete'])
    @checks.mod_or_permissions(manage_messages=True)
    async def quotes_remove(self, ctx, quote : int):
        """Deletes a quote

           Example: [p]quotes remove 3"""
        server = ctx.message.server
        if server.id not in self.quotes:
            await self.bot.say("There are no saved quotes!")
        elif quote > 0 and quote <= len(self.quotes[server.id]):
            quotes = []
            for i in range(len(self.quotes[server.id])):
                if quote - 1 == i:
                    await self.bot.say("Quote number " + str(quote) +
                                       " has been deleted.")
                else:
                    quotes.append(self.quotes[server.id][i])
            self.quotes[server.id] = quotes
            fileIO("data/quotes/quotes.json", "save", self.quotes)
        else:
            await self.bot.say("Quote " + str(quote) + " does not exist.")

    @quote.command(name="list", pass_context=True)
    async def quotes_list(self, ctx, page : int = None):
        """Whispers this server's list of quotes"""
        if ctx.message.server.id not in self.quotes or len(self.quotes[ctx.message.server.id]) < 1:
            try:
                em = discord.Embed(title="Error", description="This server doesn't have any quotes yet!", color=discord.Colour.red())
                await self.bot.say(embed=em)
            except:
                await self.bot.say("I don't have permissions to send embeds (I need the `Embed Links` permission)")
            return
        if page == None:
            page = 1
        try:
            # BUG: This seems to be delayed by about ~3-5 seconds
            await self.bot.whisper(embed=self._fmt_quotes(ctx.message.server, page=page))
        except:
            await self.bot.say("I don't have permissions to send embeds (I need the `Embed Links` permission)")

def check_folder():
    if not os.path.exists("data/quotes"):
        print("Creating data/quotes folder...")
        os.makedirs("data/quotes")

def check_file():
    f = "data/quotes/quotes.json"
    if not fileIO(f, "check"):
        print("Creating default quotes.json...")
        fileIO(f, "save", {})

def setup(bot):
    check_folder()
    check_file()
    n = Quotes(bot)
    bot.add_cog(n)
