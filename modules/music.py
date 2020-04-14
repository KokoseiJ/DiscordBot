import os
import sys
import random
import asyncio
import discord
import logging
import threading
import subprocess
import modules_old.__ytapi__ as ytapi
from subprocess import PIPE, STDOUT

PATH = os.path.dirname(os.path.abspath(__file__))

sys.path.insert(0, os.path.dirname(PATH))
from bot_func import Bot

PERMISSION = 5

HELP = """\
Plays the music.
Usage: music [join/leave/play/stop/skip/pause/resume/queue/shuffle]\
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
        self.url = self._get_url()
        if self._file_exists():
            self.downloaded = True

    def _file_exists(self):
        try:
            if self.filename + ".opus" in os.listdir(self.path):
                return True
            else:
                return False
        except FileNotFoundError:
            logging.warning(f"{self.path} Not found. Creating new one...")
            os.mkdir(self.path)
            return False

    def _get_url(self):
        if self.provider == "yt":
            url = "https://www.youtube.com/watch?v={}"
        else:
            raise NotImplementedError(f"Unknown Provider {self.provider}")
        url = url.format(self.id)
        #self._run_ytdl(url)
        return url

    async def _run_ytdl(self):
        url = self.url
        logging.info(f"Downloading {url}.")
        process = await asyncio.create_subprocess_exec(
            "youtube-dl", "-x", "--audio-format", "opus", "--audio-quality", "128K",
            url, "-o", os.path.join(self.path, self.filename + ".%(ext)s"),
            stdout = PIPE, stderr = STDOUT)
        stdout, _ = await process.communicate()
        logging.info(stdout.decode())
        self.downloaded = True
        return

    def _run_ytdl_noasync(self, url):
        logging.info(f"Downloading {url}.")
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
            await self._run_ytdl()
            if self._file_exists():
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

    async def shuffle_queue(self):
        random.shuffle(self.queue)
        return

    async def _get_queue(self):
        try:
            return self.queue.pop(0)
        except IndexError:
            raise RuntimeError("Queue is empty.")

    def _get_queue_nopop(self):
        try:
            return self.queue[0]
        except IndexError:
            raise RuntimeError("Queue is empty.")

    async def play(self, music, message):
        self.channel = message.channel
        await self.add_queue(music)
        if not await self.is_playing():
            await self._play()

    async def _play(self):
        music = await self._get_queue()
        embed = await Bot.get_embed(
            title = "Music",
            desc = f"**{await self.get_name()}: Downloading [{music.name}]({music.url})...**",
            sender = music.adder)
        embed.set_thumbnail(url = music.thumbnail)
        msg = await self.channel.send(embed = embed)
        src = await music.get()
        self.client.play(src, after = self._play_wrap)
        embed = await Bot.get_embed(
            title = "music",
            desc = f"**{await self.get_name()}: Now playing [{music.name}]({music.url}).**",
            sender = music.adder)
        embed.set_thumbnail(url = music.thumbnail)
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
        raise RuntimeError("Not connected to any voice channel in this server.")




# [join/leave/play/stop/skip/pause/resume/current/queue]
async def main(message, **kwargs):
    cmd = message.content.split()
    bot_client = kwargs['client']
    if len(cmd) == 1:
        raise ValueError("You have to input the command.")
    else:
        if cmd[1] == "join":
            func = join
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
        elif cmd[1] == "queue":
            func = queue
        elif cmd[1] == "leave_all":
            func = leave_all
        elif cmd[1] == "shuffle":
            func = shuffle
        else:
            raise ValueError(f"Unknown command: {cmd[1]}.")
        logging.info("Running " + cmd[1])
        try:
            async for msgtxt in func(message):
                yield msgtxt
        except TypeError:
            async for msgtxt in func(message, bot_client):
                yield msgtxt

async def join(message, bot_client):
    member = message.author
    if not type(member) == discord.Member:
        raise TypeError("message.author value's type is not discord.Member. Are you sure you're using this command in the server?")
    voice = member.voice
    if voice == None:
        raise RuntimeError("You are not connected to voice channel.")
    client = await voice.channel.connect()
    clients[message.guild.id] = await get_class(server_client, client, bot_client)
    yield f"Joined {client.channel.name} channel."

async def leave(message):
    client = await get_client(message)
    channel_name = await client.get_name()
    await client.nuke_queue()
    await client.leave()
    del clients[message.guild.id]
    yield f"Left {channel_name} channel."

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
        raise ValueError("You have to input the URL to play/query to search.")
    usrinput = message.content[len(cmd[0]) + len(cmd[1]) + 2:]
    yield f"Loading {usrinput}..."
    plname, video = await get_vid(usrinput)
    if plname is None:
        yield f"Loading {video[2]}..."
        music = music_file(*video, message.author)
        yield f"Adding {video[2]} to queue..."
        await client.play(music, message)
        yield f"Succesfully added {video[2]} to the queue."
    else:
        yield f"Loading {plname}..."
        music = [music_file(*_video, message.author) for _video in video]
        yield f"Adding {plname} to queue..."
        await client.play(music, message)
        yield f"Succesfully added {plname} to the queue. first song is: {video[0][2]}."

async def stop(message):
    client = await get_client(message)
    await client.nuke_queue()
    await client.stop()
    yield "Paused the song, and erased the queue."

async def skip(message):
    client = await get_client(message)
    await client.stop()
    yield "Skipping current song."

async def pause(message):
    client = await get_client(message)
    await client.pause()
    yield "Pausing the song."

async def resume(message):
    client = await get_client(message)
    await client.resume()
    yield "Resuming the song."

async def queue(message):
    client = await get_client(message)

    cmd = message.content.split()
    if len(cmd) == 2:
        page = 0
    else:
        if len(cmd) != 3:
            raise ValueError("You can only input one page number.")
        try:
            page = int(cmd[2]) - 1
        except ValueError:
            raise ValueError("Requested page number is not a number.")

    queue = await client.list_queue()
    splitqueue = [queue[n:n + 10] for n in range(0, len(queue), 10)]
    
    if page >= len(splitqueue):
        raise ValueError("Page number is bigger than the amout of the page.")
    yield "\n".join([f"{numb + (page * 10)}. [{music.name}]({music.url})" for music, numb in zip(splitqueue[page], range(1, 11))]) + \
    f"\n{page + 1}/{len(splitqueue)}"

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

async def shuffle(message):
    client = await get_client(message)
    await client.shuffle_queue()
    yield "Shuffled the queue succesfully."