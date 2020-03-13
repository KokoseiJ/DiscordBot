TYPE = "private"

HELP = """\
Send the message under the name of the bot.
Usage: echo [message]\
"""

def main(message):
    cmd = message.content.split()
    if len(cmd) == 1:
        raise ValueError("Command should contain messages to echo.")
    else:
        text = cmd[1:]
    return "noembed|" + " ".join(text)