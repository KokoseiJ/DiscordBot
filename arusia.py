import discord
import asyncio
import requests

from bs4 import BeautifulSoup

client = discord.Client()

@client.event
async def on_ready(): 
    print("디스코드 봇 로그인이 완료되었습니다.")
    print("디스코드봇 이름:" + client.user.name)
    print("디스코드봇 ID:" + str(client.user.id))
    print("디스코드봇 버전:" + str(discord.__version__))
    print('------')
    answer = ""
    for i in range(len(client.guilds)):
        answer = answer + "■" + str(i+1) + "■: " + str(client.guilds[i]) + "(" + str(client.guilds[i].id) + ")\n"
    print("방목록: \n" + answer)
    await client.change_presence(status=discord.Status.online, activity=discord.Game("공중부양"))
    await client.change_presence(status=discord.Status.idle, activity=discord.Game("Prefix - >"))
    await asyncio.sleep(3.0)
    
@client.event
async def on_message(message):
    ms = list_message = message.content.split(' ')
    m = message.content
    if message.content == '>YahooLiveChart': 
        html = requests.get("https://search.yahoo.co.jp/realtime/search;?p=a").text
        answer = ''
        for i in range(20):
            cache1_html = html.split('<div><span>' + str(i+1) + '</span>')[1]
            data_cache = cache1_html.split('">')[1].split('</a>')[0]
            answer = answer + str(i+1) + ' -  ' + data_cache + '\n'
        embed = discord.Embed(title='[Yahoo Live Chart]', description=answer, color=0x00aa00)
        await message.channel.send(embed=embed)
        return
    if message.content.startswith('>실시간검색어'):
        html = requests.get("https://m.search.naver.com/search.naver?query=%EC%8B%A4%EC%8B%9C%EA%B0%84%20%EA%B2%80%EC%83%89%EC%96%B4").text
        data = html.split('span class="tit _keyword">')
        answer = ''
        embed = discord.Embed(title='[네이버 실시간 검색어 순위]', color=0x00aa00)
        for i in range(20):
            data_cache = data[i+1].split('</span>')[0]
            answer = answer + str(i+1) + '위: ' + data_cache + '\n'
        embed = discord.Embed(title='[네이버 실시간 검색어 순위]', description=answer, color=0x00aa00)
        await message.channel.send(embed=embed)
        return

