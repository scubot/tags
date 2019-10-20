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

class TestTagging:
    def test_remove_nonexistent(self):
        dao = DictDao()
        cog = tagging.Tagging(None, None, dao)

        ctx = Context(None, Member('bob', 0))
        assert cog._remove_tag(ctx, "foo") == "[!] The tag doesn't exist."

    def test_remove_notOwner(self):
        dao = DictDao()
        dao.create_tag('foo', 'bar', 0)

        cog = tagging.Tagging(None, None, dao)
        ctx = Context(None, Member('bob', 1))
        assert cog._get_tag("foo") == "bar"
        assert cog._remove_tag(ctx, "foo") == \
            "[!] You do not have permission to do this."
        assert cog._get_tag("foo") == "bar"

    def test_remove_success(self):
        dao = DictDao()
        dao.create_tag('foo', 'bar', 0)

        cog = tagging.Tagging(None, None, dao)
        ctx = Context(None, Member('bob', 0))
        assert cog._get_tag("foo") == "bar"
        assert cog._remove_tag(ctx, "foo") == "[:ok_hand:] Tag removed."
        assert cog._get_tag("foo") == "[!] This tag does not exist."

    def test_create_empty(self):
        dao = DictDao()
        cog = tagging.Tagging(None, None, dao)

        ctx = Context(None, Member('bob', 0))
        assert cog._new_tag(ctx, "foo", "") == "[!] No content specified?"

    def test_create_duplicate(self):
        dao = DictDao()
        dao.create_tag('foo', 'bar', 0)
        cog = tagging.Tagging(None, None, dao)

        ctx = Context(None, Member('bob', 0))
        assert cog._get_tag("foo") == "bar"
        assert cog._new_tag(ctx, "foo", "baz") == "[!] This tag already exists."
        assert cog._get_tag("foo") == "bar"

    def test_create_protected(self):
        dao = DictDao()
        cog = tagging.Tagging(None, None, dao)

        ctx = Context(None, Member('bob', 0))
        assert cog._new_tag(ctx, "new", "bar") == \
            "[!] The tag you are trying to create is a protected name."
        assert cog._get_tag("new") == "[!] This tag does not exist."
    
    def test_create_success(self):
        dao = DictDao()
        cog = tagging.Tagging(None, None, dao)

        ctx = Context(None, Member('bob', 0))
        assert cog._new_tag(ctx, "foo", "bar") == "[:ok_hand:] Tag added."
        assert cog._get_tag("foo") == "bar"

    def test_get_tag_success(self):
        dao = DictDao()
        dao.create_tag('foo', 'bar', 0)
        cog = tagging.Tagging(None, None, dao)

        ctx = Context(None, Member('bob', 0))
        assert cog._get_tag("foo") == "bar"

    def test_get_tag_nonexistent(self):
        dao = DictDao()
        cog = tagging.Tagging(None, None, dao)

        ctx = Context(None, Member('bob', 0))
        assert cog._get_tag("foo") == "[!] This tag does not exist."

    def test_edit_tag_nonexistent(self):
        dao = DictDao()
        cog = tagging.Tagging(None, None, dao)

        ctx = Context(None, Member('bob', 0))
        assert cog._edit_tag(ctx, "foo", "bar") == "[!] The tag doesn't exist."

    def test_edit_tag_notOwner(self):
        dao = DictDao()
        dao.create_tag('foo', 'bar', 0)
        cog = tagging.Tagging(None, None, dao)

        ctx = Context(None, Member('bob', 1))
        assert cog._edit_tag(ctx, "foo", "baz") == \
            "[!] You do not have permission to edit this."

    def test_edit_tag_empty(self):
        dao = DictDao()
        dao.create_tag('foo', 'bar', 0)
        cog = tagging.Tagging(None, None, dao)

        ctx = Context(None, Member('bob', 0))
        assert cog._edit_tag(ctx, "foo", "") == "[!] No content specified?"

    def test_edit_success(self):
        dao = DictDao()
        dao.create_tag('foo', 'bar', 0)
        cog = tagging.Tagging(None, None, dao)

        ctx = Context(None, Member('bob', 0))
        assert cog._edit_tag(ctx, "foo", "baz") == "[:ok_hand:] Tag updated."
        assert cog._get_tag("foo") == "baz"

    def test_owner_tagNonexistent(self):
        dao = DictDao()
        cog = tagging.Tagging(None, None, dao)

        ctx = Context(Bot('bob'), Member('bob', 0))
        assert cog._tag_owner(ctx, 'foo') == "[!] The tag doesn't exist."

    def test_owner_ownerNonexistent(self):
        dao = DictDao()
        dao.create_tag('foo', 'bar', 0)
        cog = tagging.Tagging(None, None, dao)

        ctx = Context(UserNotFoundBot(), Member('bob', 0))
        assert cog._tag_owner(ctx, 'foo') == "[!] Owner has left discord."

    def test_owner_success(self):
        dao = DictDao()
        dao.create_tag('foo', 'bar', 0)
        cog = tagging.Tagging(None, None, dao)

        ctx = Context(Bot('bob'), Member('bob', 0))
        assert cog._tag_owner(ctx, 'foo') == "This tag was created by: **bob#0000**"
