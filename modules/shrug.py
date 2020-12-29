PERMISSION = 6

HELP = ':shrug:'

async def main(message):
    if message.author.bot:
        return
    if "shrug" in message.content or "¯\_(ツ)_/¯" in message.content:
        return "¯\_(ツ)_/¯"

