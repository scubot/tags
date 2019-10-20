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
        await ctx.send(self._get_tag(ctx, name))

    def _get_tag(self, ctx: commands.Context, name: str) -> str:
        """Helper to get the contents of a tag."""
        try:
            return self.dao.get_contents(name)
        except KeyError:
            return "[!] This tag does not exist."

    @tag.command(name="new")
    async def new(self, ctx, name: str, *, content: str):
        """Create a new tag."""
        await ctx.send(self._new_tag(ctx, name, content))

    def _new_tag(self, ctx: commands.Context, name: str, content: str) -> str:
        """Helper to get the creation string for a tag."""
        if name in self.PROTECTED_NAMES:
            return "[!] The tag you are trying to create is a protected name."
        try:
            self.dao.create_tag(name, content, ctx.author.id)
            return "[:ok_hand:] Tag added."
        except KeyError:
            return "[!] This tag already exists."
        except ValueError:
            return "[!] No content specified?"

    @tag.command(name="edit")
    async def edit(self, ctx, name: str, *, content: str):
        """Replace contents of tag."""
        await ctx.send(self._edit_tag(ctx, name, content))

    def _edit_tag(self, ctx: commands.Context, name: str, content: str) -> str:
        """Helper to get the edit string for a given tag."""
        try:
            self.dao.update_tag(name, content, ctx.author.id)
            return "[:ok_hand:] Tag updated."
        except PermissionError:
            return "[!] You do not have permission to edit this."
        except KeyError:
            return "[!] The tag doesn't exist."
        except ValueError:
            return "[!] No content specified?"

    @tag.command(name="remove")
    async def remove(self, ctx, name: str):
        """Delete a tag having a given name."""
        await ctx.send(self._remove_tag(ctx, name))
        
    def _remove_tag(self, ctx: commands.Context, name: str) -> str:
        """Helper to get the removal string for a tag."""
        try:
            self.dao.delete_tag(name, ctx.author.id)
            return "[:ok_hand:] Tag removed."
        except PermissionError:
            return "[!] You do not have permission to do this."
        except KeyError:
            return "[!] The tag doesn't exist."

    @tag.command(name="owner")
    async def owner(self, ctx, name: str):
        """Print the owner of a given tag."""
        await ctx.send(self._tag_owner(ctx, name))

    def _tag_owner(self, ctx: commands.Context, name: str) -> str:
        """Helper to get the owner string for a given tag."""
        try:
            tag = self.dao.get_tag(name)
            owner = ctx.bot.get_user(tag.owner)
            if not owner:
                return "[!] Owner has left discord."
            return "This tag was created by: **{}**".format(str(owner))
        except KeyError:
            return "[!] The tag doesn't exist."

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
