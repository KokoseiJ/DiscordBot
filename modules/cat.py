# -*- coding: utf-8 -*-

import aiohttp
import discord

PERMISSION = 6

HELP = '"고양이", "야옹", "meow", "cat" 이라는 단어에 반응합니다.'


class CatWorker:
    def __init__(self, message):
        self.message = message
        
    async def __get_cat(self):
        async with aiohttp.ClientSession() as session:
            # 기존api(https://aws.random.cat/meow) 503에러로 인하여 자체 api로 변경
            async with session.get("https://api.chick.ga/api") as resp:
                return await resp.json()

    async def send_cat(self, filtered, color=0xFCFCFC):
        cat_data = await self.__get_cat()

        embed = discord.Embed(title=f"{filtered}!", color=color)
        embed.set_image(url=cat_data['file'].replace("\\", ''))
        await self.message.channel.send(embed=embed)


async def main(message):
    if message.author.bot:
        return

    cat_filter = ["고양이", "야옹", "meow", "cat"]
    for check in cat_filter:
        if check in str(message.content).lower():
            worker = CatWorker(message)
            await worker.send_cat(check)
