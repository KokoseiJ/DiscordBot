import subprocess
from subprocess import PIPE, STDOUT

PERMISSION = 1

HELP = """\
Execute the python code using eval().
Usage: eval [commands]\
"""

async def main(message, **kwargs):
    cmd = message.content
    cmdsplit = cmd.split()
    if len(cmdsplit) == 1:
        raise ValueError("Command should contain commands to run.")
    else:
        code = cmd.replace(cmdsplit[0], "")
        yield f"Running {code}. Please Wait..."
        result = exec(code)
        yield "`" + str(result) + "`"

