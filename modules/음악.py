import os
import asyncio
import discord
import logging
import threading

MAX_THREAD = 100

PATH = os.path.dirname(os.path.abspath(__file__))

TYPE = "public"

HELP = """\
음악을 재생합니다.
사용 방법: 음악 [join/leave/play/stop/pause/resume/queue]\
"""

class music_file:
    def __init__(self, provider, vidid, basepath = PATH, foldername = "__music__"):
        self.provider = provider
        self.id = vidid
        self.filename = f"{self.provider}-{self.id}"
        self.path = os.path.join(basepath, foldername)

    async def _init(self):
        if not await self._file_exists():
            await self._download()
        return

    async def _file_exists(self):
        try:
            if self.filename + ".opus" in os.listdir(self.path):
                return True
            else:
                return False
        except FileNotFoundError:
            logging.warning(f"{self.path} Not found. Creating new one...")
            os.mkdir(self.path)
            return False

    async def _download(self):
        if self.provider == "yt":
            url = "https://www.youtube.com/watch?v={}"
        else:
            raise NotImplementedError(f"Unknown Provider {self.provider}")
        url = url.format(self.id)
        await self._run_ytdl(url)
        return

    async def _run_ytdl(self, url):
        logging.info(f"Downloading {url}.")
        await asyncio.create_subprocess_exec(
            "youtube-dl", "-x", "--audio-format", "opus", url, "-o", os.path.join(self.path, self.filename + ".%(ext)s"))
        return
    async def get(self):
        while not await self._file_exists():pass
        return discord.FFmpegOpusAudio(os.path.join(self.path, self.filename + ".opus"))

class server_client:
    def __init__(self, client, bot_client):
        self.bot_client = bot_client
        self.client = client
        self.queue = []

    async def _init(self):
        return

    async def get_name(self):
        return self.client.channel.name

    async def is_alive(self):
        return self.client.is_connected()

    async def is_playing(self):
        return self.client.is_playing()

    async def add_queue(self, item):
        self.queue.append(item)
        return

    async def list_queue(self):
        return self.queue.copy()

    async def _get_queue(self):
        try:
            return self.queue.pop(0)
        except IndexError:
            raise RuntimeError("Queue가 비어있습니다.")

    def _get_queue_nopop(self):
        try:
            return self.queue[0]
        except IndexError:
            raise RuntimeError("Queue가 비어있습니다.")

    async def play(self, music, message):
        self.channel = message.channel
        await self.add_queue(music)
        if not await self.is_playing():
            await self._play()

    async def _play(self):
        song = await self._get_queue()
        src = await song.get()
        self.client.play(src, after = self._play_wrap)
        return

    def _play_wrap(self, error):
        if error:
            raise error
        else:
            coro = self._play()
            fut = asyncio.run_coroutine_threadsafe(coro, self.bot_client.loop)

    async def stop(self):
        self.client.stop()
        return

    async def skip(self):
        await self.stop()
        await self._play()

    async def pause(self):
        self.client.pause()
        return

    async def resume(self):
        self.client.resume()
        return

    async def leave(self):
        await self.client.disconnect()

clients = {}

async def get_class(classobj, *args):
    rtnobj = classobj(*args)
    await rtnobj._init()
    return rtnobj

async def get_client(message):
    try:
        client = clients[message.guild.id]
        if await client.is_alive():
            return clients[message.guild.id]
        else:
            del clients[message.guild.id]
            raise KeyError
    except KeyError:
        raise RuntimeError("이 서버에서 접속하고 있는 보이스 채널이 없습니다.")

async def main(message, **kwargs):
    cmd = message.content.split()
    bot_client = kwargs['client']
    if len(cmd) == 1:
        raise ValueError("명령어를 입력하여야 합니다.")
    else:
        if cmd[1] == "join":
            async for msgtxt in join(message, bot_client):
                yield msgtxt
                return
        elif cmd[1] == "leave":
            func = leave
        elif cmd[1] == "play":
            func = play
        elif cmd[1] == "play_test":
            func = play_test
        elif cmd[1] == "play_test_legacy":
            func = play_test_legacy
        elif cmd[1] == "stop":
            func = stop
        elif cmd[1] == "skip":
            func = skip
        elif cmd[1] == "pause":
            func = pause
        elif cmd[1] == "resume":
            func = resume
        elif cmd[1] == "leave_all":
            async for msgtxt in join(message, bot_client):
                yield msgtxt
                return
        else:
            raise ValueError(f"알 수 없는 명령어: {cmd[1]}.")
        logging.info("Running " + cmd[1])
        async for msgtxt in func(message):
            yield msgtxt

async def join(message, bot_client):
    member = message.author
    if not type(member) == discord.Member:
        raise TypeError("message.author 값의 타입이 discord.Member가 아닙니다. 명령어를 사용하신 곳이 서버가 맞는지 확인해주세요.")
    voice = member.voice
    if voice == None:
        raise RuntimeError("명령어 실행자가 보이스 채널에 접속해 있지 않습니다.")
    client = await voice.channel.connect()
    clients[message.guild.id] = await get_class(server_client, client, bot_client)
    yield f"{client.channel.name} 채널에 접속하였습니다."

async def leave(message):
    client = await get_client(message)
    channel_name = await client.get_name()
    await client.leave()
    del clients[message.guild.id]
    yield f"{channel_name} 채널에서 나왔습니다."

async def play_test_legacy(message):
    clientobj = await get_client(message)
    client = clientobj.client
    testfile = "yt-55AalrbALAk.opus"
    #testfile = "test.mp3"
    music_file = discord.FFmpegPCMAudio(testfile)
    client.play(music_file)
    yield f"테스트 음악을 재생합니다."

async def play_test(message):
    client = await get_client(message)
    cmd = message.content.split()
    if len(cmd) == 2:
        raise ValueError("재생할 videoid를 입력하여야 합니다.")
    vidid = cmd[2]
    yield f"{vidid}를 Queue에 추가하는 중입니다..."
    song = await get_class(music_file, "yt", vidid)
    await client.play(song, message)
    yield f"{vidid}를 재생합니다."

async def stop(message):
    client = await get_client(message)
    await client.stop()
    yield "음악을 정지합니다."

async def skip(message):
    client = await get_client(message)
    await client.skip()
    yield "현재 재생중이 음악을 스킵합니다."

async def pause(message):
    client = await get_client(message)
    await client.pause()
    yield "음악을 일시정지합니다."

async def resume(message):
    client = await get_client(message)
    await client.resume()
    yield "음악을 다시 재생합니다."

async def leave_all(message, bot_client):
    global clients
    namelist = [await clients[client].get_name() for client in clients if await clients[client].is_alive()]
    yield ", ".join(namelist) + "에서 나가는 중입니다..."
    for client in clients:
        if await clients[client].is_alive():
            await clients[client].leave()
    clients = {}
    yield ", ".join(namelist) + "에서 성공적으로 나왔습니다."