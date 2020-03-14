import asyncio
from asyncio.subprocess import PIPE, STDOUT

TYPE = "owner"

HELP = """\
Execute the linux command.
Usage: execute [commands]\
"""

async def main(message, **kwargs):
    cmd = message.content.split()
    if len(cmd) == 1:
        raise ValueError("Command should contain commands to run.")
    else:
        cmd_txt = " ".join(cmd[1:])
        yield f"Executing {cmd_txt}. Please Wait..."
        process = await asyncio.create_subprocess_exec(cmd[1], *cmd[2:], stdout = PIPE, stderr = STDOUT)
        stdout, _ = await process.communicate()
        yield "```" + stdout.decode() + "```"