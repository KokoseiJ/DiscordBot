import io
import os
import sys
import json
import time
import httpx
import random
import struct
import asyncio
import discord
import logging
import aiofiles
import requests
import threading
import subprocess
from discord import oggparse
from bs4 import BeautifulSoup as bs
from subprocess import PIPE, DEVNULL

PATH = os.path.dirname(os.path.abspath(__file__))

from modules.util import Bot

logger = logging.getLogger()

PERMISSION = 5
HELP = """\
Plays the music from `nicovideo.jp`.
Usage: nico [play/stop/pause/resume/skip/queue/shuffle/repeat/leave]
You can input the query to search in nicovideo, content ID(sm*******), or the url of the video.
"""

NICOVIDEO_URL = "https://www.nicovideo.jp/watch/{0}"
NICO_LOGINURL = "https://account.nicovideo.jp/login/redirector"
NICO_GETTHUMBINFO_URL = "https://ext.nicovideo.jp/api/getthumbinfo/{0}"

def nico_dmc_get_postdata(info):
    return json.dumps({
    "session": {
        "recipe_id": info['video']['dmcInfo']['session_api']['recipe_id'],
        "content_id": info['video']['dmcInfo']['session_api']['content_id'],
        "content_type": "movie",
        "content_src_id_sets": [
            {
                "content_src_ids": [
                    {
                        "src_id_to_mux": {
                            # Get lowest setting of video, highest setting of audio
                            "video_src_ids": [info['video']['dmcInfo']['session_api']['videos'][-1]],
                            "audio_src_ids": [info['video']['dmcInfo']['session_api']['audios'][0]]
                        }
                    }
                ]
            }
        ],
        "timing_constraint": "unlimited",
        "keep_method": {
            "heartbeat": {
                "lifetime": info['video']['dmcInfo']['session_api']['heartbeat_lifetime']
            }
        },
        "protocol": {
            "name": info['video']['dmcInfo']['session_api']['protocols'][0],
            "parameters": {
                "http_parameters": {
                    "parameters": {
                        "hls_parameters": {
                            "use_well_known_port": "yes",
                            "use_ssl": "yes",
                            "transfer_preset": "",
                            "segment_duration": 6000
                        }
                    }
                }
            }
        },
        "content_uri": "",
        "session_operation_auth": {
            "session_operation_auth_by_signature": {
                "token": info['video']['dmcInfo']['session_api']['token'],
                "signature": info['video']['dmcInfo']['session_api']['signature']
            }
        },
        "content_auth": {
            "auth_type": info['video']['dmcInfo']['session_api']['auth_types'][info['video']['dmcInfo']['session_api']['protocols'][0]],
            "content_key_timeout": info['video']['dmcInfo']['session_api']['content_key_timeout'],
            "service_id": "nicovideo",
            "service_user_id": info['video']['dmcInfo']['session_api']['service_user_id']
        },
        "client_info": {
            "player_id": info['video']['dmcInfo']['session_api']['player_id']
        },
        "priority": info['video']['dmcInfo']['session_api']['priority']
    }
})

class OggParser:
    def __init__(self, pipe):
        self.pipe = pipe

    def packet_iter(self):
        while True:
            for page in self._page_iter():
                if page is None:
                    yield b""
                    return
                for packet in page:
                    yield packet

    def _page_iter(self):
        magicheader = self.pipe.read(4)
        if magicheader == b"OggS":
            yield self._packet_iter()
        elif not magicheader:
            yield None
            return
        else:
            raise ValueError("Invalid Ogg Header")

    def _packet_iter(self):
        header_struct = struct.Struct("<BBQIIIB")

        version, flag, granule_pos,\
        serial, page_seq, checksum,\
        page_seg = header_struct.unpack(
            self.pipe.read(header_struct.size)
        )
        seg_table = self.pipe.read(page_seg)

        packet_size = 0

        for table_value in seg_table:
            packet_size += table_value
            if table_value == 255:
                continue
            else:
                packet = self.pipe.read(packet_size)
                packet_size = 0
            yield packet

