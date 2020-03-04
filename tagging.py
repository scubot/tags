from typing import List

from discord.ext import commands
from discord.utils import find
from tinydb import TinyDB, Query
from modules.dispatch import EmbedChain, EmbedEntry
from util.missingdependency import MissingDependencyException


class Tagging(commands.Cog):
    protected_names = ['new', 'edit', 'remove', 'owner']

    def __init__(self, bot):
        self.version = "3.0.0"
        self.bot = bot
        self.db = TinyDB('./modules/databases/tagging')

    async def make_entries(self) -> List[EmbedEntry]:
        fallback_users = {}
        ret = []
        for item in self.db:
            owner = find(lambda o: o.id == item['userid'], list(self.bot.get_all_members()))
            if not owner:
                # First try getting from caching dict
                try:
                    owner = fallback_users[item['userid']]
                except KeyError:
                    # If we can't find it, then use the slow fetch.
                    owner = await self.bot.fetch_user(item['userid'])
                    fallback_users[item['userid']] = owner
                if not owner:
                    ret.append(EmbedEntry(item['tag'], "N/A"))
            ret.append(EmbedEntry(item['tag'], owner.name))
        return ret

    @commands.group(invoke_without_command=True)
    async def tag(self, ctx, name: str):
        target = Query()
        if self.db.get(target.tag == name) is None:
            await ctx.send("[!] This tag does not exist.")
            return
        await ctx.send(self.db.get(target.tag == name)['content'])
        return

    @tag.command(name="new")
    async def new(self, ctx, name: str, *, content: str):
        target = Query()
        if name in self.protected_names:
            await ctx.send("[!] The tag you are trying to create is a protected name.")
            return
        if not content:
            await ctx.send("[!] No content specified?")
            return
        if self.db.get(target.tag == name) is not None:
            await ctx.send("[!] This tag already exists.")
            return
        self.db.insert({'userid': ctx.author.id, 'tag': name, 'content': content})
        await ctx.send("[:ok_hand:] Tag added.")
        return

    @tag.command(name="edit")
    async def edit(self, ctx, name: str, *, content: str):
        target = Query()
        if self.db.get(target.tag == name)['userid'] != ctx.author.id:
            await ctx.send("[!] You do not have permission to edit this.")
            return
        if self.db.get(target.tag == name) is None:
            await ctx.send("[!] The tag doesn't exist.")
            return
        self.db.update({'content': content}, target.tag == name)
        await ctx.send("[:ok_hand:] Tag updated.")
        return

    @tag.command(name="remove")
    async def remove(self, ctx, name: str):
        target = Query()
        if self.db.get(target.tag == name)['userid'] != ctx.author.id:
            await ctx.send("[!] You do not have permission to edit this.")
            return
        if self.db.get(target.tag == name) is None:
            await ctx.send("[!] The tag doesn't exist.")
            return
        self.db.remove(target.tag == name)
        await ctx.send("[:ok_hand:] Tag removed.")
        return

    @tag.command(name="owner")
    async def owner(self, ctx, name: str):
        target = Query()
        if self.db.get(target.tag == name) is None:
            await ctx.send("[!] The tag doesn't exist.")
            return
        owner_name = str(await self.bot.fetch_user(self.db.get(target.tag == name)['userid']))
        await ctx.send("This tag was created by: **{}**".format(owner_name))

    @tag.command(name="list")
    async def list(self, ctx):
        dispatcher = self.bot.get_cog("Dispatcher")
        if not dispatcher:
            raise MissingDependencyException("Dispatcher")
        embed = EmbedChain(await self.make_entries(), limit=6, color=0xc0fefe, title="List of tags", inline=True)
        await dispatcher.register(await ctx.send(embed=embed.current()), embed)


def setup(bot):
    if not bot.get_cog("Dispatcher"):
        raise MissingDependencyException("Dispatcher")
    bot.add_cog(Tagging(bot))
