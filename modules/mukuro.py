PERMISSION = 6

HELP = '"무쿠로", "Mukuro", "むくろ" 라는 단어에 반응합니다.'

async def main(message):
    if message.author.bot:
        return
    if "무쿠로" in message.content:
        return "이쿠사바 무쿠로... 이 학교에 숨은 16번째 고교생... \"초고교급 절망\"이라 불리는 여고생... 이쿠사바 무쿠로를 조심해."
    elif "mukuro" in message.content.lower():
        return "Mukuro Ikusaba. The 16th student, hiding somewhere in the Academy. The one they call Ultimate Despair. Watch out for her."
    elif "むくろ" in message.content:
        return "戦刃むくろ···この学園に潜む16人目の高校生···超高校の望と呼ばれる女子高校生···戦刃むくろに気を付けて。"