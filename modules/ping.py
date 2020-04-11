import asyncio
from asyncio.subprocess import PIPE, STDOUT

PERMISSION = 5

HELP = """\
Pinging the given server.
Usage: ping [address]\
"""

async def main(message, **kwargs):
    cmd = message.content.split()
    if len(cmd) == 1:
        address = "google.com"
    else:
        address = cmd[1]
    yield f"Pinging {address}. Please Wait..."
    process = await asyncio.create_subprocess_exec("ping", address, "-c", "4", stdout = PIPE, stderr = STDOUT)
    stdout, _ = await process.communicate()
    try:
        avr_ping = stdout.decode().split("\n")[-2].split("/")[-3]
    except IndexError:
        raise RuntimeError("Unexpected Response from ping. stdout:\n" + stdout.decode())
    yield f"Pong!\nAverage ping time to {address} is {avr_ping}."