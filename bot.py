import os
import sys
import json
import discord
import logging
import importlib
import traceback


BOTNAME = "Kyoko Kirigiri Bot"
MAINCOLOR = 0x962fa4
PREFIX = "!"
PATH = os.path.dirname(os.path.abspath(__file__))


# Functions that are used while initialization
def get_file(filename, path = PATH):
    """
    Get given filename from the path. it uses os.path.join() to combine the path
    and filename so You can give another path to explore different folders.
    In default, path argument is set to the directory where this source code
    exists.
    If the given filename doesn't exist, It will ask you to make one.
    """
    filepath = os.path.join(path, filename)
    logger.info(f"Getting {filepath}...")
    try:
        with open(filepath) as f:
            res = f.read()
    except:
        logger.warn(f"{filepath} does not exist. Creating new one...")
        res = input(f"Input the right value for {filename}: ")
        with open(filepath, "w") as f:
            f.write(res)
        logger.info(f"Succesfully Created {filepath}.")
    return res

def get_json(filename, path = PATH):
    """
    Get given filename from the path, parse it using json.load() and return it.
    it uses os.path.join() to combine the path and filename so You can give
    another path to explore different folders.
    In default, path argument is set to the directory where this source code
    exists.
    If the given filename doesn't exist, It will return the empty dictionary.
    """
    filepath = os.path.join(path, filename)
    logger.info(f"Getting {filepath}...")
    try:
        with open(filepath) as f:
            res = json.load(f)
    except:
        logger.warn(f"{filepath} does not exist. Returning the empty dict.")
        res = {}
    return res

def set_perm(filename = "bot_perm", path = PATH):
    """
    This function sets bot_perm file if it doesn't exist, It needs it's own fun-
    ction to set it because it is a JSON format.
    It requires user to input owner's discord user ID, that's pretty much all.
    """
    filepath = os.path.join(path, filename)
    logger.info(f"Setting {filepath}...")
    # It will keep looping in there if user inputs wrong value, cause int()
    # function to raise an error.
    while True:
        try:
            ownerid = int(input("Input the userid of the bot's owner - \
it should be an integer.: "))
            break
        except ValueError:
            print("Error: Ownerid should only contain integer value.")
            continue
    permdict = {
        "ownerid": ownerid,
        "command": {},
        "user": {}
    }
    with open(filepath, "w") as f:
        json.dump(permdict, f)
    return permdict


# functions that are used in runtime code. It is coroutine function to not block
# the bot's operation, and to call other coroutine functions in this function.
async def get_embed(cmd, desc, sender, colour = MAINCOLOR):
    """
    This will generate the Embed object using the given data.
    This will set title to the cmd argument, but with capitalized and "_" being
    replaced to " ".
    This will set Description to the desc argument.
    This will set color to the colour argument.
    This will set footer to "Requested by **{username}**" or
    "Requested by **{display_name}({username})". if they are different.
    This will set footer icon to the requested user's icon.
    """
    embed = discord.Embed(
        title = cmd.replace("_", "").capitalize(),
        description = desc,
        colour = colour
    )
    username = str(sender)
    displayname = sender.display_name
    if username == displayname:
        printname = username
    else:
        printname = f"{displayname}({username})"
    usericon = sender.avatar_url
    embed.set_footer(
        text = f"Requested by {printname}",
        icon_url = usericon
    )
    return embed

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

async def edit_msg(message, content):
    """
    This will edit the given message, but it will check the type of
    content argument and act differently.
    If it is str, it will edit the message normally.
    If it is discord.Embed, It will edit the message using the embed parameter.
    If it is discord.File, It will remove the message and send the message to
    the channel that original message was sent using the file parameter.
    """
    if type(content) == str:
        return await message.edit(content)
    elif type(content) == discord.Embed:
        return await message.edit(embed = content)
    elif type(content) == discord.File:
        return await message.channel.send(file = content)

# Logging part, This logs at both console window and discordbot.log file
log_formatter = logging.Formatter(
    "%(asctime)s|[%(levelname)s](%(funcName)s): %(message)s",
    "%Y/%m/%d %H:%M:%S"
)
logger = logging.getLogger()
logger.setLevel(logging.INFO)

file_handler = logging.FileHandler(os.path.join(PATH, "discordbot.log"))
file_handler.setFormatter(log_formatter)
logger.addHandler(file_handler)

console_handler = logging.StreamHandler()
console_handler.setFormatter(log_formatter)
logger.addHandler(console_handler)

logger.info("\n====================Starting...====================\n")


token = get_file("discord_token")
sv_prefix = get_json("bot_prefix")
sv_perm = get_json("bot_perm")
if not sv_perm:
    sv_perm = set_perm()
client = discord.Client()


@client.event
async def on_ready():
    logger.info('Succesfully logged in as {0.user}!'.format(client))
    activity = discord.Game("재미있는 코드 갈아엎기")
    await client.change_presence(activity = activity)

@client.event
async def on_message(message):
    """
    Gets prefix from the server, check if command exists, check permission of
    the user, and finally run it.
    It won't do anything if message.author is client.user.
    it contains the code for permission/prefix.
    """
    if message.author == client.user:
        return
    # Get prefix from sv_prefix dict. if KeyError happens, load default prefix.
    try:
        prefix = sv_prefix[str(message.guild.id)]
    except KeyError:
        prefix = PREFIX
    
    if message.content == "?prefix":
        embed = await get_embed(
            "prefix",
            f"Prefix used by this server is `{prefix}`.",
            message.author
        )
        await send_msg(message.channel, embed)

@client.event
async def on_error(event, *args, **kwargs):
    """
    If event is on_message, get Traceback information and send it to the channel
    , also log it using traceback.format_exc().
    else, raise the exception again.
    """
    if event == "on_message":
        message = args[0]
        exc = sys.exc_info()
        excname = exc[0].__name__
        excarglist = [str(x) for x in exc[1].args]
        if not excarglist:
            tbtxt = excname
        else:
            tbtxt = excname + ": " + ", ".join(excarglist)
        tb = traceback.format_exc()
        logger.error(tb)
        embed = discord.Embed(
            title = "An error has been occured while running the task.",
            description = f"```{tbtxt}```",
            color = 0xff0000
        )
        await message.channel.send(embed = embed)
    else:
        raise


client.run(token)