import os
import sys
import json
import discord 
import logging
import aiofiles
import importlib

BOTNAME = "키리기리 쿄코 봇"
PREFIX = "!"
PATH = os.path.dirname(os.path.abspath(__file__))

def get_ownerid(path = PATH):
    try:
        ownerid = int(open(os.path.join(path, "owner_id")).read())
    except:
        ownerid = None
        while ownerid is None:
            try:
                ownerid = int(input("Paste the id of the bot's owner.: "))
            except ValueError:
                print("id should only contain integer values.")
        with open(os.path.join(path, "owner_id"), "w") as f:
            f.write(str(ownerid))
    return ownerid

def get_token(path = PATH):
    try:
        token = open(os.path.join(path, "discord_token")).read()
    except:
        token = input("Paste your bot token here.: ")
        with open(os.path.join(path, "discord_token"), "w") as f:
            f.write(token)
    return token

def get_json(filename, path = PATH):
    try:
        with open(os.path.join(path, filename)) as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def import_modules(path = PATH):
    global public, private, owner, bot_filter
    for x in os.listdir(os.path.join(path, "modules")):
        if "__" in x:
            continue
        module_name = x.split(".")[0]
        logging.info(f"loading {module_name} module...")
        try:
            importlib.reload(modules[module_name])
            logtxt = f"succesfully reloaded {module_name} module."
        except:
            modules[module_name] = importlib.import_module("modules." + module_name)
            module_type = modules[module_name].TYPE
            if module_type == "public":
                public.append(module_name)
            elif module_type == "private":
                private.append(module_name)
            elif module_type == "owner":
                owner.append(module_name)
            elif module_type == "filter":
                bot_filter.append(module_name)
            else:
                logging.info(f"{module_name} has unknown type.")
                continue
            logtxt = f"succesfully loaded {module_type} type {module_name} module."
        logging.info(logtxt)

async def get_embed(cmd, desc, color = 0x962fa4):
    if desc.startswith("noembed|"):
        return desc[len("noembed|"):]
    else:
        return discord.Embed(title = cmd.replace("_", " ").capitalize(), description = desc, color = color)

async def save_dict(filename, dict, path = PATH):
    async with aiofiles.open(os.path.join(path, filename), "w") as f:
        await f.write(json.dumps(dict))
    return

async def send_msg(channel, msgtxt):
    if type(msgtxt) == str:
        return await channel.send(msgtxt)
    elif type(msgtxt) == discord.Embed:
        return await channel.send(embed = msgtxt)

async def edit_msg(msg, msgtxt):
    if type(msgtxt) == str:
        return await msg.edit(msgtxt)
    elif type(msgtxt) == discord.Embed:
        return await msg.edit(embed = msgtxt)

token = ""
modules = {}
public = []
private = []
owner = []
bot_filter = []
ownerid = 0
sudoers_server = {}
prefix_server = {}

log_formatter = logging.Formatter("%(asctime)s | %(levelname)s: %(message)s")
logger = logging.getLogger()
logger.setLevel(logging.INFO)

file_handler = logging.FileHandler(os.path.join(PATH, "discordbot.log"))
file_handler.setFormatter(log_formatter)
logger.addHandler(file_handler)

console_handler = logging.StreamHandler()
console_handler.setFormatter(log_formatter)
logger.addHandler(console_handler)

token = get_token()
ownerid = get_ownerid()
sudoers_server = get_json("sudoers")
prefix_server = get_json("prefix")
import_modules()
client = discord.Client()

