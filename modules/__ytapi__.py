import os
import json
import logging
import aiofiles
import textwrap
import threading
import requests_async as requests

BASEPATH = os.path.dirname(os.path.abspath(__file__))
PATH = os.path.join(BASEPATH, "__music__")
KEYPATH = os.path.join(PATH, "yt_api_key")

async def get_key(path = KEYPATH):
    try:
        async with aiofiles.open(path) as f:
            key = await f.read()
    except FileNotFoundError:
        logging.info(f"Can't find {path}. Creating one...")
        key = input("Enter your API Key here. type \"noapi\" to use noapi method instead.: ")
        logging.info("Saving api_key...")
        # open(path, "w").write(key)
        try:
            async with aiofiles.open(path, "w") as f:
                await f.write(key)
        except:
            logging.info(f"Can't find {os.path.dirname(path)}, Creating one...")
            os.mkdir(os.path.dirname(path))
            async with aiofiles.open(path, "w") as f:
                await f.write(key)
    return key

async def get_playlist_name(playlistid):
    key = await get_key()
    pagetoken = ""
    videos = []
    r = await requests.get(f"https://www.googleapis.com/youtube/v3/playlists?part=snippet&maxResults=1&id={playlistid}&key={key}")
    response = json.loads(r.text)
    return response['items'][0]['snippet']['title']

async def get_playlist(playlistid, videoid = None):
    key = await get_key()
    pagetoken = ""
    playlist_name = await get_playlist_name(playlistid)
    videos = []
    while True:
        r = await requests.get(f"https://www.googleapis.com/youtube/v3/playlistItems?part=snippet&maxResults=50&pageToken={pagetoken}&playlistId={playlistid}&key={key}")
        response = json.loads(r.text)
        try:
            for video in response['items']:
                video = video['snippet']
                name = video['title']
                if name in ["Private video", "Deleted video"]:
                    continue
                vid_id = video['resourceId']['videoId']
                try:
                    thumbnail = video['thumbnails']['maxres']['url']
                except KeyError:
                    try:
                        thumbnail = video['thumbnails']['standard']['url']
                    except KeyError:
                        thumbnail = video['thumbnails']['high']['url']
                videos.append(("yt", vid_id, name, thumbnail))
            try:
                pagetoken = response['nextPageToken']
            except:
                break
        except:
            logging.info(video)
            raise
    if videoid:
        videos_beforevid = []
        while not videos[0][1] == videoid:
            videos_beforevid.append(videos.pop(0))
        videos.extend(videos_beforevid)
    return playlist_name, tuple(videos)

async def get_vid_info(videoid):
    key = await get_key()
    r = await requests.get(f"https://www.googleapis.com/youtube/v3/videos?part=snippet,id&maxResults=1&id={videoid}&key={key}")
    response = json.loads(r.text)
    video = response['items'][0]
    try:
        thumbnail = video['snippet']['thumbnails']['maxres']['url']
    except KeyError:
        try:
            thumbnail = video['snippet']['thumbnails']['standard']['url']
        except KeyError:
            thumbnail = video['snippet']['thumbnails']['high']['url']
    return ("yt", video['id'], video['snippet']['title'], thumbnail)

async def search_video(query, maxresults = 1):
    key = await get_key()
    videos = []
    r = await requests.get(f"https://www.googleapis.com/youtube/v3/search?part=snippet&maxResults={str(maxresults)}&q={query}&key={key}")
    response = json.loads(r.text)
    logging.info(response)
    for video in response['items']:
        try:
            thumbnail = video['snippet']['thumbnails']['maxres']['url']
        except KeyError:
            try:
                thumbnail = video['snippet']['thumbnails']['standard']['url']
            except KeyError:
                thumbnail = video['snippet']['thumbnails']['high']['url']
        videos.append(("yt", video['id']['videoId'], video['snippet']['title'], thumbnail))
    return tuple(videos)