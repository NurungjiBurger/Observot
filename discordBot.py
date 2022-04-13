from os import system
from ssl import Options
from typing_extensions import Self
import discord
import time
import threading
from discord_slash import SlashCommand, SlashContext
from dataclasses import dataclass
from discord.ext import commands
from to import Token

intents = discord.Intents.all()
client = discord.Client()

bot_activity = discord.Game(name="감시")
bot = commands.Bot(command_prefix='/', intents=intents)

slash = SlashCommand(bot, sync_commands=True)
guild_id = [961443814101360661]

# 명단 구조체
@dataclass
class informaiton():
    caught = list()


# 명단 리스트
members = list()
membersInformation = list()

# 봇 활성화
@bot.event
async def on_ready():
    print('로그인중입니다. ')
    print(f"봇={bot.user.name}로 연결중")
    print('연결이 완료되었습니다.')

    await bot.change_presence(status=discord.Status.online, activity=bot_activity)    

# 봇 활동중 멤버의 변화 체크
@bot.event
async def on_member_update(before, after):
    channel = bot.get_channel(961443814101360664)
    catch = str()
    # 비활동 -> 게임중
    if (len(before.activities) > len(after.activities)):
        cnt = 0
        for cnt in range (len(members)):
            if (members[cnt].name == before.name) :
                await channel.send("{} 님이 {} 활동을 해제했습니다.".format(members[cnt].name, before.activities[0].name))
    else :
        # 게임중 -> 비활동
        if (len(before.activities) < len(after.activities)) :
            cnt = 0
            for cnt in range (len(members)):
                if (members[cnt].name == before.name) :
                    await channel.send("{} 님이 {} 활동을 시작했습니다.".format(members[cnt].name, after.activities[0].name))
                    membersInformation[cnt].caught.append("{} 님이 {} 활동을 시작했습니다.".format(members[cnt].name, after.activities[0].name))
        # 게임중 -> 게임중        
        else :
            if (len(before.activities) > 0 & len(after.activities) > 0 ) :
                if (before.activities[0].name != after.activities[0].name) :
                    cnt = 0
                    for cnt in range (len(members)):
                        if (members[cnt].name == before.name) :
                            await channel.send("{} 님이 {} 활동을 해제하고 {} 활동을 시작했습니다.".format(members[cnt].name, before.activities[0].name, after.activities[0].name))
                            membersInformation[cnt].caught.append("{} 님이 {} 활동을 해제하고 {} 활동을 시작했습니다.".format(members[cnt].name, before.activities[0].name, after.activities[0].name))

# 적발 횟수 출력
@slash.slash(name="CaughtCnt", description="적발횟수를 출력합니다.", guild_ids = guild_id)
async def CaughtCnt(ctx):

    cnt = 0
    for cnt in range (len(members)) :
        # 적발횟수를 묻는 대상이 감시 대상이라면
        if (ctx.author.name == members[cnt].name) :
            await ctx.send("{}님은 {}회 적발 되셨습니다.".format(ctx.author.name, len(membersInformation[cnt].caught)))
    
    # 감시 대상이 아닌경우
    if (cnt == len(members)):
        await ctx.send("{}님은 감시대상이 아닙니다. 감시 대상으로 등록해주세요.".format(ctx.author.name))

# 적발 로그 출력
@slash.slash(name="CaughtLog", description="적발로그를 출력합니다.", guild_ids = guild_id)
async def CaughtLog(ctx):

    cnt = 0
    for cnt in range (len(members)) :
        # 적발로그를 묻는 대상이 감시 대상이라면
        if (ctx.author.name == members[cnt].name):
            log = ''
            lognum = 0
            for lognum in range (len(membersInformation[cnt].caught)):
                log += "{}. {}\n".format(lognum+1, membersInformation[cnt].caught[lognum])

            await ctx.send(log)
    
    # 감시 대상이 아닌경우
    if (cnt == len(members)) :
        await ctx.send("{}님은 감시대상이 아닙니다. 감시 대상으로 등록해주세요.".format(ctx.author.name))

# 적발 로그 지우기
@slash.slash(name="RemoveCaught", description="적발로그를 삭제합니다.", guild_ids = guild_id)
async def RemoveCaught(ctx, membername, lognum):

    if (ctx.author.name == "화릿불"):
        cnt = 0
        for cnt in range (len(members)) :
            # 적발로그를 지우려는 대상이 감시 대상이라면
            if (membername == members[cnt].name):
                del(membersInformation[cnt].caught[int(lognum)-1])
                await ctx.send("{}님의 {}번째 적발은 철회되었습니다.".format(membername, lognum))
    
        # 감시 대상이 아닌경우
        if (cnt == len(members)) :
            await ctx.send("{}님은 감시대상이 아닙니다.".format(membername))
    else :
        await ctx.send("{}님 적발철회 권한이 없습니다. 방장에게 문의하세요.".format(ctx.author.name))

# 감시 등록
@slash.slash(name="Enroll", description="감시대상에 등록합니다.", guild_ids = guild_id)
async def Enroll(ctx):

    # 해당 감시를 요청한 멤버를 감시 명단에 투입    
    cnt = 0
    for cnt in range (len(members)) :
        # 이미 감시 대상인 경우 추가하지 않음
        if (ctx.author.name == members[cnt].name) :
            await ctx.send('{}님은 이미 감시중입니다.'.format(ctx.author.name))

    # cnt 가 members의 길이와 같으면 끝까지 탐색해서 해당인원이 없는것이므로 추가
    if (cnt == len(members)) :
        #await ctx.send ('{}님 감시를 시작합니다.'.format(ctx.author.name))
        await ctx.channel.send ('{}님 감시를 시작합니다.'.format(ctx.author.name))

        members.append(ctx.author)
        member = informaiton()
        membersInformation.append(member)

# 사용자 출력
@slash.slash(name="User", description="감시중인 사용자를 보여줍니다.", guild_ids = guild_id)
async def User(ctx):

    # 현재 감시중인 사용자 출력
    cnt = 0
    membersName = ''
    for cnt in range (len(members)):
        if (cnt != 0) : membersName += ', '
        membersName += members[cnt].name

    if (len(members) > 0) :
        await ctx.send('현재 감시중인 인원수는 {} 명이고 인원은 {} 입니다.'.format(len(members), membersName))    
    else :
        await ctx.send('현재 감시중인 인원은 없습니다.')

# 감시 해제
@slash.slash(name="Clear", description="감시대상에서 해제합니다.", guild_ids = guild_id)
async def Clear(ctx):

    cnt = 0
    # 리스트에 사람이 있을 경우
    if (len(members) > 0) : 
        for cnt in range (len(members)) :
            if (ctx.author.name == members[cnt].name): 
                # 해당 감시 해제를 요청한 멤버를 감시 명단에서 제외
                del(members[cnt])
                del(membersInformation[cnt])
                await ctx.send ('{}님 감시를 해제합니다.'.format(ctx.author.name))
                break
            else :        
                if (cnt == len(members)) :
                    await ctx.send ('{}님은 이미 감시대상이 아닙니다.'.format(ctx.author.name))
    else :
        await ctx.send ('현재 감시중인 대상이 없습니다.')


# 봇 실행
bot.run(Token)