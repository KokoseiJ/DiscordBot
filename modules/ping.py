import subprocess
from subprocess import PIPE, STDOUT

TYPE = "public"

HELP = """\
Pinging the given server.
Usage: ping [address]\
"""

def main(message):
    cmd = message.content.split()
    if len(cmd) == 1:
        address = "google.com"
    else:
        address = cmd[1]
    yield f"Pinging {address}. Please Wait..."
    process = subprocess.run(["ping", address, "-c", "4"], stdout = PIPE, stderr = STDOUT)
    avr_ping = process.stdout.decode().split("\n")[-2].split("/")[-3]
    yield f"Pong!\nAverage ping time to {address} is {avr_ping}."