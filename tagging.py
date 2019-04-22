import discord
from discord.ext import commands
from tinydb import TinyDB, Query
import modules.reactionscroll as rs

# Broken right now. Fix for rewrite.
class TaggingScrollable(rs.Scrollable):
    async def preprocess(self, client, module_db):
        fallback_users = {}
        ret = []
        for item in module_db:
            owner = discord.utils.get(client.get_all_members(), id=item['userid'])
            if not owner:
                # First try getting from caching dict
                try:
                    owner = fallback_users[item['userid']]
                except KeyError:
                    # If we can't find it, then use the slow fetch.
                    owner = await client.get_user_info(item['userid'])
                    fallback_users[item['userid']] = owner
                if not owner:
                    ret.append([item['tag'], "N/A"])
            ret.append([item['tag'], owner.name])
        return ret

    async def refresh(self, client, module_db):
        self.processed_data.clear()
        self.embeds.clear()
        self.processed_data = await self.preprocess(client, module_db)
        self.create_embeds()


class Tagging(commands.Cog):
    protected_names = ['new', 'edit', 'remove', 'owner']

    def __init__(self, bot):
        self.version = "2.0.0"
        self.bot = bot
        self.db = TinyDB('./modules/databases/tagging')
        self.scroll = TaggingScrollable(limit=6, color=0xc0fefe, table=self.db, title="List of tags", inline=True)

    @commands.command()
    async def tag(self, ctx, action: str, name: str, *, content: str):
        target = Query()
        # await self.scroll.refresh()

        if action == "new":
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

        elif action == "edit":
            if self.db.get(target.tag == name)['userid'] != ctx.author.id:
                await ctx.send("[!] You do not have permission to edit this.")
                return
            if self.db.get(target.tag == name) is None:
                await ctx.send("[!] The tag doesn't exist.")
                return
            self.db.update({'content': content}, target.tag == name)
            await ctx.send("[:ok_hand:] Tag updated.")
            return

        elif action == "remove":
            if self.db.get(target.tag == name)['userid'] != ctx.author.id:
                await ctx.send("[!] You do not have permission to edit this.")
                return
            if self.db.get(target.tag == name) is None:
                await ctx.send("[!] The tag doesn't exist.")
                return
            self.db.remove(target.tag == name)
            await ctx.send("[:ok_hand:] Tag removed.")
            return

        elif action == "owner":
            if self.db.get(target.tag == name) is None:
                await ctx.send("[!] The tag doesn't exist.")
                return
            owner_name = str(ctx.bot.get_user(self.db.get(target.tag == name)))
            await ctx.send_message("This tag was created by: **{}**".format(owner_name))
        else:
            if self.db.get(target.tag == name) is None:
                await ctx.send("[!] This tag does not exist.")
                return
            await ctx.send(self.db.get(target.tag == name)['content'])
            return
