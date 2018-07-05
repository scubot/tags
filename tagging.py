import discord
from modules.botModule import *
import shlex
import time

class Tagging(BotModule):
    name = 'tagging'

    description = 'Allows for user-defined tags.'

    help_text = '`!tag new [name] [content]` to create a new tag. \n' \
                '`!tag edit [name] [newcontent]` to edit an existing tag. You must be the creator of the tag to edit it.\n' \
                '`!tag remove [name]` to remove a tag. You must be the creator of the tag to remove it.\n' \
                '`!tag owner [name]` to fetch the user who created a tag and is able to make changes to it.\n' \
                '`!tag [name]` to retrieve a tag.' 

    trigger_string = 'tag'

    module_version = '1.0.0'

    listen_for_reaction = False

    protected_names = ['new', 'edit', 'remove', 'owner'] # These are protected names that cannot be used as a tag.

    async def parse_command(self, message, client):
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
            elif msg[1] == "owner":
                if len(msg) != 3:
                    send_msg = "[!] Invalid arguments."
                    await client.send_message(message.channel, send_msg)
                else:
                    tag = self.module_db.get(target.tag == msg[2])
                    if not tag:
                        send_msg = "[!] This tag does not exist."
                        await client.send_message(message.channel, send_msg)
                    else:
                        owner_name = await client.get_user_info(tag['userid']).name
                        send_msg = "[:ok_hand:] This tag was created by: **{}**".format(owner_name)
                        await client.send_message(message.channel, send_msg)
            else:
                msg[1] = msg[1].lower()
                if self.module_db.get(target.tag == msg[1]) is None:
                    send_msg = "[!] This tag does not exist."
                    await client.send_message(message.channel, send_msg)
                else:
                    send_msg = self.module_db.get(target.tag == msg[1])['content']
                    await client.send_message(message.channel, send_msg)
