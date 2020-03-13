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

def get_sudoers(channel, path = PATH):
    try:
        return json.load(open(os.path.join(path, "sudoers")))[channel]
    except:
        return []

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
        return discord.Embed(title = cmd.capitalize(), description = desc, color = color)

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

modules = {}
public = []
private = []
owner = []
bot_filter = []
ownerid = 0

log_start()
ownerid = get_ownerid()
import_modules()
client = discord.Client()

@client.event
async def on_ready():
    log('We have logged in as {0.user}'.format(client))
    activity = discord.Game("Danganronpa 1: Trigger Happy Havoc")
    await client.change_presence(activity = activity)

@client.event
async def on_message(message):
    sudoers = get_sudoers(message.channel.id)
    if message.author == client.user:
        return
    """
    if message.content.startswith('$hello'):
        await message.channel.send('이쿠사바 무쿠로... 이 학교에 숨은 16번째 고교생... "초고교급 절망"이라 불리는 여고생... 이쿠사바 무쿠로를 조심해.')
    """
    # TODO: prefix 바꾸는 기능 추가할것
    if message.content.startswith(PREFIX):
        cmd = message.content.split()[0].replace(PREFIX, "")
        if cmd == "reload" and message.author.id == ownerid:
            log("Reloading...")
            embed = get_embed("reload", "모듈을 다시 로딩하는 중입니다.")
            msg = await message.channel.send(embed = embed)
            import_modules()
            embed = get_embed("reload", "모듈을 성공적으로 로딩하였습니다.")
            await msg.edit(embed = embed)
        elif cmd == "help":
            embed = get_embed("help", f"{BOTNAME}에서 쓸 수 있는 명령어들입니다.")
            system_help = "help:\n이 메세지를 보여줍니다.\n\nreload:\n모듈을 다시 로딩합니다. 본 모듈은 owner만이 사용할 수 있습니다."
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
            message.channel.send(msgtxt)

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