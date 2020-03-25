# soup.find_all("table")[4]
import discord
import requests_async as requests
from bs4 import BeautifulSoup as bs

TYPE = "public"

HELP = """\
Search the image using google.
Usage: googleimg [QUERY TO SEARCH]
"""

#이름 = soup.find("body").find("div", {"id":"main"}).find_all("div", {"class":["ZINbbc", "xpd", "09g5cc", "uUPGi"]})[x].find("div", {"class":["BNeawe", "vvjwJb", "AP7Wnd"]}).text
#URL = soup.find("body").find("div", {"id":"main"}).find_all("div", {"class":["ZINbbc", "xpd", "09g5cc", "uUPGi"]})[x].find("a")['href'].replace("/url?q=")

async def main(message, **kwargs):
    loop = kwargs['client'].loop
    cmd = message.content.split()
    if len(cmd) == 1:
        raise ValueError("You have to provide words to search")
    query = message.content[len(cmd[0]):]
    yield f"Searching {query} in google..."
    url = f"https://www.google.com/search?tbm=isch&q={query}"
    r = await requests.get(url)
    soup = bs(r.text, "html.parser")
    imgurl = soup.find_all("table")[4].find("img")['src']
    embed = discord.Embed()
    embed.set_image(url = imgurl)
    await message.channel.send(embed = embed)
    yield ""