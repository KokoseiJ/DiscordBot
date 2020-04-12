import logging
import requests_async as requests
from bs4 import BeautifulSoup as bs

PERMISSION = 5

HELP = """\
Search the google using the given query.
Usage: google [QUERY TO SEARCH]
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
    url = f"https://www.google.com/search?q={query}"
    r = await requests.get(url)
    soup = bs(r.text, "html.parser")
    searchres = soup.find("body").find("div", {"id":"main"})\
    .find_all("div", {"class":["ZINbbc", "xpd", "09g5cc", "uUPGi"]})
    searchlist = [(res.find("div", {"class":["BNeawe", "vvjwJb", "AP7Wnd"]}).text,
                  res.find("a")['href'].replace("/url?q=", "https://www.google.com/url?q="))
                  for res in searchres
                  if res.find("a")['href'].startswith("/url?q=")]
    yield "\n\n".join([f"[{res[0]}]({res[1]})" for res in searchlist][:5])