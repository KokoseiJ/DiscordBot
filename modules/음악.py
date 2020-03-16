import os
import re
import asyncio
import discord
import logging
import threading
import subprocess
import modules.__ytapi__ as ytapi
from subprocess import PIPE, STDOUT

PATH = os.path.dirname(os.path.abspath(__file__))

TYPE = "public"

HELP = """\
음악을 재생합니다.
사용 방법: 음악 [join/leave/play/stop/skip/pause/resume/current/queue]\
"""

class music_file:
    def __init__(self, provider, vidid, name, thumbnail, adder, basepath = PATH, foldername = "__music__"):
        self.provider = provider
        self.id = vidid
        self.name = name
        self.thumbnail = thumbnail
        self.adder = adder
        self.filename = f"{self.provider}-{self.id}"
        self.path = os.path.join(basepath, foldername)
        self.downloaded = False

    async def _init(self):
        if await self._file_exists():
            self.downloaded = True
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

    async def _get_url(self):
        if self.provider == "yt":
            url = "https://www.youtube.com/watch?v={}"
        else:
            raise NotImplementedError(f"Unknown Provider {self.provider}")
        url = url.format(self.id)
        #self._run_ytdl(url)
        return url

    async def _run_ytdl(self, url):
        logging.info(f"음악_Downloading {url}.")
        process = await asyncio.create_subprocess_exec(
            "youtube-dl", "-x", "--audio-format", "opus", "--audio-quality", "128K",
            url, "-o", os.path.join(self.path, self.filename + ".%(ext)s"),
            stdout = PIPE, stderr = STDOUT)
        stdout, _ = await process.communicate()
        logging.info(stdout.decode())
        self.downloaded = True
        return

    def _run_ytdl_noasync(self, url):
        logging.info(f"음악_Downloading {url}.")
        process = subprocess.run(
            ["youtube-dl", "-x", "--audio-format", "opus", "--audio-quality", "128K",
            url, "-o", os.path.join(self.path, self.filename + ".%(ext)s")],
            stdout = PIPE, stderr = STDOUT)
        logging.info(process.stdout.decode())
        self.downloaded = True
        return

    async def get(self):
        if self.downloaded:
            return discord.FFmpegOpusAudio(os.path.join(self.path, self.filename + ".opus"))
        else:
            url = await self._get_url()
            await self._run_ytdl(url)
            if await self._file_exists():
                return discord.FFmpegOpusAudio(os.path.join(self.path, self.filename + ".opus"))
            raise RuntimeError("Failed to download.")



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
        if type(item) == music_file:
            self.queue.append(item)
        else:
            self.queue.extend(item)
        return

    async def list_queue(self):
        return self.queue.copy()

    async def nuke_queue(self):
        return self.queue.clear()

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
        music = await self._get_queue()
        embed = discord.Embed(
            title = "음악",
            description = f"**{await self.get_name()}: {music.name}을 다운로드하는 중입니다...**",
            color = 0x962fa4)
        embed.set_thumbnail(url = music.thumbnail)
        embed.set_footer(text = f"신청자: {music.adder.display_name}", icon_url = music.adder.avatar_url)
        msg = await self.channel.send(embed = embed)
        src = await music.get()
        self.client.play(src, after = self._play_wrap)
        embed = discord.Embed(
            title = "음악",
            description = f"**{await self.get_name()}: {music.name}을 재생합니다.**",
            color = 0x962fa4)
        embed.set_thumbnail(url = music.thumbnail)
        embed.set_footer(text = f"신청자: {music.adder.display_name}", icon_url = music.adder.avatar_url)
        await msg.edit(embed = embed)
        return

    def _play_wrap(self, error = None):
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



async def get_vid(usrinput):
    if usrinput.startswith("https://www.youtube.com/watch?v="):
        videoid = usrinput.split("=")[1].split("&")[0]
        if "&list=" in usrinput:
            playlistid = usrinput.split("=")[2].split("&")[0]
            return await ytapi.get_playlist(playlistid, videoid)
        else:
            return None, await ytapi.get_vid_info(videoid)
    elif usrinput.startswith("https://youtu.be/"):
        videoid = usrinput.split("/")[-1].split("?")[0]
        return None, await ytapi.get_vid_info(videoid)
    elif usrinput.startswith("https://www.youtube.com/playlist?list="):
        playlistid = usrinput.split("=")[1].split("&")[0]
        return await ytapi.get_playlist(playlistid)
    else:
        result = await ytapi.search_video(usrinput)
        return None, result[0]

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
            async for msgtxt in leave_all(message, bot_client):
                yield msgtxt
            return
        else:
            raise ValueError(f"알 수 없는 명령어: {cmd[1]}.")
        logging.info("음악_Running " + cmd[1])
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
    music = await get_class(
        music_file, "yt", vidid, "Test_music",
        "https://www.meme-arsenal.com/memes/c9e6371faa3b57eaee1d35595ca8e910.jpg",
        message.author)
    await client.play(music, message)
    yield f"{vidid}를 재생합니다."

async def play(message):
    client = await get_client(message)
    cmd = message.content.split()
    if len(cmd) == 2:
        raise ValueError("재생할 URL/검색어를 입력하여야 합니다.")
    usrinput = message.content[len(cmd[0]) + len(cmd[1]) + 2:]
    yield f"{usrinput} 을(를) 로딩하는 중입니다..."
    plname, video = await get_vid(usrinput)
    if plname is None:
        yield f"{video[2]}을 로딩하는 중입니다..."
        music = await get_class(music_file, *video, message.author)
        yield f"{video[2]}을(를) Queue에 추가하는 중입니다..."
        await client.play(music, message)
        yield f"{video[2]}을(를) Queue에 추가하였습니다."
    else:
        yield f"{plname}을 로딩하는 중입니다..."
        music = [await get_class(music_file, *_video, message.author) for _video in video]
        yield f"{plname}을(를) Queue에 추가하는 중입니다..."
        await client.play(music, message)
        yield f"{plname}을(를) Queue에 추가하였습니다. 첫 곡은 {video[0][2]}입니다."

async def stop(message):
    client = await get_client(message)
    await client.nuke_queue()
    await client.stop()
    yield "음악을 정지하고, 리스트를 비웠습니다."

async def skip(message):
    client = await get_client(message)
    await client.stop()
    yield "현재 재생중인 음악을 스킵합니다."

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
    voice_clients = bot_client.voice_clients
    namelist = [client.channel.name for client in voice_clients]
    yield ", ".join(namelist) + "에서 나가는 중입니다..."
    for client in voice_clients:
        if client.is_connected():
            await client.disconnect()
    clients = {}
    yield ", ".join(namelist) + "에서 성공적으로 나왔습니다."