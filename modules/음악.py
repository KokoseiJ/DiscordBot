import discord

TYPE = "public"
IS_ASYNC = True

HELP = """\
음악을 재생합니다.
사용 방법: 음악 [join/leave/play/stop/pause/resume/queue]\
"""

clients = {}

async def get_client(message):
    try:
        return clients[message.channel.id]
    except KeyError:
        raise KeyError("이 서버에서 접속하고 있는 보이스 채널이 없습니다.")

async def main(message):
    cmd = message.content.split()
    if len(cmd) == 1:
        raise ValueError("명령어를 입력하여야 합니다.")
    else:
        if cmd[1] == "join":
            return await join(message)
        elif cmd[1] == "leave":
            return await leave(message)
        elif cmd[1] == "play":
            return await play_test(message)
        elif cmd[1] == "pause":
            return await pause(message)
        elif cmd[1] == "resume":
            return await resume(message)
        else:
            return f"알 수 없는 명령어: {cmd[1]}."

async def join(message):
    member = message.author
    if not type(member) == discord.Member:
        raise TypeError("message.author 값의 타입이 discord.Member가 아닙니다. 명령어를 사용하신 곳이 서버가 맞는지 확인해주세요.")
    channel = member.voice.channel
    if channel == None:
        raise RuntimeError("명령어 실행자가 보이스 채널에 접속해 있지 않습니다.")
    client = await channel.connect()
    clients[message.channel.id] = client
    return f"{client.channel.name} 채널에 접속하였습니다."

async def leave(message):
    client = await get_client(message)
    channel_name = client.channel.name
    await client.disconnect()
    del clients[message.channel.id]
    return f"{channel_name} 채널에서 나왔습니다."

async def play_test(message):
    client = await get_client(message)
    music_file = discord.FFmpegPCMAudio("yt-55AalrbALAk.opus")
    client.play(music_file)
    return f"테스트 음악을 재생합니다."

async def pause(message):
    client = await get_client(message)
    client.pause()
    return "음악을 일시정지합니다."

async def resume(message):
    client = await get_client(message)
    client.resume()
    return "음악을 다시 재생합니다."