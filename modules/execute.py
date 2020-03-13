import subprocess
from subprocess import PIPE, STDOUT

TYPE = "owner"
IS_ASYNC = False

HELP = """\
Execute the linux command.
Usage: execute [commands]\
"""

def main(message):
    cmd = message.content.split()
    if len(cmd) == 1:
        raise ValueError("Command should contain commands to run.")
    else:
        cmd_txt = " ".join(cmd[1:])
        yield f"Executing {cmd_txt}. Please Wait..."
        process = subprocess.run(cmd[1:], stdout = PIPE, stderr = STDOUT)
        yield "```" + process.stdout.decode() + "```"