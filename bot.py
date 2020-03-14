import os
import sys
import json
import time
import types
import discord 
import importlib

BOTNAME = "키리기리 쿄코 봇"
PREFIX = "!"
PATH = os.path.dirname(os.path.abspath(__file__))

def log_start(path = PATH):
    timenow = time.strftime("%Y/%M/%d %H:%M:%S")
    with open(os.path.join(path, "bot_log"), "a") as file:
        file.write(f"====================\n{timenow} {BOTNAME} Starting...\n")

def log(text, path = PATH):
    timenow = time.strftime("%H:%M:%S")
    logtxt = f"{timenow} | {text}"
    print(logtxt)
    with open(os.path.join(path, "bot_log"), "a") as file:
        file.write(logtxt + "\n")

def get_ownerid(path = PATH):
    try:
        ownerid = int(open(os.path.join(path, "owner_id")).read())
    except:
        log("Error: owner_id file was not found. Creating new one...")
        ownerid = None
        while ownerid is None:
            try:
                ownerid = int(input("Paste the id of the bot's owner.: "))
            except ValueError:
                print("id should only contain integer values.")
        log("Creating owner_id file...")
        open(os.path.join(path, "owner_id"), "w").write(str(ownerid))
    return ownerid

def get_token(path = PATH):
    try:
        token = open(os.path.join(path, "discord_token")).read()
    except:
        log("Error: discord_token file was not found. Creating new one...")
        token = input("Paste your bot token here.: ")
        log("Saving Token...")
        open(os.path.join(path, "discord_token"), "w").write(token)
    return token

def get_json(filename, path = PATH):
    try:
        return json.load(open(os.path.join(path, filename)))
    except FileNotFoundError:
        log(filename + " was not found.")
        return {}

def import_modules(path = PATH):
    global public, private, owner, bot_filter
    for x in os.listdir(os.path.join(path, "modules")):
        if "__" in x:
            continue
        module_name = x.split(".")[0]
        log(f"loading {module_name} module...")
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
                log(f"{module_name} has unknown type.")
            logtxt = f"succesfully loaded {module_type} type {module_name} module."
        log(logtxt)

def get_embed(cmd, desc, color = 0x962fa4):
    if desc.startswith("noembed|"):
        return desc.replace("noembed|", "")
    else:
        return discord.Embed(title = cmd.replace("_", " ").capitalize(), description = desc, color = color)

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

log_start()
token = get_token()
ownerid = get_ownerid()
sudoers_server = get_json("sudoers")
prefix_server = get_json("prefix")
import_modules()
client = discord.Client()

