PERMISSION = 6

HELP = '"하라는 코딩은 안하고!" 라는 문장에 반응합니다.'

async def main(message):
    if ";;" in message.content:
        return "하라는 코딩은 안하고!"
