from discord.ext import commands
from discord.utils import find

import reactionscroll as rs


class TaggingScrollable(rs.Scrollable):
    async def preprocess(self, bot, db):
        fallback_users = {}
        ret = []
        for item in db:
            owner = find(lambda o: o.id == item['userid'], list(bot.get_all_members()))
            if not owner:
                # First try getting from caching dict
                try:
                    owner = fallback_users[item['userid']]
                except KeyError:
                    # If we can't find it, then use the slow fetch.
                    owner = await bot.fetch_user(item['userid'])
                    fallback_users[item['userid']] = owner
                if not owner:
                    ret.append([item['tag'], "N/A"])
            ret.append([item['tag'], owner.name])
        return ret

    async def refresh(self, bot, db):
        self.processed_data.clear()
        self.embeds.clear()
        self.processed_data = await self.preprocess(bot, db)
        self.create_embeds()


class Tagging(commands.Cog):
    protected_names = ['new', 'edit', 'remove', 'owner']
    scrolling_cache = []

    # Helper functions for scrolling
    async def contains_returns(self, message):
        for x in self.scrolling_cache:
            if message.id == x[0].id:
                return True
        return False

    async def find_pos(self, message):
        for x in self.scrolling_cache:
            if message.id == x[0].id:
                return x[1]

    async def update_pos(self, message, ty):
        for x in self.scrolling_cache:
            if message.id == x[0].id:
                if ty == 'next':
                    x[1] += 1
                if ty == 'prev':
                    x[1] -= 1

    def __init__(self, bot):
        self.version = "2.0.0"
        self.bot = bot
        self.db = TinyDB('./modules/databases/tagging')
        self.scroll = TaggingScrollable(limit=6, color=0xc0fefe, table=self.db, title="List of tags", inline=True)

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
        owner_name = str(ctx.bot.get_user(self.db.get(target.tag == name)))
        await ctx.send_message("This tag was created by: **{}**".format(owner_name))

    @tag.command(name="list")
    async def list(self, ctx):
        await self.scroll.refresh(self.bot, self.db)
        m = await ctx.send(embed=self.scroll.initial_embed())
        self.scrolling_cache.append([m, 0])
        await m.add_reaction("⏪")
        await m.add_reaction("⏩")

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        if not await self.contains_returns(reaction.message):
            return
        pos = await self.find_pos(reaction.message)
        react_text = reaction.emoji
        if type(reaction.emoji) is not str:
            react_text = reaction.emoji.name
        if react_text == "⏩":
            embed = self.scroll.next(current_pos=pos)
            await reaction.message.edit(embed=embed)
            await self.update_pos(reaction.message, 'next')
        if react_text == "⏪":
            embed = self.scroll.previous(current_pos=pos)
            await reaction.message.edit(embed=embed)
            await self.update_pos(reaction.message, 'prev')


def setup(bot):
    bot.add_cog(Tagging(bot))
