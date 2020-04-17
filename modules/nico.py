import io
import os
import sys
import json
import time
import httpx
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

sys.path.insert(0, os.path.dirname(PATH))
from bot_func import Bot

logger = logging.getLogger()

PERMISSION = 1
HELP = """\
Plays the music from `nicovideo.jp`.
Usage: nico [play/stop/pause/resume/skip/queue/shuffle]
"""

NICOVIDEO_URL = "https://www.nicovideo.jp/watch/{0}"
NICO_LOGINURL = "https://account.nicovideo.jp/login/redirector"

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
                if not page:
                    return b""
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
    def __init__(self, url, title, author, thumbnail, adder):
        self.url = url
        self.title = title
        self.author = author
        self.thumbnail = thumbnail
        self.adder = adder

        self.download_in_progress = threading.Event()
        self.download_done = threading.Event()

        # This argument will decode the audio stream from mp4 to PCM
        """
        self.ffmpeg_args = [
            "ffmpeg", "-vn",
            "-i", "-",
            "-f", "s16le",
            "-ar", "48000",
            "-ac", "2",
            "-"
        ]
        """
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

    def cleanup(self):
        return

class NicoStream(BotMusicStream):
    def __init__(self, session, info, adder):
        self.info = info
        self.session = session

        url = NICOVIDEO_URL.format(info['video']['id'])
        title = info['video']['title']
        author = info['owner']['nickname']
        thumbnail = info['video']['largeThumbnailURL']

        super().__init__(url, title, author, thumbnail, adder)

class NicoDMCStream(NicoStream):
    def __init__(self, session, info, adder):
        #self.bytestream = ThreadSafeBytesIO()
        #self.oggparser = OggParser(self.bytestream)
        #self.packet_iter = self.oggparser.packet_iter()

        super().__init__(session, info, adder)

    def _download(self):
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

class NicoSmileStream(NicoStream):
    def _download(self):
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

    def read(self):
        framesize = discord.opus.Encoder.FRAME_SIZE
        """
        rtnbyte = b""
        while len(rtnbyte) < framesize:
            print("read")
            rtnbyte = self.ffmpeg_process.stdout.read(
                framesize - len(rtnbyte)
            )
            if len(rtnbyte) < framesize and self.download_done.is_set():
                print("read done")
                return b""
        return rtnbyte
        """
        return next(self.packet_iter, b"")

    def is_opus(self):
        return True

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

def nico_get_session():
    session = requests.session()
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

async def main(message, *args, **kwargs):
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

if __name__ == "modules.nico":
    SESSION = nico_get_session()