@client.event
async def on_ready():
    log('We have logged in as {0.user}'.format(client))
    activity = discord.Game("Danganronpa 1: Trigger Happy Havoc")
    await client.change_presence(activity = activity)

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    try:
        sudoers = sudoers_server[str(message.guild.id)]
    except KeyError:
        sudoers = []
        sudoers_server[str(message.guild.id)] = sudoers
    try:
        prefix = prefix_server[str(message.guild.id)]
    except KeyError:
        log("Prefix was not presented in prefix_server.")
        prefix = PREFIX
        prefix_server[str(message.guild.id)] = prefix

    """
    if message.content.startswith('$hello'):
        await message.channel.send('이쿠사바 무쿠로... 이 학교에 숨은 16번째 고교생... "초고교급 절망"이라 불리는 여고생... 이쿠사바 무쿠로를 조심해.')
    """
    if message.content.startswith("?prefix"):
        log(message.author.display_name + " used ?prefix Command.")
        embed = get_embed("prefix", f"이 서버의 Prefix는 `{prefix}`입니다.")
        await send_msg(message.channel, embed)

    if message.content.startswith(prefix):
        cmd = message.content.split()[0][len(prefix):]
        log(message.author.display_name + f" used {prefix}{cmd} Command. Message: {message.content}")

        if cmd == "help":
            log("Showing Help...")
            embed = get_embed("help", f"{BOTNAME}에서 쓸 수 있는 명령어들입니다.")
            system_help = "\
help:\n이 메세지를 보여줍니다.\n\n\
reload:\n모듈을 다시 로딩합니다. 본 모듈은 Owner만이 사용할 수 있습니다.\n\n\
add_sudoer:\n사용자를 등록합니다. 등록된 사용자는 서버별로 관리됩니다. 본 모듈은 Owner만이 사용할 수 있습니다.\n\
사용법: add_sudoer [user_list]\n\n\
remove_sudoer:\n사용자를 등록해제합니다. 본 모듈은 Owner만이 사용할 수 있습니다.\n\
사용법: remove_sudoer [user_list]\n\n\
list_sudoer:\n이 서버에 있는 등록된 사용자의 목록을 출력합니다.\n\n\
set_prefix:\n이 서버에서 사용할 Prefix를 설정합니다. 본 모듈은 등록된 사용자만 사용할 수 있습니다.\n\
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
            log("Reloading...")
            embed = get_embed("reload", "모듈을 다시 로딩하는 중입니다.")
            msg = await send_msg(message.channel, embed)
            import_modules()
            embed = get_embed("reload", "모듈을 성공적으로 로딩하였습니다.")
            await edit_msg(msg, embed)

        elif cmd == "add_sudoer" and message.author.id == ownerid:
            log("Running add_sudoer...")
            userlist = message.mentions
            if not userlist:
                raise ValueError("등록할 사용자를 멘션하여야 합니다.")
            embed = get_embed("add_sudoer", "사용자를 등록하는 중입니다...")
            msg = await send_msg(message.channel, embed)
            addlist = [user.id for user in userlist if not user.id in sudoers]
            if not addlist:
                raise RuntimeError("추가로 등록할 사용자가 없습니다.")
            names = ", ".join([user.display_name for user in userlist if not user.id in sudoers])
            for user in addlist:
                sudoers_server[str(message.guild.id)].append(user)
            json.dump(sudoers_server, open(os.path.join(PATH, "sudoers"), "w"))
            embed = get_embed("add_sudoer", f"{names} 사용자들을 등록하였습니다.")
            await edit_msg(msg, embed)

        elif cmd == "remove_sudoer" and message.author.id == ownerid:
            log("Running remove_sudoer...")
            userlist = message.mentions
            if not userlist:
                raise ValueError("등록해제할 사용자를 멘션하여야 합니다.")
            embed = get_embed("remove_sudoer", "사용자를 등록해제하는 중입니다...")
            msg = await send_msg(message.channel, embed)
            dellist = [user.id for user in userlist if user.id in sudoers]
            if not dellist:
                raise RuntimeError("등록해제할 사용자가 없습니다.")
            names = ", ".join([user.display_name for user in userlist if user.id in sudoers])
            for user in dellist:
                sudoers_server[str(message.guild.id)].remove(user)
            json.dump(sudoers_server, open(os.path.join(PATH, "sudoers"), "w"))
            embed = get_embed("remove_sudoer", f"{names} 사용자들을 등록해제하였습니다.")
            await edit_msg(msg, embed)

        elif cmd == "list_sudoer":
            log("Running list_sudoer...")
            sudoerlist = [user.display_name for user in message.guild.members if user.id in sudoers]
            sudoerstxt = "\n".join(sudoerlist)
            embed = get_embed("list_sudoer", sudoerstxt)
            msg = await send_msg(message.channel, embed)

        elif cmd == "set_prefix" and (message.author.id in sudoers or message.author.id == ownerid):
            log("Running set_prefix...")
            splitcmd = message.content.split()
            if len(splitcmd) == 1:
                raise ValueError("바꿀 Prefix를 입력해야 합니다.")
            elif len(splitcmd) != 2:
                raise ValueError("Prefix에는 띄어쓰기를 포함할 수 없습니다.")
            embed = get_embed("set_prefix", "Prefix를 변경하는 중입니다...")
            msg = await send_msg(message.channel, embed)
            prefix = splitcmd[1]
            prefix_server[str(message.guild.id)] = prefix
            json.dump(prefix_server, open(os.path.join(PATH, "prefix"), "w"))
            embed = get_embed("set_prefix", f"Prefix를 {prefix}로 변경하였습니다.")
            await edit_msg(msg, embed)

        else:
            if (cmd in owner and message.author.id == ownerid) or \
            (cmd in private and (message.author.id in sudoers or message.author.id == ownerid)) or \
            (cmd in public):
                module = modules[cmd]
                if module.IS_ASYNC:
                    msgtxt = await module.main(message)
                else:
                    msgtxt = module.main(message)
                if msgtxt:
                    if isinstance(msgtxt, types.GeneratorType):
                        msg = None
                        for txt in msgtxt:
                            embed = get_embed(cmd, txt)
                            if msg:
                                await edit_msg(msg, embed)
                            else:
                                msg = await send_msg(message.channel, embed)
                    else:
                        embed = get_embed(cmd, msgtxt)
                        await send_msg(message.channel, embed)

    for cmd in bot_filter:
        msgtxt = modules[cmd].main(message)
        if msgtxt:
            await message.channel.send(msgtxt)

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
        embed = discord.Embed(title = "코드를 실행하는 중 오류가 발생하였습니다.", description = traceback, color = 0xff0000)
        await message.channel.send(embed = embed)
    else:
        raise

client.run(get_token())