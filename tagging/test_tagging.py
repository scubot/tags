"""Unit tests for Scubot Tagging module"""
from tagging import database

from tagging import tagging

class DictDao(database.DAO):
    def __init__(self):
        self.tags = dict()
    
    def get_tag(self, name: str) -> database.Tag:
        return self.tags[name]

    def create_tag(self, name: str, contents: str, user_id: int) -> None:
        if name in self.tags:
            raise KeyError('This tag already exists.')
        if not contents:
            raise ValueError('No content specified.')
        self.tags[name] = database.Tag(name=name, content=contents, owner=user_id)

    def update_tag(self, name: str, contents: str, user_id: int) -> None:
        if name not in self.tags:
            raise KeyError('No tag')
        if not contents:
            raise ValueError('No content')
        if self.tags[name].owner != user_id:
            raise PermissionError('No Permission')

        tag = self.tags[name]
        del self.tags[name]
        self.tags[name] = database.Tag(name=name, content=contents, owner=user_id)

    def delete_tag(self, name: str, user_id: int):
        if name not in self.tags:
            raise KeyError('No tag')
        if self.tags[name].owner != user_id:
            raise PermissionError('No permission')

        del self.tags[name]

class Bot:
    def __init__(self, name):
        self.name = name

    def get_user(self, user_id):
        return Member(self.name, user_id)

class UserNotFoundBot:
    def get_user(self, user_id):
        return None

class Member:
    def __init__(self, name: str, user_id: int):
        self.id = user_id
        self.name = name

    def __str__(self):
        return '{}#{}'.format(self.name, str(self.id).zfill(4))

class Context:
    def __init__(self, bot: Bot, author: Member):
        self.bot = bot
        self.author = author

    async def send(self, content: str):
        self.last_content = content


