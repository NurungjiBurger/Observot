import os

import discord
import pymysql

from discord_slash import SlashCommand
from discord.ext import commands
from dotenv import load_dotenv
from datetime import datetime, timezone, timedelta

load_dotenv()
TOKEN = os.getenv('TOKEN')
HOST = os.getenv('HOST')
USER = os.getenv('USER')
PASSWORD = os.getenv('PASSWORD')
DB = os.getenv('DB')

con = pymysql.connect(host=HOST, user=USER, password=PASSWORD, db=DB, charset='utf8')
#con = pymysql.connect(host='127.0.0.1', user='root', password='6195', db='test', charset='utf8')

cur = con.cursor()

"""
res = cur.fetchall()

for data in res:
    print(data)
"""

INSERT = "insert"
UPDATE = "update"
DELETE = "delete"
SELECT = "select"

intents = discord.Intents.all()
client = discord.Client()

bot_activity = discord.Game(name="감시")
bot = commands.Bot(command_prefix='/', intents=intents)

slash = SlashCommand(bot, sync_commands=True)
guild_id = [961443814101360661]

def table_check():

    sql = """SHOW TABLES"""
    cur.execute(sql)
    result = cur.fetchall()

    if result:
        return True
    else:
        sql = '''CREATE TABLE user ( user_id bigint NOT NULL PRIMARY KEY, cnt int(10) )'''
        cur.execute(sql)
        con.commit()
        sql = """CREATE TABLE log (  id int NOT NULL AUTO_INCREMENT PRIMARY KEY, user_id bigint NOT NULL, time varchar(255), activity varchar(255), FOREIGN KEY (user_id) REFERENCES user (user_id) )"""
        cur.execute(sql)
        con.commit()


def user_data(type, user_id, cnt):

    if type == INSERT:
        sql = """INSERT INTO user (user_id, cnt) VALUES (%s, %s)"""
        cur.execute(sql, (user_id, cnt))
        con.commit()
        return None
    elif type == UPDATE:
        sql = "UPDATE user SET cnt = %s WHERE user_id = %s"
        cur.execute(sql, (cnt, user_id))
        con.commit()
        return None
    elif type == DELETE:
        sql = "DELETE FROM user WHERE user_id = %s"
        cur.execute(sql, user_id)
        con.commit()
        return None
    elif type == SELECT:
        if user_id == 0:
            sql = "SELECT * FROM user"
            cur.execute(sql)
        else:
            sql = "SELECT * FROM user where user_id = %s"
            cur.execute(sql, user_id)
        result = cur.fetchall()
        con.commit()
        return result


def log_data(type, user_id, time, activity, id):

    if type == INSERT:
        sql = "INSERT INTO log (user_id, time, activity) VALUES (%s, %s, %s)"
        cur.execute(sql, (user_id, time, activity))
        con.commit()
        return None
    elif type == UPDATE:
        return None
    elif type == DELETE:
        sql = "DELETE FROM log WHERE id = %s"
        cur.execute(sql, id)
        con.commit()
        return None
    elif type == SELECT:
        sql = "SELECT * FROM log where user_id = %s"
        cur.execute(sql, user_id)
        result = cur.fetchall()
        con.commit()
        return result


# 봇 활성화
@bot.event
async def on_ready():
    print('로그인중입니다. ')
    print(f"봇={bot.user.name}로 연결중")
    print('연결이 완료되었습니다.')

    table_check()

    await bot.change_presence(status=discord.Status.online, activity=bot_activity)    

# 봇 활동중 멤버의 변화 체크
@bot.event
async def on_member_update(before, after):


    # 토요일 일요일 제외
    tms = datetime.now(timezone(timedelta(hours=9)))
    if tms.weekday() >= 5:
        await bot.change_presence(status=discord.Status.online, activity=discord.Game("다같이 게임"))
        return
    else:
        await bot.change_presence(status=discord.Status.online, activity=bot_activity)

    channel = bot.get_channel(961443814101360664)

    # 대상 아님
    data = user_data(SELECT, before.id, 0)
    if data:
        # 게임중 -> 비활동
        if len(before.activities) > len(after.activities):
            await channel.send("{}님이 {} 활동을 해제했습니다.".format(before.name, before.activities[0].name))
        # 비활동 -> 게임중
        else:
            if len(before.activities) < len(after.activities):
                msg = "{}님이 {} 활동을 시작했습니다.".format(before.name, after.activities[0].name)
                await channel.send(msg)
                tms = datetime.now(timezone(timedelta(hours=9)))
                tm = str(tms)[:10] + " " + str(tms.time())[:8]
                user_data(UPDATE, before.id, data[0][1]+1)
                log_data(INSERT, before.id, tm, after.activities[0].name, 0)

  
