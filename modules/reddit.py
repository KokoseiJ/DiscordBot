import os
import sys
import httpx
import logging
from bs4 import BeautifulSoup as bs

PATH = os.path.dirname(os.path.abspath(__file__))

from modules.util import Bot

PERMISSION = 5

HELP = """\
Get a random post from subreddit.
Usage: reddit <name of subreddit> [hot/new/random/rising/top/controversial]
"""

REDDIT_BASEURL = "https://www.reddit.com"
REDDIT_SUBREDDIT_URL = REDDIT_BASEURL + "/r/{subreddit}/{sort}/.json"

async def main(message, **kwargs):
    cmd = message.content.split()[1:]
    if len(cmd) < 1:
        raise ValueError("You have to specify the subreddit to search.")
    elif len(cmd) > 2:
        raise ValueError("Too many arguments")
    elif len(cmd) == 2 and not cmd[1] in ["hot", "new", "random", "rising", "top", "controversial"]:
        raise ValueError("Wrong sort type")
    subreddit = cmd[0]
    if len(cmd) == 1:
        sort = "random"
    else:
        sort = cmd[1]
    async with httpx.AsyncClient() as client:
        r = await client.get(
            REDDIT_SUBREDDIT_URL.format(subreddit = subreddit, sort = sort),
            headers = {"User-Agent": "Kyoko_Kirigiri_Bot"}
        )
    r.raise_for_status()
    data = r.json()
    try:
        try:
            postdatas = data[0]["data"]["children"]
        except KeyError:
            postdatas = data["data"]["children"]
        for postdata in [x['data'] for x in postdatas]:
            if postdata['stickied']:
                continue
            posturl = REDDIT_BASEURL + postdata['permalink']
            posttitle = postdata['title']
            embed = await Bot.get_embed(
                title = posttitle,
                desc = postdata['selftext'],
                sender = message.author,
                url = posturl
                )
            if not postdata['is_self']:
                if postdata['is_video']:
                    embed.set_image(url = postdata['preview']['images'][0]['source']['url'])
                else:
                    embed.set_image(url = postdata['url'])
            print(posturl, postdata['url'])
            yield embed
            return
    except:
        if data['data']['dist'] == 0:
            raise RuntimeError("That subreddit does not exist.")
        logging.info(data)
        raise RuntimeError("Unknown Error occured!")
