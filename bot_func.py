import os
import json
import discord
import logging
import aiofiles

logger = logging.getLogger()

class Bot:
    @classmethod
    def set_statics(cls, statics):
        """
        This is like __init__.
        Get statics from the main code, save it to global variables
        This happened for the sake of comportability, they are statics after all
        """
        cls.path, cls.botname, cls.maincolor, cls.prefix, cls.ownerid = [
            statics[x] for x in statics
        ]
    
    # Functions that are used in initialization, but also can be used in modules
    @classmethod
    def get_file(cls, filename, path = None):
        """
        Get given filename from the path. it uses os.path.join() to combine the 
        path and filename so You can give another path to explore different
        folders. In default, path argument is set to the directory where this
        source code exists. If the given filename doesn't exist, It will ask you
        to make one.
        """
        if path is None:
            path = cls.path
        filepath = os.path.join(path, filename)
        logger.info(f"Getting {filepath}...")
        try:
            with open(filepath) as f:
                res = f.read()
        except:
            logger.warning(f"{filepath} does not exist. Creating new one...")
            res = input(f"Input the right value for {filename}: ")
            with open(filepath, "w") as f:
                f.write(res)
            logger.info(f"Succesfully Created {filepath}.")
        return res
    
    @classmethod
    def get_json(cls, filename, path = None):
        """
        Get given filename from the path, parse it using json.load() and return it.
        it uses os.path.join() to combine the path and filename so You can give
        another path to explore different folders.
        In default, path argument is set to the directory where this source code
        exists.
        If the given filename doesn't exist, It will return the empty dictionary.
        """
        if path is None:
            path = cls.path
        filepath = os.path.join(path, filename)
        logger.info(f"Getting {filepath}...")
        try:
            with open(filepath) as f:
                res = json.load(f)
        except:
            logger.warning(f"{filepath} does not exist. Returning the empty dict.")
            res = {}
        return res
    
    # functions that are used in runtime code. It is coroutine function to not
    # block the bot's operation, and to call other coroutine functions in these
    # functions.

    @classmethod
    async def get_user_perm(cls, user, guild, sv_perm):
        """
        Get user's permission for this server. if user is owner, return 1.
        If not present, return 5
        """
        if user.id == cls.ownerid:
            return 1
        elif user.id == guild.owner_id:
            return 2
        else:
            try:
                return sv_perm['user'][str(guild.id)][str(user.id)]
            except KeyError:
                return 5
    
    @staticmethod
    async def get_module_perm(module, guild, sv_perm):
        """
        Get the module's permission for this server. If not present, return 5
        """
        try:
            return sv_perm['command'][str(guild.id)][module.__name__.split(
                ".")[1]]
        except KeyError:
            logger.warning(f"Permission of command {module.__name__} for server\
 {str(guild.id)} is not present.")
            return module.PERMISSION
    
    @classmethod
    async def get_embed(cls, title, desc, sender, colour = None, **kwargs):
        """
        This will generate the Embed object using the given data.
        This will set title to the cmd argument, but with capitalized and "_"
        being replaced to " ". This will set Description to the desc argument.
        This will set color to the colour argument. If not present, This will
        use the default one that is specified in config.
        This will set footer to "Requested by **{username}**" or
        "Requested by **{display_name}({username})". if they are different.
        This will set footer icon to the requested user's icon.
        If you wish to set something else, just pass it to the function like
        using discord.Embed method as we will pass the keyword arguments to
        discord.Embed method when generating one.(avoid title, description,
        colour keywords as we already passed that keywords.)
        We might add more for the sake of flexibility, but for now I think this
        is enough as You can set keyword arguments.
        """

        if colour is None:
            colour = cls.maincolor
        embed = discord.Embed(
            title = title.replace("_", "").capitalize(),
            description = desc,
            colour = colour,
            **kwargs
        )
        username = str(sender)
        displayname = sender.display_name
        if sender.name == displayname:
            printname = username
        else:
            printname = f"{displayname}({username})"
        usericon = sender.avatar_url
        embed.set_footer(
            text = f"Requested by {printname}",
            icon_url = usericon
        )
        return embed

    @classmethod
    async def json_dump(cls, savedict, filename, path = None):
        """
        It basically dumps the json to the given filename. it calls json.dumps()
        so it works identically with json.dumps method, but it will load file
        itself.
        """
        if path == None:
            path = cls.path
        async with aiofiles.open(os.path.join(path, filename), 'w') as f:
            await f.write(json.dumps(savedict))

    @staticmethod
    async def send_msg(channel, content):
        """
        This will send message to the given channel, but it will check the type of
        content argument and act differently.
        If it is str, it will send the message normally.
        If it is discord.Embed, It will send the message using the embed parameter.
        If it is discord.File, It will send the message using the file parameter.
        """
        if type(content) == str:
            return await channel.send(content)
        elif type(content) == discord.Embed:
            return await channel.send(embed = content)
        elif type(content) == discord.File:
            return await channel.send(file = content)
    
    @staticmethod
    async def edit_msg(message, content):
        """
        This will edit the given message, but it will check the type of
        content argument and act differently.
        If it is str, it will edit the message normally.
        If it is discord.Embed, It will edit the message using the embed parameter.
        If it is discord.File, It will send a new message to the channel that
        original message was sent using the file parameter.
        """
        if type(content) == str:
            return await message.edit(content)
        elif type(content) == discord.Embed:
            return await message.edit(embed = content)
        elif type(content) == discord.File:
            return await message.channel.send(file = content)