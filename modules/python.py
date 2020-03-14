import asyncio
from asyncio.subprocess import PIPE, STDOUT

TYPE = "owner"

HELP = """\
Execute the python code. This will open another interpreter using `python -c` \
so You won't be able to access variables on the userbot itself.
Usage: execute [commands]\
"""

async def main(message, **kwargs):
    cmd = message.content
    cmdsplit = cmd.split()
    if len(cmdsplit) == 1:
        raise ValueError("Command should contain commands to run.")
    else:
        code = cmd.replace(cmdsplit[0], "")
        yield f"Running {code}. Please Wait..."
        process = await asyncio.create_subprocess_exec("python", "-c", code, stdout = PIPE, stderr = STDOUT)
        stdout, _ = await process.communicate()
        yield "```" + stdout.decode() + "```"