import subprocess
from subprocess import PIPE, STDOUT

TYPE = "owner"
IS_ASYNC = False

HELP = """\
Execute the python code using eval().
Usage: eval [commands]\
"""

def main(message):
    cmd = message.content
    cmdsplit = cmd.split()
    if len(cmdsplit) == 1:
        raise ValueError("Command should contain commands to run.")
    else:
        code = cmd.replace(cmdsplit[0] + " ", "")
        yield f"Running {code}. Please Wait..."
        result = eval(code)
        yield "```" + str(result) + "```"