# Unused - Should be deleted later
class ThreadSafeBytesIO(io.BytesIO):
    def __init__(self, *args, **kwargs):
        self.byte_rw_lock = threading.Lock()
        super().__init__(*args, **kwargs)
    def read(self, *args, **kwargs):
        self.byte_rw_lock.acquire()
        rtnbyte = super().read(*args, **kwargs)
        self.byte_rw_lock.release()
        return rtnbyte
    def write(self, *args, **kwargs):
        self.byte_rw_lock.acquire()
        prevoffset = self.seek(0, 1)
        self.seek(0, 2)
        rtnbyte = super().write(*args, **kwargs)
        self.seek(prevoffset)
        self.byte_rw_lock.release()
        return rtnbyte

class BotMusicStream(discord.AudioSource):
    def __init__(self, url, title, thumbnail, adder):
        self.url = url
        self.title = title
        self.thumbnail = thumbnail
        self.adder = adder

        self.download_in_progress = threading.Event()
        self.download_done = threading.Event()

        self.ffmpeg_args = [
            "ffmpeg", "-vn",
            "-i", "-",
            "-f", "opus",
            "-"
        ]

    async def prepare(self):
        # 다른 스레드에서 다운로드 시작하고 플레이 가능할때까지 asyncio.sleep()
        self.download_thread = threading.Thread(
            target = self._download
        )
        self.download_thread.start()
        while not self.download_in_progress.is_set():
            await asyncio.sleep(0.1)
        return

    def _download(self):
        raise NotImplementedError()

    def read(self):
        raise NotImplementedError()

    def cleanup(self):
        return

class NicoStream(BotMusicStream):
    def __init__(self, contentid, session, thumbinfo, adder):
        self.adder = adder
        self.session = session
        self.contentid = contentid

        url = NICOVIDEO_URL.format(contentid)

        title = thumbinfo['title']
        thumbnail = thumbinfo['thumbnail']

        super().__init__(url, title, thumbnail, adder)

    async def prepare(self):
        info = await nico_get_info(self.session, self.url)
        self.info = info

        if info['video']['dmcInfo']:
            self.download_thread = threading.Thread(
                target = self._download_dmc
            )
        else:
            self.download_thread = threading.Thread(
                target = self._download_smile
            )

        # 다른 스레드에서 다운로드 시작하고 플레이 가능할때까지 asyncio.sleep()
        self.download_thread.start()
        while not self.download_in_progress.is_set():
            await asyncio.sleep(0.1)
        return

    def _download_dmc(self):
        # info에서 데이터 긁어와서 API 보내고 하트비트 시작한 후
        # m3u8 긁어와서 다운받고 bytearray에 작성
        api_url = self.info['video']['dmcInfo']['session_api']['urls'][0]['url']
        data = nico_dmc_get_postdata(self.info)
        api_request = self.session.post(
            api_url + "?_format=json",
            headers = {"Content-Type": "application/json"},
            data = data
        )
        api_request.raise_for_status()
        api_result = api_request.json()

        self.heartbeat_thread = threading.Thread(
            target = self._heartbeat,
            args = (api_url, api_result['data'])
        )
        self.heartbeat_thread.start()

        m3u8_baseurl = api_result['data']['session']['content_uri'].split("master.m3u8")[0]
        m3u8_master = self.session.get(
            api_result['data']['session']['content_uri']
        ).text
        m3u8_playlist_url = m3u8_baseurl + m3u8_master.split()[-1]
        m3u8_baseurl = m3u8_playlist_url.split("playlist.m3u8")[0]
        m3u8_playlist = self.session.get(m3u8_playlist_url).text
        ts_list = [
            m3u8_baseurl + entry
            for entry in m3u8_playlist.split("\n")
            if entry and not entry.startswith("#")
        ]
    
        self.ffmpeg_process = subprocess.Popen(
            self.ffmpeg_args,
            stdin = PIPE,
            stdout = PIPE,
            stderr = DEVNULL
        )
    
        self.oggparser = OggParser(self.ffmpeg_process.stdout)
        self.packet_iter = self.oggparser.packet_iter()
        
        self.download_in_progress.set()
        for ts_url in ts_list:
            ts = self.session.get(ts_url, stream = True)
            ts.raise_for_status()
            
            for chunk in ts.iter_content(8192):
                self.ffmpeg_process.stdin.write(chunk)
                if self.download_done.is_set():
                    return
        self.ffmpeg_process.stdin.close()
        self.download_done.set()
        return

    def _download_smile(self):
        url = self.info['video']['smileInfo']['url']
        video = self.session.get(url, stream = True)
        video.raise_for_status()
        self.ffmpeg_process = subprocess.Popen(
            self.ffmpeg_args,
            stdin = PIPE,
            stdout = PIPE,
            stderr = DEVNULL
        )

        self.oggparser = OggParser(self.ffmpeg_process.stdout)
        self.packet_iter = self.oggparser.packet_iter()

        self.download_in_progress.set()
        for chunk in video.iter_content(8192):
            self.ffmpeg_process.stdin.write(chunk)
            if self.download_done.is_set():
                return
        self.ffmpeg_process.stdin.close()
        self.download_done.set()
        return

    def _heartbeat(self, api_url, data, interval = 40):
        url = api_url + "/" +\
              data['session']['id'] + \
              "?_format=json&_method=PUT"
        while True:
            heartbeat_request = self.session.post(
                url,
                headers = {"Content-Type": "application/json"},
                data = json.dumps(data)
            )
            heartbeat_request.raise_for_status()
            data = heartbeat_request.json()['data']
            if self.download_done.wait(timeout = interval):
                return

    def read(self):
        return next(self.packet_iter, b"")

    def is_opus(self):
        return True

