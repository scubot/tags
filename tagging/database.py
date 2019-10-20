"""Database abstraction module for Scubot Tagging Cog."""
import abc
import typing

import tinydb


class Tag(typing.NamedTuple):
    """Represents a Scubot Tag."""
    name: str
    content: str
    owner: int


class DAO(abc.ABC):
    """Database Abstraction Object interface."""
    def get_contents(self, name: str) -> str:
        """Get the content associated with a given tag name.

        Args:
            name: the name of the tag.

        Returns:
            The contents of the tag.

        Raises:
            KeyError: if no tag with the given name exists.
        """
        return self.get_tag(name).content

    @abc.abstractmethod
    def get_tag(self, name: str) -> 'Tag':
        """Get the content associated with a given tag name.

        Args:
            name: the name of the tag.

        Returns:
            The complete Tag object.

        Raises:
            KeyError: if no tag with the given name exists.
        """

    @abc.abstractmethod
    def create_tag(self, name: str, contents: str, user_id: int) -> None:
        """Create a tag with the given name and contents.

        Args:
            name: the string that will be used to look up the tag.
            contents: the contents of the tag.
            user_id: the id of the user requesting this change.

        Returns:
            None

        Raises:
            KeyError: if a tag with the given name already exists.
            ValueError: if no content has been supplied (empty tags are forbidden).
        """

    @abc.abstractmethod
    def update_tag(self, name: str, contents: str, user_id: int) -> None:
        """Update tag to the given contents.

        This update will only succeed if the given user has permission to update the tag.

        Args:
            name: the string that identifies the tag.
            contents: the new contents of the tag.
            user_id: the id of the user requesting the change.

        Returns:
            None

        Raises:
            PermissionError: if user_id does not have permission to make this change.
            KeyError: if no tag with the given name exists.
            ValueError: if no content has been supplied (empty tags are forbidden).
        """

    @abc.abstractmethod
    def delete_tag(self, name: str, user_id: int) -> None:
        """Delete the tag with the given name.

        This will only succeed if the given user has permission to delete the tag.

        Args:
            name: the string that identifies the tag.
            user_id: the id of the user requesting the deletion.

        Returns:
            None

        Raises:
            PermissionError: if user_id does not have permission to make this change.
            KeyError: if no tag with the given name exists.
        """


class TinyDbDao(DAO):
    """DAO using a TinyDB backend."""
    def __init__(self, database: tinydb.TinyDB):
        """DAO Constructor using a TinyDB backend.

        Args:
            database: TinyDB instance.
        """
        self.database = database

    def get_tag(self, name: str) -> 'Tag':
        """Gets tag from TinyDB backend."""
        target = tinydb.Query()
        raw = self.database.get(target.tag == name)
        if not raw:
            raise KeyError('No such tag exists.')
        return Tag(name=raw['tag'], content=raw['content'], owner=raw['userid'])

    def create_tag(self, name: str, contents: str, user_id: int) -> None:
        """Creates tag in TinyDB backend."""
        if not contents:
            raise ValueError('No content specified.')
        if self.get_tag(name):
            raise KeyError('This tag already exists.')

        self.database.insert({
            'userid': user_id,
            'tag': name,
            'content': contents
        })

    def update_tag(self, name: str, contents: str, user_id: int) -> None:
        """Updates a tag in TinyDB backend."""
        if not contents:
            raise ValueError('No content specified.')
        tag = self.get_tag(name)
        if not tag:
            raise KeyError('No such tag exists.')
        if tag.owner != user_id:
            raise PermissionError('Only the owner may update a tag.')

        target = tinydb.Query()
        self.database.update({'content': contents}, target.tag == name)

    def delete_tag(self, name, user_id) -> None:
        """Deletes a tag in TinyDB backend."""
        tag = self.get_tag(name)
        if not tag:
            raise KeyError('No such tag exists.')
        if tag.owner != user_id:
            raise PermissionError('Only the owner may delete a tag.')

        target = tinydb.Query()
        self.database.remove(target.tag == name)
