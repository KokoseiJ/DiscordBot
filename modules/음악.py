TYPE = "public"

HELP = """\
음악을 재생합니다.
사용 방법: 음악 [join/leave/play/pause/queue]\
"""

def main(message):
    cmd = message.content.split()
    if len(cmd) == 1:
        raise ValueError("명령어를 입력하여야 합니다.")
    else:
        if cmd[1] == "join":
            #return join(message)
            return "테스트"
        else:
            return f"알 수 없는 명령어: {cmd[1]}."

def join(message):pass