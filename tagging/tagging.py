"""Tagging module for Scubot."""
from discord.ext import commands
import reactionscroll as rs
import tinydb

from tagging import database


class Tagging(commands.Cog):
    """Tagging Cog for Scubot."""
    PROTECTED_NAMES = ['new', 'edit', 'remove', 'owner']

    def __init__(self,
                 bot: commands.Bot,
                 scroll_builder: rs.ScrollViewBuilder,
                 dao: database.DAO):
        """Constructor for tagging module.

        Args:
            bot: Discord bot to which the cog will be attached.
            scroll_builder: The builder used to create Scrollable Embeds.
            database: DAO for the tagging database.
        """
        self.version = "2.0.0"
        self.bot = bot
        self.scroll_builder = scroll_builder
        self.dao = dao

    @commands.group(invoke_without_command=True)
    async def tag(self, ctx, name: str):
        """Print the contents of a given tag."""
        try:
            await ctx.send(self.dao.get_contents(name))
        except KeyError:
            await ctx.send("[!] This tag does not exist.")

    @tag.command(name="new")
    async def new(self, ctx, name: str, *, content: str):
        """Create a new tag."""
        if name in self.PROTECTED_NAMES:
            await ctx.send("[!] The tag you are trying to create is a protected name.")
            return
        try:
            self.dao.create_tag(name, content, ctx.author.id)
            await ctx.send("[:ok_hand:] Tag added.")
        except KeyError:
            await ctx.send("[!] This tag already exists.")
        except ValueError:
            await ctx.send("[!] No content specified?")

    @tag.command(name="edit")
    async def edit(self, ctx, name: str, *, content: str):
        """Replace contents of tag."""
        try:
            self.dao.update_tag(name, content, ctx.author.id)
            await ctx.send("[:ok_hand:] Tag updated.")
        except PermissionError:
            await ctx.send("[!] You do not have permission to edit this.")
        except KeyError:
            await ctx.send("[!] The tag doesn't exist.")
        except ValueError:
            await ctx.send("[!] No content specified?")

    @tag.command(name="remove")
    async def remove(self, ctx, name: str):
        """Delete a tag having a given name."""
        try:
            self.dao.delete_tag(name, ctx.author.id)
            await ctx.send("[:ok_hand:] Tag removed.")
        except PermissionError:
            await ctx.send("[!] You do not have permission to do this.")
        except KeyError:
            await ctx.send("[!] The tag doesn't exist.")

    @tag.command(name="owner")
    async def owner(self, ctx, name: str):
        """Print the owner of a given tag."""
        try:
            tag = self.dao.get_tag(name)
            owner = ctx.bot.get_user(tag.owner)
            if not owner:
                await ctx.send("[!] Owner has left discord.")
                return
            await ctx.send("This tag was created by: **{}**".format(str(owner)))
        except KeyError:
            await ctx.send("[!] The tag doesn't exist.")

    @tag.command(name="list")
    async def list(self, ctx):
        """Create a scrollable list of all tags."""


def setup(bot):
    """API endpoint that allows the module to be loaded dynamically."""
    scroll_builder = rs.ScrollViewBuilder(
        bot=bot,
        color=0xc0fefe,
        title="List of tags",
        inline=True)
    dao = database.TinyDbDao(tinydb.TinyDB('./modules/databases/tagging'))
    bot.add_cog(Tagging(bot, scroll_builder, dao))