@client.event
async def on_ready():
    logger.info('We have logged in as {0.user}'.format(client))
    activity = discord.Game("Use ?prefix to get prefix")
    await client.change_presence(activity = activity)

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    for cmd in bot_filter:
        msgtxt = await modules[cmd].main(message)
        if msgtxt:
            await message.channel.send(msgtxt)

    if message.author.bot:
        return

    try:
        sudoers = sudoers_server[str(message.guild.id)]
    except KeyError:
        sudoers = []
        sudoers_server[str(message.guild.id)] = sudoers
    try:
        prefix = prefix_server[str(message.guild.id)]
    except KeyError:
        logger.warning("Prefix was not presented in prefix_server.")
        prefix = PREFIX
        prefix_server[str(message.guild.id)] = prefix

    """
    if message.content.startswith('$hello'):
        await message.channel.send('이쿠사바 무쿠로... 이 학교에 숨은 16번째 고교생... "초고교급 절망"이라 불리는 여고생... 이쿠사바 무쿠로를 조심해.')
    """
    if message.content == "?prefix":
        logger.info(message.author.display_name + " used ?prefix Command.")
        embed = await get_embed("prefix", f"이 서버의 Prefix는 `{prefix}`입니다.")
        await send_msg(message.channel, embed)
    elif message.content == "?reset_prefix" and (message.author.id in sudoers or message.author.id == ownerid):
        logger.info(message.author.display_name + " used ?reset_prefix Command.")
        splitcmd = message.content.split()
        embed = await get_embed("reset_prefix", "Prefix를 변경하는 중입니다...")
        msg = await send_msg(message.channel, embed)
        prefix = "!"
        prefix_server[str(message.guild.id)] = prefix
        await save_dict("prefix", prefix_server)
        embed = await get_embed("reset_prefix", f"Prefix를 {prefix}로 리셋하였습니다.")
        await edit_msg(msg, embed)

    elif message.content.startswith(prefix) and not message.content == prefix:
        cmd = message.content[len(prefix):].split()[0]
        fullcmd = message.content[len(prefix):].split()
        logger.info(message.author.display_name + f" used {prefix}{cmd} Command. Message: {message.content}")

        if cmd == "help":
            logger.info("Showing Help...")
            embed = await get_embed("help", f"{BOTNAME}에서 쓸 수 있는 명령어들입니다.")
            system_help = "\
?prefix:\n이 서버의 prefix를 알려줍니다. 본 명령어는 서버의 prefix의 영향을 받지 않습니다.\n\n\
?reset_prefix:\n이 서버의 prefix를 기본값인 !로 리셋합니다. 본 명령어는 서버의 prefix의 영향을 받지 않으며, 등록된 사용자만이 사용할 수 있습니다.\n\n\
help:\n이 메세지를 보여줍니다.\n\n\
reload:\n모듈을 다시 로딩합니다. 본 명령어는 Owner만이 사용할 수 있습니다.\n\n\
add_sudoer:\n사용자를 등록합니다. 등록된 사용자는 서버별로 관리됩니다. 본 명령어는 Owner만이 사용할 수 있습니다.\n\
사용법: add_sudoer [user_list]\n\n\
remove_sudoer:\n사용자를 등록해제합니다. 본 명령어는 Owner만이 사용할 수 있습니다.\n\
사용법: remove_sudoer [user_list]\n\n\
list_sudoer:\n이 서버에 있는 등록된 사용자의 목록을 출력합니다.\n\n\
set_prefix:\n이 서버에서 사용할 Prefix를 설정합니다. 본 명령어는 등록된 사용자만 사용할 수 있습니다.\n\
사용법: set_prefix [prefix]"
            embed.add_field(name = "봇 내부 명령어", value = system_help)
            public_help = "\n\n".join([f"{module}:\n{modules[module].HELP}" for module in public])
            embed.add_field(name = "Public(모두가 사용할 수 있는 명령어)", value = public_help)
            private_help = "\n\n".join([f"{module}:\n{modules[module].HELP}" for module in private])
            embed.add_field(name = "Private(서버별로 등록된 사용자만 사용할 수 있는 명령어)", value = private_help)
            owner_help = "\n\n".join([f"{module}:\n{modules[module].HELP}" for module in owner])
            embed.add_field(name = "Owner(봇의 주인 만이 사용할 수 있는 명령어)", value = owner_help)
            filter_help = "\n\n".join([f"{module}:\n{modules[module].HELP}" for module in bot_filter])
            embed.add_field(name = "Filter(명령어로 작동되지 않고 평문 메세지에 반응하는 모듈)", value = filter_help)
            await send_msg(message.channel, embed)

        elif cmd == "reload" and message.author.id == ownerid:
            logger.info("Reloading...")
            embed = await get_embed("reload", "모듈을 다시 로딩하는 중입니다.")
            msg = await send_msg(message.channel, embed)
            import_modules()
            embed = await get_embed("reload", "모듈을 성공적으로 로딩하였습니다.")
            await edit_msg(msg, embed)

        elif cmd == "add_sudoer" and message.author.id == ownerid:
            logger.info("Running add_sudoer...")
            userlist = message.mentions
            if not userlist:
                raise ValueError("등록할 사용자를 멘션하여야 합니다.")
            embed = await get_embed("add_sudoer", "사용자를 등록하는 중입니다...")
            msg = await send_msg(message.channel, embed)
            addlist = [user.id for user in userlist if not user.id in sudoers]
            if not addlist:
                raise RuntimeError("추가로 등록할 사용자가 없습니다.")
            names = ", ".join([user.display_name for user in userlist if not user.id in sudoers])
            for user in addlist:
                sudoers_server[str(message.guild.id)].append(user)
            await save_dict("sudoers", sudoers_server)
            embed = await get_embed("add_sudoer", f"{names} 사용자들을 등록하였습니다.")
            await edit_msg(msg, embed)

        elif cmd == "remove_sudoer" and message.author.id == ownerid:
            logger.info("Running remove_sudoer...")
            userlist = message.mentions
            if not userlist:
                raise ValueError("등록해제할 사용자를 멘션하여야 합니다.")
            embed = await get_embed("remove_sudoer", "사용자를 등록해제하는 중입니다...")
            msg = await send_msg(message.channel, embed)
            dellist = [user.id for user in userlist if user.id in sudoers]
            if not dellist:
                raise RuntimeError("등록해제할 사용자가 없습니다.")
            names = ", ".join([user.display_name for user in userlist if user.id in sudoers])
            for user in dellist:
                sudoers_server[str(message.guild.id)].remove(user)
            await save_dict("sudoers", sudoers_server)
            embed = await get_embed("remove_sudoer", f"{names} 사용자들을 등록해제하였습니다.")
            await edit_msg(msg, embed)

        elif cmd == "list_sudoer":
            logger.info("Running list_sudoer...")
            sudoerlist = [user.display_name for user in message.guild.members if str(user.id) in sudoers]
            sudoerstxt = "\n".join(sudoerlist)
            embed = await get_embed("list_sudoer", sudoerstxt)
            msg = await send_msg(message.channel, embed)

        elif cmd == "set_prefix" and (message.author.id in sudoers or message.author.id == ownerid):
            logger.info("Running set_prefix...")
            splitcmd = message.content.split()
            if len(splitcmd) == 1:
                raise ValueError("바꿀 Prefix를 입력해야 합니다.")
            elif len(splitcmd) != 2 or "\u200b" in splitcmd[1] or "\u3164" in splitcmd[1]:
                raise ValueError("Prefix에는 띄어쓰기를 포함할 수 없습니다.")
            embed = await get_embed("set_prefix", "Prefix를 변경하는 중입니다...")
            msg = await send_msg(message.channel, embed)
            prefix = splitcmd[1]
            prefix_server[str(message.guild.id)] = prefix
            await save_dict("prefix", prefix_server)
            embed = await get_embed("set_prefix", f"Prefix를 {prefix}로 변경하였습니다.")
            await edit_msg(msg, embed)

        else:
            if (cmd in owner and message.author.id == ownerid) or \
            (cmd in private and (message.author.id in sudoers or message.author.id == ownerid)) or \
            (cmd in public):
                logger.info(f"Running {cmd}... ")
                msgtxt = modules[cmd].main(message, client = client)
                if msgtxt:
                    msg = None
                    async for txt in msgtxt:
                        embed = await get_embed(cmd, txt)
                        if msg:
                            await edit_msg(msg, embed)
                        else:
                            msg = await send_msg(message.channel, embed)

@client.event
async def on_error(event, *args, **kwargs):
    if event == "on_message":
        message = args[0]
        exc = sys.exc_info()
        excname = exc[0].__name__
        excarglist = [str(x) for x in exc[1].args]
        if not excarglist:
            traceback = excname
        else:
            traceback = excname + ": " + ", ".join(excarglist)
        logger.error(traceback)
        embed = discord.Embed(title = "코드를 실행하는 중 오류가 발생하였습니다.", description = traceback, color = 0xff0000)
        await message.channel.send(embed = embed)
    else:
        raise

client.run(get_token())