class VoiceQueue:
    def __init__(self, client):
        self.client = client
        self.channel = None
        self.queue = []
        self.repeat = False

    def set_repeat(self):
        self.repeat = not self.repeat
        return self.repeat

    def add_queue(self, item):
        if isinstance(item, BotMusicStream):
            return self.queue.append(item)
        else:
            return self.queue.extend(item)

    def list_queue(self):
        return self.queue.copy()

    def nuke_queue(self):
        return self.queue.clear()

    def shuffle_queue(self):
        return random.shuffle(self.queue)

    def get_queue(self):
        try:
            return self.queue.pop(0)
        except IndexError:
            raise RuntimeError("Queue is empty.")

    async def play(self, music, channel):
        self.channel = channel
        self.add_queue(music)
        if not self.client.is_playing():
            await self._play()

    async def _play(self):
        music = self.source = self.get_queue()
        embed = await Bot.get_embed(
            title = "music",
            desc = f"**{self.client.channel.name}: Downloading [{music.title}]({music.url})...**",
            sender = music.adder)
        embed.set_thumbnail(url = music.thumbnail)
        msg = await Bot.send_msg(self.channel, embed)
        await music.prepare()
        self.client.play(music, after = self._play_wrap)
        embed = await Bot.get_embed(
            title = "music",
            desc = f"**{self.client.channel.name}: Now playing [{music.title}]({music.url}).**",
            sender = music.adder)
        embed.set_thumbnail(url = music.thumbnail)
        await Bot.edit_msg(msg, embed)

    def _play_wrap(self, error = None):
        if error:
            raise error
        else:
            if self.repeat:
                self.add_queue(self.source)
            coro = self._play()
            fut = asyncio.run_coroutine_threadsafe(
                coro, self.client.loop
            )

async def nico_get_info(session, url):
    loop = asyncio.get_event_loop()
    r = await loop.run_in_executor(
        None,
        session.get,
        url
    )

    soup = bs(r.text, "html.parser")
    return json.loads(
        soup.find(
            id = "js-initial-watch-data"
        )['data-api-data']
    )

async def nico_get_thumbinfo(session, contentid):
    loop = asyncio.get_event_loop()
    r = await loop.run_in_executor(
        None,
        session.get,
        NICO_GETTHUMBINFO_URL.format(contentid)
    )
    soup = bs(r.text, "html.parser")
    return {
        "title": soup.thumb.title.text,
        "thumbnail": soup.thumb.thumbnail_url.text
    }

