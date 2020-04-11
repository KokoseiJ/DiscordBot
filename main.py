import os
import sys
import json
import discord
import logging
import importlib
import traceback
import configparser

# Get path based on the script's location.
PATH = os.path.dirname(os.path.abspath(__file__))

# Read configs
config = configparser.ConfigParser()
# This step is required because I don't prefer headers in my config file and
# configparser will definitely not accept it. This workaround idea is from
# CoupleWavyLines' answer, from stackoverflow question
# 'parsing .properties file in Python': https://stackoverflow.com/a/25493615
try:
    with open(os.path.join(PATH, 'config.ini')) as f:
        config.read_string("[section]\n" + f.read())
except:
    raise FileNotFoundError("Config file is not in the directory.")

BOTNAME = config['section']['BotName']
try:
    MAINCOLOR = int(config['section']['MainColor'], 16)
except ValueError:
    raise ValueError("Value of config entry 'MainColor' is not hexadecimal.")
PREFIX = config['section']['Prefix']
OWNERID = int(config['section']['OwnerId'])
STATICS = {
    "PATH": PATH,
    "PREFIX": PREFIX,
    "MAINCOLOR": MAINCOLOR,
    "BOTNAME": BOTNAME,
    "OWNERID": OWNERID
}

token = ""
sv_prefix = {}
sv_perm = {}
modules = {}
commands = []
filters = []

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
import_module()
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

    # Load user's permission.
    perm = await get_user_perm(message.author, message.guild)

    if message.content == "?prefix":
        # Print the prefix that is used in this server
        logging.info(f"{str(message.author)} used the command ?prefix.")
        embed = await get_embed(
            "prefix",
            f"Prefix used in this server is `{prefix}`.",
            message.author
        )
        await send_msg(message.channel, embed)

    elif message.content == "?reset_prefix" and perm <= 3:
        # Reset the prefix to !. only svmod user can use this.
        logging.info(f"{str(message.author)} used the command ?prefix_reset.")
        sv_prefix[str(message.guild.id)] = PREFIX
        await save_json(sv_prefix, "prefix")
        embed = await get_embed(
            "reset_prefix",
            f"Sucessfully restored the prefix to `{prefix}`.",
            message.author
        )
        await send_msg(message.channel, embed)

    elif message.content.startswith(prefix):
        # Get a command and run it if it's a thing
        fullcmd = message.content.replace(prefix, "", 1)
        print(fullcmd)
        cmd = fullcmd.split()[0]
        logging.info(
    f"{str(message.author)} used the command {cmd}. message: {message.content}")

        if cmd == "reload" and perm == 1:
            # Call import_module() function to reload modules
            logger.info("Reloading...")
            embed = await get_embed(
                "reload",
                "Reloading Modules...",
                message.author
            )
            msg = await send_msg(message.channel, embed)
            import_module()
            embed = await get_embed(
                "reload",
                "Succesfully Reloaded modules.",
                message.author
            )
            await edit_msg(msg, embed)

        elif cmd in commands:
            # Get the module's permission, If user's permission is higher than
            # the command, execute it
            module = modules[cmd]
            module_perm = await get_module_perm(cmd, message.guild)
            if perm <= module_perm and not module_perm == 6:
                # module.main function is async generator which yields the
                # content to send. so It stores the generator in msggen variable
                # and execute it.
                logging.info(
                    f"{str(message.author)} used the command {prefix}{cmd}."
                )
                msggen = module.main(message, client = client)
                msg = None
                async for txt in msggen:
                    if txt is None:
                        # If module wants to remove the message, It will return
                        # None. If we already sent a message, delete it.
                        if msg:
                            await msg.delete()
                            msg == None
                    else:
                        # If the type is str, It has to be converted to embed
                        # unless it's starting with "noembed|", which should be
                        # sent as is.
                        # Module can also yield the embed object directly, or
                        # Yield the file. If the type is not a str, It will
                        # assume that it is either embed or file, and pass it
                        # directly to send_msg or edit_msg function.
                        if type(txt) == str:
                            if txt.startswith("noembed|"):
                                content = txt.replace("noembed|", "", 1)
                            else:
                                content = await get_embed(
                                    cmd,
                                    txt,
                                    message.author
                                )
                        else:
                            content = txt
                        if msg:
                            # If we already sent a message, edit it. else, send
                            # a new one.
                            await edit_msg(msg, content)
                        else:
                            msg = await send_msg(message.channel, content)
    for module_name in filters:
        # Execute all the filters. it should only recieve a message object and
        # return(not yield) a string to be sent as is.
        content = await modules[module_name].main(message)
        if content:
            await send_msg(message.channel, content)

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