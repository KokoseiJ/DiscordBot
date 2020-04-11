import os
import sys
import discord
import logging
import importlib
import traceback
import configparser
from bot_func import Bot

def import_module():
    """
    This function checks modules folder by default, and load every single module
    in the folder and store it as a dict.
    It couldn't be put in to the bot_func.py as it requires the access to the
    modules, commands, filters variables. I know that there's ways to implement
    this without global keyword, but not now.
    also, I suggest you to not use reload command often as it messes up badly
    with some modules that stores informations on their own like 음악, it
    literally fucks up and it requires you to manually kick the bot and rejoin.
    """
    # TODO: Implement `on_reload` methods to all the modules, and execute it
    # when the bot reloads modules.
    global modules, commands, filters
    folderpath = os.path.join(PATH, "modules")
    logging.info(f"Loading {folderpath}...")
    for modulefile in os.listdir(folderpath):
        if not modulefile.startswith("__"):
            module_name = modulefile.split(".")[0]
            # if it exists, reload it. else, import it.
            try:
                importlib.reload(modules[module_name])
                log = f"Succesfully Reloaded {module_name}."
            except KeyError:
                module = importlib.import_module(f"modules.{module_name}")
                modules[module_name] = module
                if module.PERMISSION == 6:
                    filters.append(module_name)
                else:
                    commands.append(module_name)
                log = f"Succesfully Loaded {module_name}."
            logging.info(log)

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

# Convert value to hexadecimal. raise valueerror if it's not hexadecimal.
try:
    MAINCOLOR = int(config['section']['MainColor'], 16)
except ValueError:
    raise ValueError("Value of config entry 'MainColor' is not hexadecimal.")
BOTNAME = config['section']['BotName']
PREFIX = config['section']['Prefix']
OWNERID = int(config['section']['OwnerId'])
# STATICS will be passed to modules/bot module.
STATICS = {
    "PATH": PATH,
    "PREFIX": PREFIX,
    "MAINCOLOR": MAINCOLOR,
    "BOTNAME": BOTNAME,
    "OWNERID": OWNERID
}

# Initialize Bot module with static variables.
Bot.set_statics(STATICS)

del config

# Logging part, This logs at both console window and discordbot.log file
logging.captureWarnings(True)

# Example output: 
# 2020/04/20 01:10:37|[LEVEL](any_function): This is example
log_formatter = logging.Formatter(
    "%(asctime)s|[%(levelname)s](%(funcName)s): %(message)s",
    "%Y/%m/%d %H:%M:%S"
)

logger = logging.getLogger()
# Set loglevel to INFO.
logger.setLevel(logging.INFO)

# This handler will log to the file.
file_handler = logging.FileHandler(os.path.join(PATH, "discordbot.log"))
file_handler.setFormatter(log_formatter)
logger.addHandler(file_handler)

# This handler will log to the console.
console_handler = logging.StreamHandler()
console_handler.setFormatter(log_formatter)
logger.addHandler(console_handler)

logger.info(
    f"\n====================Starting {BOTNAME}...====================\n"
)

token = Bot.get_file("discord_token")
sv_prefix = Bot.get_json("bot_prefix")
sv_perm = Bot.get_json("bot_perm")
modules = {}
commands = []
filters = []
import_module()

client = discord.Client()

# Aight, here goes handlers

@client.event
async def on_ready():
    ## TODO: Do something in here, like changing the activity for every single
    # second
    logger.info('Succesfully logged in as {0.user}!'.format(client))
    activity = discord.Game("재미있는 코드 갈아엎기")
    await client.change_presence(activity = activity)

@client.event
async def on_message(message):
    """
    Gets prefix for the server, check if command exists, check permission of
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
    perm = await Bot.get_user_perm(message.author, message.guild, sv_perm)
    if not message.author.bot:

        if message.content == "?prefix":
            # Print the prefix that is used in this server
            logging.info(f"{str(message.author)} used the command ?prefix.")
            embed = await Bot.get_embed(
                "prefix",
                f"Prefix used in this server is `{prefix}`.",
                message.author
            )
            await Bot.send_msg(message.channel, embed)
    
        elif message.content == "?reset_prefix" and perm <= 3:
            # Reset the prefix to !. only svmod user can use this.
            logging.info(
                f"{str(message.author)} used the command ?prefix_reset."
            )
            sv_prefix[str(message.guild.id)] = PREFIX
            await Bot.json_dump(sv_prefix, "prefix")
            embed = await Bot.get_embed(
                "reset_prefix",
                f"Sucessfully restored the prefix to `{prefix}`.",
                message.author
            )
            await Bot.send_msg(message.channel, embed)
    
        elif message.content.startswith(prefix):
            # Get a command and run it if it's a thing
            fullcmd = message.content.replace(prefix, "", 1)
            cmd = fullcmd.split()[0]
            logging.info(
    f"{str(message.author)} used the command {cmd}. message: {message.content}"
            )
    
            if cmd == "reload" and perm == 1:
                # Call import_module() function to reload modules
                logger.info("Reloading...")
                embed = await Bot.get_embed(
                    "reload",
                    "Reloading Modules...",
                    message.author
                )
                msg = await Bot.send_msg(message.channel, embed)
                import_module()
                embed = await Bot.get_embed(
                    "reload",
                    "Succesfully Reloaded modules.",
                    message.author
                )
                await Bot.edit_msg(msg, embed)
    
            elif cmd in commands:
                # Get the module's permission, If user's permission is higher
                # than the command, execute it
                module = modules[cmd]
                module_perm = await Bot.get_module_perm(
                    module, message.guild, sv_perm
                )
                if perm <= module_perm and not module_perm == 6:
                    # module.main function is async generator which yields the
                    # content to send. so It stores the generator in msggen
                    # variable and execute it.
                    logging.info(
                        f"{str(message.author)} used the command {prefix}{cmd}."
                    )
                    msggen = module.main(
                        message,
                        client = client,
                        statics = STATICS,
                        sv_perm = sv_perm,
                        sv_prefix = sv_prefix,
                        bot_func = Bot
                    )
                    msg = None
                    async for rtnvalue in msggen:
                        if rtnvalue is None:
                            # If module wants to remove the message, It will
                            # return None. If we already sent a message, delete it.
                            if msg:
                                await Bot.msg.delete()
                                msg == None
                        else:
                            # If the type is str, It has to be converted to
                            # embed unless it's starting with "noembed|", which
                            # should be sent as is.
                            # Module can also yield the embed object directly,
                            # or Yield the file. If the type is not a str, It
                            # will assume that it is either embed or file, and
                            # pass it directly to send_msg or edit_msg function.
                            if type(rtnvalue) == str:
                                if rtnvalue.startswith("noembed|"):
                                    content = rtnvalue.replace(
                                        "noembed|", "", 1
                                    )
                                else:
                                    content = await Bot.get_embed(
                                        cmd,
                                        rtnvalue,
                                        message.author
                                    )
                            else:
                                content = rtnvalue
                            if msg:
                                # If we already sent a message, edit it. else,
                                # send a new one.
                                await Bot.edit_msg(msg, content)
                            else:
                                msg = await Bot.send_msg(message.channel, content)
    
    for module_name in filters:
        # Execute all the filters. it should only recieve a message object and
        # return(not yield) a string to be sent as is.
        # Inputs from bots are not filtered for fun interactions between bots,
        # Modules should filter those.
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
        embed = await Bot.get_embed(
            title = "An error has been occured while running the task.",
            desc = f"```{tbtxt}```",
            colour = 0xff0000,
            sender = message.author
        )
        await Bot.send_msg(message.channel, embed)
    else:
        raise


client.run(token)