import subprocess
from subprocess import PIPE, STDOUT

TYPE = "owner"
IS_ASYNC = False

HELP = """\
Execute the python code. This will open another interpreter using `python -c` \
so You won't be able to access variables on the userbot itself.
Usage: execute [commands]\
"""

def main(message):
    cmd = message.content
    cmdsplit = cmd.split()
    if len(cmdsplit) == 1:
        raise ValueError("Command should contain commands to run.")
    else:
        code = cmd.replace(cmdsplit[0] + " ", "")
        yield f"Running {code}. Please Wait..."
        process = subprocess.run(["python", "-c", code], stdout = PIPE, stderr = STDOUT)
        yield "```" + process.stdout.decode() + "```"