async def nico_get_mylist(url, session):
    loop = asyncio.get_event_loop()
    name = None
    r = await loop.run_in_executor(
        None,
        requests.get,
        url
    )
    soup = bs(r.text, "html.parser")
    name = soup.find("div", id = "PAGEBODY")\
        .find_all("script")[-4]\
        .string\
        .split("MylistGroup.preloadSingle(")[1]\
        .split("name:")[1].split("\"")[1].split("\"")[0]

    vidlist = []
    prev_json = None
    page = 0
    while True:
        page += 1
        r = await loop.run_in_executor(
            None,
            requests.get,
            f"{url}#+page={page}"
        )
        soup = bs(r.text, "html.parser")
        listtxt = soup.find("div", id = "PAGEBODY")\
            .find_all("script")[-4]\
            .string\
            .split("Mylist.preload")[1]\
            .split(", ", 1)[1].split(");")[0]
        jsonlist = json.loads(listtxt)
        if jsonlist == prev_json:
            break
        vidlist.extend([
            (   
                vid['item_data']['video_id'],
                {
                    "title": vid['item_data']['title'],
                    "thumbnail": vid['item_data']['thumbnail_url']
                }
            )
            for vid in jsonlist
            ])
        prev_json = jsonlist
    return name, vidlist

async def nico_search(q, session):
    loop = asyncio.get_event_loop()
    r = await loop.run_in_executor(
        None,
        session.get,
        f"https://api.search.nicovideo.jp/api/v2/snapshot/video/contents/search?targets=title,description,tags&fields=contentId&_sort=viewCounter&_limit=1&q={q}"
    )
    result = r.json()
    if str(r.status_code)[0] == "5":
        raise RuntimeError(f"Error: Nicovideo server is currently unavailable.\nError Code: `{result['meta']['errorCode']}`\nError Message: `{result['meta']['errorMessage']}`")
    elif str(r.status_code)[0] == "4":
        raise RuntimeError(f"Error: There was an error while sending request to nicovideo server.\nError Code: `{result['meta']['errorCode']}`\nError Message: `{result['meta']['errorMessage']}`")
    elif not result['data']:
        raise RuntimeError(f"No results found.")
    return result['data'][0]['contentId']

def nico_get_session():
    session = requests.session()
    # Set User-Agent
    session.headers.update({"User-Agent": Bot.botname.replace(" ", "_")})
    # I prefer japanese server so I will use this cookie
    session.cookies.set("lang", "ja-jp")
    try:
        with open(os.path.join(PATH, "__music__", "nico_idpw")) as f:
            ID, PASSWD = [x.replace("\n", "") for x in f.readlines()]
        logger.info("ID/PASSWD present.logging in...")
        r = session.post(NICO_LOGINURL, data = {"mail_tel": ID, "password": PASSWD})
        if not "user_session" in list(session.cookies.get_dict()):
            logger.warning("Failed to log in. fallback to non-login mode.\n" + list(session.cookies.get_dict()))
    except FileNotFoundError:
        ID = PASSWD = None
        logger.info("no ID/PASSWD was present, Downloading as a guest...")
    return session

async def _get_voice_client(guild, user):
    client = guild.voice_client
    if client is None:
        voice = user.voice
        if voice is None:
            raise RuntimeError("Error: User is not connected to any voice channel")
        client = await voice.channel.connect()
    return client

async def get_voice_client(guild, user):
    try:
        client = voice_clients[str(guild.id)]
        if not client.client.is_connected():
            client.cient = await _get_voice_client(guild, user)
        return client
    except KeyError:
        client = await _get_voice_client(guild, user)
        voice_clients[str(guild.id)] = VoiceQueue(client)
        return voice_clients[str(guild.id)]

voice_clients = {}

async def test(message, *args, **kwargs):
    yield "스크립트를 시작한!"
    member = message.author
    if not type(member) == discord.Member:
        raise TypeError("에러: 서버가 아닌!")
    voice = member.voice
    if voice == None:
        raise RuntimeError("에러: 보이스채널에 들어가있지 않은!")
    client = await voice.channel.connect()
    nicourl = message.content.split()[-1]
    info = await nico_get_info(SESSION, nicourl)
    if info['video']['dmcInfo']:
        yield "DMC 영상이 감지된. 로드하는."
        teststream = NicoDMCStream(SESSION, info, message.author)
    else:
        yield "Smile 영상이 감지된. 로드하는."
        teststream = NicoSmileStream(SESSION, info, message.author)
    yield "다운로드 준비중..."
    await teststream.prepare()

    embed = await Bot.get_embed(
        title = "music",
        desc = f"**{client.channel.name}: Now playing [{teststream.author} - {teststream.title}]({teststream.url}).**",
        sender = teststream.adder)
    embed.set_thumbnail(url = teststream.thumbnail)
    client.play(teststream)
    yield embed

