TYPE = "private"

HELP = """\
Send the message under the name of the bot.
Usage: echo [message]\
"""

async def main(message, **kwargs):
    cmd = message.content.split()
    if len(cmd) == 1:
        raise ValueError("Command should contain messages to echo.")
    else:
        text = cmd[1:]
    await message.delete()
    yield "noembed|" + " ".join(text)