# 적발 횟수 출력
@slash.slash(name="Count", description="적발 횟수를 출력 합니다.", guild_ids=guild_id)
async def my_cnt(ctx):

    # 적발횟수를 묻는 대상이 감시 대상이라면
    data = user_data(SELECT, ctx.author.id, 0)
    if data:
        await ctx.send("{}님은 {}회 적발 되셨습니다.".format(ctx.author.name, data[0][1]))
    # 감시 대상이 아닌경우
    else:
        await ctx.send("{}님은 감시대상이 아닙니다. 감시 대상으로 등록해주세요.".format(ctx.author.name))

# 적발 로그 출력
@slash.slash(name="Log", description="적발 로그를 출력 합니다.", guild_ids=guild_id)
async def my_log(ctx):

    # 적발로그를 묻는 대상이 감시 대상이라면
    udata = user_data(SELECT, ctx.author.id, 0)
    if udata:
        ldata = log_data(SELECT, ctx.author.id, 0, 0, 0)
        log = ''
        for num in range(len(ldata)):
            log += "{}. {}\n".format(num + 1, ldata[num][2] + " " + ctx.author.name + "님이 " + ldata[num][3] + " 활동을 시작했습니다.")

        if log == '':
            await ctx.send("적발된 적이 없습니다.")
        else:
            await ctx.send(log)

    # 감시 대상이 아닌경우
    else:
        await ctx.send("{}님은 감시대상이 아닙니다. 감시 대상으로 등록해주세요.".format(ctx.author.name))    

# 적발 로그 지우기
@slash.slash(name="RemoveLog", description="적발로그를 삭제합니다.", guild_ids=guild_id)
async def remove_log(ctx, num):

    # 적발로그를 지우려는 대상이 감시 대상이라면
    data = log_data(SELECT, ctx.author.id, 0, 0, 0)
    if data:
        log_data(DELETE, ctx.author.id, 0, 0, num)
        await ctx.send("{}님의 {}번째 적발은 철회 되었습니다.".format(ctx.author.name, num))
    # 감시 대상이 아닌 경우
    else:
        await ctx.send("{}님은 감시 대상이 아닙니다.".format(ctx.author.name))

# 방장만 로그 삭제 할 수 있게 업데이트 ㄱ
    """
    if ctx.author.id == 271493892224843777:
        data = log_data(SELECT, member.id, 0, 0, 0)
        if data:
            print("삭제하겠습니다")
            #log_data(DELETE, name.id, 0, 0, num)
            await ctx.send("{}님의 {}번째 적발은 철회 되었습니다.".format(member.name, num))
        # 감시 대상이 아닌 경우
        else:
            await ctx.send("{}님은 감시 대상이 아닙니다.".format(member.name))
    else:
        await ctx.send("{}님 적발철회 권한이 없습니다. 방장에게 문의하세요.".format(ctx.author.name))
    """

# 감시 등록
@slash.slash(name="Enroll", description="감시대상에 등록합니다.", guild_ids=guild_id)
async def enroll(ctx):

    # 해당 감시를 요청한 멤버를 감시 명단에 투입
    data = user_data(SELECT, ctx.author.id, 0)
    if data:
        await ctx.send('{}님은 이미 감시중입니다.'.format(ctx.author.name))
    else:
        user_data(INSERT, ctx.author.id, 0)
        await ctx.send('{}님 감시를 시작합니다.'.format(ctx.author.name))


# 사용자 출력
@slash.slash(name="User", description="감시중인 사용자를 보여줍니다.", guild_ids=guild_id)
async def user(ctx):

    data = user_data(SELECT, 0, 0)
    if data:
        membersName = ''
        for cnt in range(len(data)):
            membersName += bot.get_user(data[cnt][0]).name
            if cnt >= 1:
                membersName += ', '
        await ctx.send('현재 감시중인 인원수는 {} 명이고 인원은 {} 입니다.'.format(cnt+1, membersName))
    else:
        await ctx.send('현재 감시중인 인원은 없습니다.')

# 감시 해제
@slash.slash(name="Clear", description="감시대상에서 해제합니다.", guild_ids=guild_id)
async def clear(ctx):

    # 리스트에 사람이 있을 경우
    data = user_data(SELECT, ctx.author.id, 0)
    if data:
        # 해당 감시 해제를 요청한 멤버를 감시 명단에서 제외
        for num in range(data[0][1]):
            log_data(DELETE, ctx.author.id, 0, 0, num+1)
        user_data(DELETE, ctx.author.id, 0)
        await ctx.send('{}님 감시를 해제합니다.'.format(ctx.author.name))
    else :
        await ctx.send('{}님은 이미 감시대상이 아닙니다.'.format(ctx.author.name))


# 봇 실행
bot.run(TOKEN)

con.close()