class TestTagging:
    async def test_remove_nonexistent(self):
        dao = DictDao()
        cog = tagging.Tagging(None, None, dao)

        ctx = Context(None, Member('bob', 0))
        await cog.remove.callback(cog, ctx, "foo")
        assert ctx.last_content == "[!] The tag doesn't exist."

    async def test_remove_notOwner(self):
        dao = DictDao()
        dao.create_tag('foo', 'bar', 0)

        cog = tagging.Tagging(None, None, dao)
        ctx = Context(None, Member('bob', 1))

        await cog.tag.callback(cog, ctx, "foo")
        assert ctx.last_content == "bar"

        await cog.remove.callback(cog, ctx, "foo")
        assert ctx.last_content == "[!] You do not have permission to do this."

        await cog.tag.callback(cog, ctx, "foo")
        assert ctx.last_content == "bar"

    async def test_remove_success(self):
        dao = DictDao()
        dao.create_tag('foo', 'bar', 0)

        cog = tagging.Tagging(None, None, dao)
        ctx = Context(None, Member('bob', 0))

        await cog.tag.callback(cog, ctx, "foo")
        assert ctx.last_content == "bar"

        await cog.remove.callback(cog, ctx, "foo")
        assert ctx.last_content == "[:ok_hand:] Tag removed."

        await cog.tag.callback(cog, ctx, "foo")
        assert ctx.last_content == "[!] This tag does not exist."

    async def test_create_empty(self):
        dao = DictDao()
        cog = tagging.Tagging(None, None, dao)

        ctx = Context(None, Member('bob', 0))

        await cog.new.callback(cog, ctx, "foo", content="")
        assert ctx.last_content == "[!] No content specified?"

        await cog.tag.callback(cog, ctx, "foo")
        assert ctx.last_content == "[!] This tag does not exist."

    async def test_create_duplicate(self):
        dao = DictDao()
        dao.create_tag('foo', 'bar', 0)
        cog = tagging.Tagging(None, None, dao)

        ctx = Context(None, Member('bob', 0))

        await cog.tag.callback(cog, ctx, "foo")
        assert ctx.last_content == "bar"

        await cog.new.callback(cog, ctx, "foo", content="baz")
        assert ctx.last_content == "[!] This tag already exists."

        await cog.tag.callback(cog, ctx, "foo")
        assert ctx.last_content == "bar"

    async def test_create_protected(self):
        dao = DictDao()
        cog = tagging.Tagging(None, None, dao)

        ctx = Context(None, Member('bob', 0))

        await cog.new.callback(cog, ctx, "new", content="bar")
        assert ctx.last_content == \
            "[!] The tag you are trying to create is a protected name."

        await cog.tag.callback(cog, ctx, "new")
        assert ctx.last_content == "[!] This tag does not exist."
    
    async def test_create_success(self):
        dao = DictDao()
        cog = tagging.Tagging(None, None, dao)

        ctx = Context(None, Member('bob', 0))

        await cog.new.callback(cog, ctx, "foo", content="bar")
        assert ctx.last_content == "[:ok_hand:] Tag added."

        await cog.tag.callback(cog, ctx, "foo")
        assert ctx.last_content == "bar"

    async def test_get_tag_success(self):
        dao = DictDao()
        dao.create_tag('foo', 'bar', 0)
        cog = tagging.Tagging(None, None, dao)

        ctx = Context(None, Member('bob', 0))

        await cog.tag.callback(cog, ctx, "foo")
        assert ctx.last_content == "bar"

    async def test_get_tag_nonexistent(self):
        dao = DictDao()
        cog = tagging.Tagging(None, None, dao)

        ctx = Context(None, Member('bob', 0))

        await cog.tag.callback(cog, ctx, "foo")
        assert ctx.last_content == "[!] This tag does not exist."

    async def test_edit_tag_nonexistent(self):
        dao = DictDao()
        cog = tagging.Tagging(None, None, dao)

        ctx = Context(None, Member('bob', 0))

        await cog.edit.callback(cog, ctx, "foo", content="bar")
        assert ctx.last_content == "[!] The tag doesn't exist."

    async def test_edit_tag_notOwner(self):
        dao = DictDao()
        dao.create_tag('foo', 'bar', 0)
        cog = tagging.Tagging(None, None, dao)

        ctx = Context(None, Member('bob', 1))

        await cog.edit.callback(cog, ctx, "foo", content="baz")
        assert ctx.last_content == \
            "[!] You do not have permission to edit this."

        await cog.tag.callback(cog, ctx, "foo")
        assert ctx.last_content == "bar"

    async def test_edit_tag_empty(self):
        dao = DictDao()
        dao.create_tag('foo', 'bar', 0)
        cog = tagging.Tagging(None, None, dao)

        ctx = Context(None, Member('bob', 0))

        await cog.edit.callback(cog, ctx, "foo", content="")
        assert ctx.last_content == "[!] No content specified?"

    async def test_edit_success(self):
        dao = DictDao()
        dao.create_tag('foo', 'bar', 0)
        cog = tagging.Tagging(None, None, dao)

        ctx = Context(None, Member('bob', 0))

        await cog.edit.callback(cog, ctx, "foo", content="baz")
        assert ctx.last_content == "[:ok_hand:] Tag updated."

        await cog.tag.callback(cog, ctx, "foo")
        assert ctx.last_content == "baz"

    async def test_owner_tagNonexistent(self):
        dao = DictDao()
        cog = tagging.Tagging(None, None, dao)

        ctx = Context(Bot('bob'), Member('bob', 0))

        await cog.owner.callback(cog, ctx, "foo")
        assert ctx.last_content == "[!] The tag doesn't exist."

    async def test_owner_ownerNonexistent(self):
        dao = DictDao()
        dao.create_tag('foo', 'bar', 0)
        cog = tagging.Tagging(None, None, dao)

        ctx = Context(UserNotFoundBot(), Member('bob', 0))

        await cog.owner.callback(cog, ctx, "foo")
        assert ctx.last_content == "[!] Owner has left discord."

    async def test_owner_success(self):
        dao = DictDao()
        dao.create_tag('foo', 'bar', 0)
        cog = tagging.Tagging(None, None, dao)

        ctx = Context(Bot('bob'), Member('bob', 0))

        await cog.owner.callback(cog, ctx, "foo")
        assert ctx.last_content == "This tag was created by: **bob#0000**"