@client.event
async def on_message(message):
    if message.author.bot or isinstance(message.channel, discord.abc.PrivateChannel):
        return

    if client.user.mentioned_in(message):
        if str(client.user.id) in message.content:
            embed = discord.Embed(title="Would you like to visit Hakodate?", description="Reservations for trains from Shin-Chitose Airport to Hakodate are available [here](https://jrhokkaidonorikae.com/pc/cgi/result.cgi?search_target=route&search_way=time&sum_target=7&faretype=2&jr=on&privately=on&dep_node=%E6%96%B0%E5%8D%83%E6%AD%B3%E7%A9%BA%E6%B8%AF&arv_node=%E5%87%BD%E9%A4%A8&via_node01=&via_node02=&via_node03=&year=2020&month=05&day=28&hour=10&minute=47&search_type=departure&sort=time&max_route=5&nearexpress=on&sprexprs=on&utrexprs=on&exprs=on&slputr=on&slpexprs=on&sprnozomi=on&transfer=normal). More can be found [here](https://www.jrhokkaido.co.jp/network/index.html).", color=0x00aaaa)
            await message.channel.send(embed=embed)
            try:
                await message.delete()
            except:
                pass

            return
        else:
            return
    content = message.content 
    guild = message.guild 
    author = message.author 
    channel = message.channel 
    if content.startswith(">NAGANO"): 
        await message.channel.send("DENTETSU")
    if content.startswith("Hakodate"):
        embed = discord.Embed(title="Pleack cheak your Direct Message.", description="私はあなたにDMでHakodateのヘルプを送ったよ。", color=0x00aaaa)
        await message.channel.send(embed=embed)  
        embed = discord.Embed(title="도움말",colour=0xBFE5E8)
        embed.add_field(name=">k_help", value=' - 명령어를 알려드립니다.', inline=False)
        embed.add_field(name=">청소 {청소할 메세지 갯수}", value=' - 사용자가 지정한만큼 메세지를 삭제합니다.', inline=False)
        embed.add_field(name=">문의", value=' - 문의, 또는 건의사항이 있으신가요? 연락처를 제공합니다.', inline=False)
        embed.add_field(name=">botinfo", value=' - 봇의 상세정보를 알려드립니다.', inline=False)
        embed.add_field(name=">19사이트모음", value=' - **반드시 nsfw 방에서만 사용하십시오!!**', inline=False)
        embed.add_field(name=">실시간검색어", value=' - 네이버의 현재 실검을 불러옵니다.', inline=False)
        user = client.get_user(int(message.author.id))
        await user.send(embed=embed)
    if content == "끼헦헦헦헦헦": 
        await message.channel.send("끼헦헦헦헦헦헦헦헦(어이상실)")
    if content == "노무현": 
        await message.channel.send("https://www.youtube.com/watch?v=u9hGFeBO4T8&list=PLFCdlMwym996PEczmAVX-ZOczOQpicbp-&index=11&t=0s 들어보쉴? (드디어 미침)")
    if content == ">개발자소개": 
        embed = discord.Embed(title="미친놈입니다",description="아니 진짜 미친놈이라고밖엔 설명이 안되는걸요", color=0x00aaaa)
        await message.channel.send(embed=embed)
    if content == ">愛は嫌いだ": 
        embed = discord.Embed(title="愛は嫌いだ",description="「妄想鑑賞対象連盟 中。 https://www.youtube.com/watch?v=Srj4FPLJe5g」", color=0x00aaaa)
        await message.channel.send(embed=embed)
    if content == ">페도라32라이젠3000호환성이슈기원": 
        embed = discord.Embed(title="봉준호님",description="「제사장이 코앞인데~」", color=0x00aaaa)
        await message.channel.send(embed=embed)
    if content == ">開発者": 
        embed = discord.Embed(title="問い合わせ事項がありますか?",description="問い合わせ事項及び提案事項はАshiуаlice#4462にご連絡下さい", color=0xf9a0f8)
    if content == ">나이": 
        embed = discord.Embed(title="장난하냐?",description="아무리 허본좌라도 니 나이는 모른다.", color=0xf9a0f8)
        await message.channel.send(embed=embed)
    if content == ">help": 
        embed = discord.Embed(title="Are You Korean? Japanese?",description="Kor Help -> >k_help, JP Help -> >J_help", color=0x00aaaa)
        await message.channel.send(embed=embed)
    if content == ">k_help": 
        embed = discord.Embed(title="도움말", color=0xBFE5E8)
        embed.add_field(name=">k_help", value=' - 명령어를 알려드립니다.', inline=False)
        embed.add_field(name=">청소 {청소할 메세지 갯수}", value=' - 사용자가 지정한만큼 메세지를 삭제합니다.', inline=False)
        embed.add_field(name=">문의", value=' - 문의, 또는 건의사항이 있으신가요? 연락처를 제공합니다.', inline=False)
        embed.add_field(name=">botinfo", value=' - 봇의 상세정보를 알려드립니다.', inline=False)
        embed.add_field(name=">19사이트모음", value=' - **반드시 nsfw 방에서만 사용하십시오!!**', inline=False)
        embed.add_field(name=">실시간검색어", value=' - 네이버의 현재 실검을 불러옵니다.', inline=False)
        await message.channel.send(embed=embed)
    if content == ">J_help": 
        embed = discord.Embed(title="ヘルプ", color=0xBFE5E8)
        embed.add_field(name=">J_help", value=' - ヘルプを表示します。', inline=False)
        embed.add_field(name=">clear {消すことがメッセージ数}", value=' - チャットウィンドウのメッセージをユーザーが指定した分だけ削除します。', inline=False)
        embed.add_field(name=">開発者", value=' - 本自動応答ボットの開発者を確認します。', inline=False)
        embed.add_field(name=">botinfo", value=' - 本自動応答ボットの詳細情報を確認します。', inline=False)
        embed.add_field(name=">YahooLiveChart", value=' - ヤフーのリアルタイム検索ワードチャートを読み込みます。', inline=False)
        await message.channel.send(embed=embed)
    if content == ">botinfo": 
        embed = discord.Embed(title="Bot info.", color=0xBFE5E8)
        embed.add_field(name="Bot Ver.", value='Ver.0.13 7XW', inline=True)
        embed.add_field(name="Firm ", value=' TEST/R " X', inline=True)
        embed.add_field(name="Developer", value='///#1012', inline=False)
        embed.add_field(name="Server Country", value=' Japan, Kobe - Sannomiya', inline=False)
        embed.add_field(name="Network", value=' KDDI - Stable 10Gbit, 15 / 19 sec.', inline=True)  
        await message.channel.send(embed=embed)
    if content == ">19사이트모음": 
        embed = discord.Embed(title="어떤 취향이십니까?",description="망가는 >19manga, 실사물은 >19video 를 사용해주십시오.", color=0x00aaaa)
        await message.channel.send(embed=embed)
    if content == ">19manga": 
        embed = discord.Embed(title="19만화사이트 모음입니다.", color=0xBFE5E8)
        embed.add_field(name="Hitomi", value='https://hitomi.la', inline=False)
        embed.add_field(name="hiyobi", value='https://hiyobi.me', inline=False)
        embed.add_field(name="Hikomi", value='https://hikomi.la', inline=False)
        embed.add_field(name="HentaiHeaven", value='https://hentaihaven.pro/', inline=False)
        embed.add_field(name="hanime.tv", value='https://hanime.tv/', inline=False)
        embed.add_field(name="K258059", value='https://k258059.net/', inline=False)
        embed.add_field(name="Luscious", value='https://luscious.net/', inline=False)
        embed.add_field(name="Nozomi.la", value='https://nozomi.la/', inline=False)
        embed.add_field(name="nhentai", value='https://nhentai.net/', inline=False)
        embed.add_field(name="SM People", value='https://smpeople.net/', inline=False)
        embed.add_field(name="Sankaku Complex", value='https://www.sankakucomplex.com/', inline=False)
        embed.add_field(name="Tsumino", value='https://www.tsumino.com/', inline=False)
        embed.add_field(name="늑대닷컴", value='https://wfwf68.com/', inline=False)
        await message.channel.send(embed=embed)
    if content == ">19video": 
        embed = discord.Embed(title="19성인동영상 사이트 모음입니다.", color=0xBFE5E8)
        embed.add_field(name="Pornhub", value='https://www.pornhub.com/', inline=False)
        embed.add_field(name="Sean Cody **게이 포르노 사이트입니다. 주의하세요.**", value='https://www.seancody.com/', inline=False)
        embed.add_field(name="Thumbzilla", value='https://www.thumbzilla.com/', inline=False)
        embed.add_field(name="Xvideos", value='https://xvideos.com/', inline=False)
        embed.add_field(name="xHamster", value='https://www.xhamster.desi/', inline=False)
        embed.add_field(name="sora.la", value='https://sora1.la/', inline=False)
        await message.channel.send(embed=embed)
    m = message.content
    if m.startswith(">남후"):
        await message.channel.send("https://namu.wiki/w/" + ms[1])
    if m.startswith(">나무위키"):
       await message.channel.send("https://namu.wiki/w/" + ms[1])
    if ms[0] == (">좆무"):
        await message.channel.send("https://namu.wiki/w/" + ms[1])
    if m.startswith(">꺼무위키"):
        await message.channel.send("https://namu.wiki/w/" + ms[1])
    if m.startswith(">namuwiki"):
        await message.channel.send("https://namu.wiki/w/" + ms[1])
    if m.startswith(">youtube"):
        await message.channel.send("https://www.youtube.com/results?search_query=" + ms[1])
    if m.startswith(">유튜브"):
        await message.channel.send("https://www.youtube.com/results?search_query=" + ms[1])
    if m.startswith(">너튜브"):
        await message.channel.send("https://www.youtube.com/results?search_query=" + ms[1])
    if m.startswith(">google"):
        await message.channel.send("https://www.google.co.kr/search?q=" + ms[1])
    if m.startswith(">구글"):
        await message.channel.send("https://www.google.co.kr/search?q=" + ms[1])
    if m.startswith(">twitch"):
        await message.channel.send("https://www.twitch.tv/search?term=" + ms[1])
    if m.startswith(">트위치"):
        await message.channel.send("https://www.twitch.tv/search?term=" + ms[1])
    if(m.startswith('>페북')):
        await message.channel.send("https://www.facebook.com/search/top/?q=" + ms[1])
    if(m.startswith('>페이스북')):
        await message.channel.send("https://www.facebook.com/search/top/?q=" + ms[1])
    if(m.startswith('>얼굴')):
        await message.channel.send("https://www.facebook.com/search/top/?q=" + ms[1])
    if(m.startswith('>facebook')):
        await message.channel.send("https://www.facebook.com/search/top/?q=" + ms[1])
    if(m.startswith('>트위터')):
        await message.channel.send("https://twitter.com/search?q="+ ms[1] +"&src=typed_query")
    if(m.startswith('>틧터')):
        await message.channel.send("https://twitter.com/search?q="+ ms[1] +"&src=typed_query")
    if(m.startswith('>틧허')):
        await message.channel.send("https://twitter.com/search?q="+ ms[1] +"&src=typed_query")
    if(m.startswith('>twitter')):
        await message.channel.send("https://twitter.com/search?q="+ ms[1] +"&src=typed_query")
    if(m.startswith('>Bluebird')):
        await message.channel.send("https://twitter.com/search?q="+ ms[1] +"&src=typed_query")
    if(m.startswith('>페미광장')):
          await message.channel.send("https://twitter.com/search?q=" + ms[1] +"&src=typed_query")
    if(m.startswith('>ㅇㅂ')):
        await message.channel.send("https://www.ilbe.com/search?docType=doc&searchType=title_content&page=1&q=" + ms[1])
        
    if message.content.startswith('>청소'):
        try:
            amount = list_message[1]
        except:
            embed = discord.Embed(title="ERROR..",description="명령어가 잘못되었거나, 권한이 부족합니다.", color=0x00aaaa)
            await message.channel.send(embed=embed)
            return
        try:
            await message.channel.purge(limit = int(amount))
            embed = discord.Embed(title="「당신의 요청은 매우 혁명적인 방법으로 처리되었습니다」",description=str(message.author) + " 님에 의해 메세지 " + amount + '개가 청소되었습니다.', color=0x00aaaa)
            await message.channel.send(embed=embed)
        except:
            embed = discord.Embed(title="ERROR..",description="권한이 부족한 것 같아요. UwU", color=0x00aaaa)
            await message.channel.send(embed=embed)
        return
    if message.content.startswith('>타노슨'):
        try:
            amount = list_message[1]
        except:
            embed = discord.Embed(title="ERROR..",description="명령어가 잘못되었거나, 권한이 부족합니다.", color=0x00aaaa)
            await message.channel.send(embed=embed)
            return
        try:
            await message.channel.purge(limit = int(amount))
            embed = discord.Embed(title="「채팅방이 북! 딱!」",description=str(message.author) + " 이라는 빌런에 의해 메세지 " + amount + '개가 타노슨되었다.', color=0x00aaaa)
            await message.channel.send(embed=embed)
        except:
            embed = discord.Embed(title="ERROR..",description="권한이 부족한 것 같아요. UwU", color=0x00aaaa)
            await message.channel.send(embed=embed)
        return

    if message.content.startswith('>clear'):
        try:
            amount = list_message[1]
        except:
            embed = discord.Embed(title="ERROR..",description=">clear[消すことがメッセージ数]ロマンの使用が可能です。", color=0xf9a0f8)
            await message.channel.send(embed=embed)
            return
        try:
            await message.channel.purge(limit = int(amount))
            embed = discord.Embed(title="「あなたの要請は非常に革命的な方法で処理されました。」",description=str(message.author) + " あなたによりメッセージ " + amount + '個が整理されました。', color=0xf9a0f8)
            await message.channel.send(embed=embed)
        except:
            embed = discord.Embed(title="ERROR..",description="正しいメッセージの値を入力してください。", color=0xf9a0f8)
            await message.channel.send(embed=embed)
        return
    if(ms[0] == ">날씨"):
            mes = await message.channel.send('허본좌를 불러봐 너의 얼굴에 웃음꽃이 피게 될 것이야')
            a = m[4:]
            #print(a)
            
            b = a.replace(" ", "+")
            html = requests.get('https://search.naver.com/search.naver?query='+ b +'날씨')
            # pprint(html.text)
            
            soup = BeautifulSoup(html.text,'html.parser')
            
            data1 = soup.find('div',{'class':'detail_box'})
            #pprint(data1)
            
            data2 = data1.findAll('dd')
            # pprint(data2)
            
            fine_dust = data2[0].text
            #print(fine_dust)
            find_dust_asdf = data2[0].text
            #print(find_dust_asdf)
            #await message.channel.send(str(fine_dust))
            
            ultra_fine_dust = data2[1].text
            #print(ultra_fine_dust)
            #await message.channel.send(str(ultra_fine_dust))
            
            ohjon = data2[2].text
            #print(ohjon)
            
            chegam = soup.find('span',{'class':'sensible'}).text
            #print(chegam)
            
            jawisun = soup.find('span',{'class':'indicator'}).text
            #print(jawisun)
            
            data3 = soup.find('div', {'class' : 'main_info'})
            data4 = data3.findAll('span')
            C = data4[1].text
            #await message.channel.send(str(C))  
            
            data5 = soup.find('span', {'class' : 'btn_select'})
            data6 = data5.findAll('em')[0].text
            #await message.channel.send(data6)
            embed = discord.Embed(title = data6 + " 의 날씨 정보일껍니다 (네 그렇다네요)", color = 0x00ff00)
            embed.add_field(name = "기온", value = str(C) + "˚C")
            embed.add_field(name = "미세먼지", value = str(fine_dust))
            embed.add_field(name = "초미세먼지", value = str(ultra_fine_dust))
            embed.add_field(name = "오존지수", value = str(ohjon))
            embed.add_field(name = "자외선지수", value = str(jawisun))
            embed.add_field(name = "체감온도", value = str(chegam[4:]) + 'C')
            await mes.delete()
            await message.channel.send(embed=embed)
            return

client.run('NzExNTMyODc4ODgxODgyMTMz.XsSDeQ.fA2b4jZ2yzSfzLzn86ock70ubPk')

print()

