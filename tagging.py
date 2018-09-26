import discord
from modules.botModule import *
import shlex
from tinydb import TinyDB, Query
import time
import modules.reactionscroll as rs
import asyncio


class TaggingScrollable(rs.Scrollable):
    async def preprocess(self, client, module_db):
        ret = []
        for item in module_db:
            owner = discord.utils.get(client.get_all_members(), id=item['userid'])
            if not owner:
                owner = await client.get_user_info(item['userid'])
                if not owner:
                    ret.append([item['tag'], "N/A"])
            ret.append([item['tag'], owner.name])
        return ret

    async def refresh(self, client, module_db):
        self.processed_data.clear()
        self.embeds.clear()
        self.processed_data = await self.preprocess(client, module_db)
        self.create_embeds()


class Tagging(BotModule):
    name = 'tagging'

    description = 'Allows for user-defined tags.'

    help_text = '`!tag new [name] [content]` to create a new tag. \n' \
                '`!tag edit [name] [newcontent]` to edit an existing tag. You must be the creator of the tag to edit it.\n' \
                '`!tag remove [name]` to remove a tag. You must be the creator of the tag to remove it.\n' \
                '`!tag owner [name]` to fetch the user who created a tag and is able to make changes to it.\n' \
                '`!tag [name]` to retrieve a tag.' 

    trigger_string = 'tag'

    module_version = '1.1.0'

    listen_for_reaction = True

    protected_names = ['new', 'edit', 'remove', 'owner', 'list'] # These are protected names that cannot be used as a tag.

    module_db = TinyDB('./modules/databases/' + name)

    message_returns = []

    scroll = TaggingScrollable(limit=6, color=0xc0fefe, table=module_db, title="List of tags", inline=True)

    async def contains_returns(self, message):
        for x in self.message_returns:
            if message.id == x[0].id:
                return True
        return False

    async def find_pos(self, message):
        for x in self.message_returns:
            if message.id == x[0].id:
                return x[1]

    async def update_pos(self, message, ty):
        for x in self.message_returns:
            if message.id == x[0].id:
                if ty == 'next':
                    x[1] += 1
                if ty == 'prev':
                    x[1] -= 1

    async def parse_command(self, message, client):
        self.scroll.refresh(client, self.module_db)
        msg = shlex.split(message.content)
        target = Query()
        if len(msg) > 1:
            if len(msg) > 2:
                msg[2] = msg[2].lower()
            if msg[1] == "new":
                if msg[2] in self.protected_names:
                    send_msg = "[!] The tag you are trying to create is a protected name. Please choose another name."
                    await client.send_message(message.channel, send_msg)
                else:
                    if len(msg) != 4:
                        send_msg = "[!] Invalid arguments."
                        await client.send_message(message.channel, send_msg)
                    else:
                        if self.module_db.get(target.tag == msg[2]) is not None:
                            send_msg = "[!] This tag already exists."
                            await client.send_message(message.channel, send_msg)
                        else:
                            self.module_db.insert({'userid': message.author.id, 'tag': msg[2], 'content': msg[3]})
                            send_msg = "[:ok_hand:] Tag added."
                            await client.send_message(message.channel, send_msg)
            elif msg[1] == "edit":
                if len(msg) != 4:
                    send_msg = "[!] Invalid arguments."
                    await client.send_message(message.channel, send_msg)
                else:
                    if self.module_db.get(target.tag == msg[2])['userid'] != message.author.id:
                        send_msg = "[!] You do not have permission to edit this."
                        await client.send_message(message.channel, send_msg)
                    else:
                        self.module_db.update({'content': msg[3]}, target.tag == msg[2])
                        send_msg = "[:ok_hand:] Tag updated."
                        await client.send_message(message.channel, send_msg)
            elif msg[1] == "remove":
                if len(msg) != 3:
                    send_msg = "[!] Invalid arguments."
                    await client.send_message(message.channel, send_msg)
                else:
                    if self.module_db.get(target.tag == msg[2])['userid'] != message.author.id:
                        send_msg = "[!] You do not have permission to remove this."
                        await client.send_message(message.channel, send_msg)
                    else:
                        self.module_db.remove(target.tag == msg[2])
                        send_msg = "[:ok_hand:] Tag removed."
                        await client.send_message(message.channel, send_msg)
            elif msg[1] == "list": # This is completely untested, plz test before prod
                if len(msg) > 2:
                    send_msg = "[!] Too many arguments"
                    await client.send_message(message.channel, send_msg)
                else:
                    m_ret = await client.send_message(message.channel, embed=self.scroll.initial_embed())
                    self.message_returns.append([m_ret, 0])
                    await client.add_reaction(m_ret, "⏪")
                    await client.add_reaction(m_ret, "⏩")
            elif msg[1] == "owner":
                if len(msg) != 3:
                    send_msg = "[!] Invalid arguments."
                    await client.send_message(message.channel, send_msg)
                else:
                    tag = self.module_db.get(target.tag == msg[2])
                    if tag is None:
                        send_msg = "[!] This tag does not exist."
                        await client.send_message(message.channel, send_msg)
                    else:
                        owner = await client.get_user_info(tag['userid'])
                        send_msg = "This tag was created by: **{}**".format(owner.name)
                        await client.send_message(message.channel, send_msg)
            else:
                msg[1] = msg[1].lower()
                if self.module_db.get(target.tag == msg[1]) is None:
                    send_msg = "[!] This tag does not exist."
                    await client.send_message(message.channel, send_msg)
                else:
                    send_msg = self.module_db.get(target.tag == msg[1])['content']
                    await client.send_message(message.channel, send_msg)

    async def on_reaction_add(self, reaction, client, user):
        if not await self.contains_returns(reaction.message):
            return 0
        pos = await self.find_pos(reaction.message)
        react_text = reaction.emoji
        if type(reaction.emoji) is not str:
            react_text = reaction.emoji.name
        if react_text == "⏩":
            embed = self.scroll.next(current_pos=pos)
            await client.edit_message(reaction.message, embed=embed)
            await self.update_pos(reaction.message, 'next')
        if react_text == "⏪":
            embed = self.scroll.previous(current_pos=pos)
            await client.edit_message(reaction.message, embed=embed)
            await self.update_pos(reaction.message, 'prev')