async def main(message, **kwargs):
    # play/stop/pause/resume/skip/queue/shuffle/leave
    cmd = message.content.split()[1:]
    if not cmd:
        yield "Usage: nico [play/stop/pause/resume/skip/queue/shuffle/leave]"
    elif cmd[0] == "play":
        if cmd[1].startswith("https://www.nicovideo.jp/mylist/"):
            name, vidlist = await nico_get_mylist(cmd[1], SESSION)
            streamlist = [
                NicoStream(
                    contentid,
                    SESSION,
                    thumbinfo,
                    message.author
                )
                for contentid, thumbinfo in vidlist
            ]
            client = await get_voice_client(message.guild, message.author)
            await client.play(streamlist, message.channel)
            yield f"Successfully added mylist[{name}]({cmd[1]})."
        else:
            if cmd[1].startswith("https://www.nicovideo.jp/watch/"):
                contentid = cmd[1].replace("https://www.nicovideo.jp/watch/", "")
            elif cmd[1].startswith("sm"):
                contentid = cmd[1]
            else:
                contentid = await nico_search(cmd[1], SESSION)
            client = await get_voice_client(message.guild, message.author)
            stream = NicoStream(
                contentid,
                SESSION,
                await nico_get_thumbinfo(
                    SESSION,
                    contentid
                ),
                message.author
            )
            await client.play(stream, message.channel)
            yield f"Successfully added [{stream.title}]({stream.url})."
    elif cmd[0] == "stop":
        client = await get_voice_client(message.guild, message.author)
        client.nuke_queue()
        client.repeat = False
        client.client.stop()
        yield "Stopped the playback and removed the queue."
    elif cmd[0] == "pause":
        client = await get_voice_client(message.guild, message.author)
        client.client.pause()
        yield "Paused."
    elif cmd[0] == "resume":
        client = await get_voice_client(message.guild, message.author)
        client.client.resume()
        yield "Resumed."
    elif cmd[0] == "skip":
        client = await get_voice_client(message.guild, message.author)
        client.client.stop()
    elif cmd[0] == "queue":
        client = await get_voice_client(message.guild, message.author)
        queue = client.list_queue()
        txtqueue = [
            f"[{music.title}]({music.url})"
            for music in queue
        ]
        splitqueue = [txtqueue[n:n + 10] for n in range(0, len(txtqueue), 10)]
        if len(cmd) == 1:
            page = 0
        else:
            try:
                page = int(cmd[1]) - 1
            except ValueError:
                raise ValueError(f"{cmd[1]} is not a number.")
        if page >= len(splitqueue):
            raise ValueError(f"{page} is bigger than the amount of existing page.")

        yield "\n\n".join([
            f"{numb}. {music}"
            for music, numb in zip(splitqueue[page], range(1, 11))
        ]) + f"\n\n{page + 1}/{len(splitqueue)}"
    elif cmd[0] == "shuffle":
        client = await get_voice_client(message.guild, message.author)
        client.shuffle_queue()
        yield "Shuffled the queue."
    elif cmd[0] == "repeat":
        client = await get_voice_client(message.guild, message.author)
        repeat = client.set_repeat()
        if repeat:
            yield "Enabled repeat."
        else:
            yield "Disabled repeat."
    elif cmd[0] == "leave":
        client = await get_voice_client(message.guild, message.author)
        await client.client.disconnect()
        del voice_clients[str(message.guild.id)]
        yield "Removed the queue and disconnected from the voice channel."
    else:
        yield "Usage: nico [play/stop/pause/resume/skip/queue/shuffle/leave]"
    return

if __name__ == "modules.nico":
    SESSION = nico_get_session()
