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
CHEIFS = os.getenv('CHEIFS')

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

LOG = "log"
EXCEPTION = "exception"

intents = discord.Intents.all()
client = discord.Client()

bot_activity = discord.Game(name="감시")
bot = commands.Bot(command_prefix='/', intents=intents)

slash = SlashCommand(bot, sync_commands=True)
guild_id = [961443814101360661]

# 테이블이 있는지 체크하고 없다면 생성
def table_check():
    
    sql = "SHOW TABLES like 'user'"
    cur.execute(sql)
    result = cur.fetchall()

    if result:
        True
    else:
        sql = "CREATE TABLE user ( user_id bigint NOT NULL PRIMARY KEY, cnt int(10) )"
        cur.execute(sql)
        con.commit()

    sql = "SHOW TABLES like 'exception'"
    cur.execute(sql)
    result = cur.fetchall()

    if result:
        True
    else:
        sql = "CREATE TABLE exception (  user_id bigint NOT NULL, activity varchar(255) )"
        cur.execute(sql)
        con.commit()

    sql = "SHOW TABLES like 'log'"
    cur.execute(sql)
    result = cur.fetchall()

    if result:
        True
    else:
        sql = "CREATE TABLE log (  id int NOT NULL AUTO_INCREMENT PRIMARY KEY, user_id bigint NOT NULL, time varchar(255), activity varchar(255), FOREIGN KEY (user_id) REFERENCES user (user_id) )"
        cur.execute(sql)
        con.commit()

# 유저 DB 관리
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

# 예외 DB 관리
def exception_data(type, user_id, activity):

    if type == INSERT:
        sql = "INSERT INTO exception (user_id, activity) VALUES (%s, %s)"
        cur.execute(sql, (user_id, activity))
        con.commit()
        return None
    elif type == UPDATE:
        return None
    elif type == DELETE:
        if activity == '':
            sql = "DELETE FROM exception where user_id = %s"
            cur.execute(sql, user_id)
        else:
            sql = "DELETE FROM exception WHERE user_id = %s and activity = %s"
            cur.execute(sql, (user_id, activity))
        con.commit()
        return None
    elif type == SELECT:
        if activity == '':
            sql = "SELECT * FROM exception where user_id = %s"
            cur.execute(sql, user_id)
        else:
            sql = "SELECT * FROM exception where user_id = %s and activity = %s"
            cur.execute(sql, (user_id, activity))
        result = cur.fetchall()
        con.commit()
        return result

# 로그 DB 관리
def log_data(type, user_id, time, activity, id):

    if type == INSERT:
        sql = "INSERT INTO log (user_id, time, activity) VALUES (%s, %s, %s)"
        cur.execute(sql, (user_id, time, activity))
        con.commit()
        return None
    elif type == UPDATE:
        return None
    elif type == DELETE:
        if id == -1:
            sql = "DELETE FROM log where user_id = %s"
            cur.execute(sql, user_id)
        else :
            sql = "DELETE FROM log WHERE user_id = %s and id = %s"
            cur.execute(sql, (user_id, id))
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
    
    # 구글 캘린더 // 휴일 이거나 금, 토, 일 이라면 제외
    

    # 금요일 토요일 일요일 제외
    tms = datetime.now(timezone(timedelta(hours=9)))
    if tms.weekday() >= 4:
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
                edata = exception_data(SELECT, after.id, after.activities[0].name)
                if edata:
                    return
                else:
                    tms = datetime.now(timezone(timedelta(hours=9)))
                    tm = str(tms)[:10] + " " + str(tms.time())[:8]
                    user_data(UPDATE, before.id, data[0][1]+1)
                    log_data(INSERT, before.id, tm, after.activities[0].name, 0)

# 적발 예외 등록
@slash.slash(name="EnrollExceptionActivity", description="적발 예외 활동을 등록합니다.", guild_ids=guild_id)
async def enroll_except(ctx, activity: str):

    udata = user_data(SELECT, ctx.author.id, 0)
    if udata:
        edata = exception_data(SELECT, ctx.author.id, activity)
        if edata:
            await ctx.send("{}님의 {}활동은 이미 예외로 등록되어있습니다.".format(ctx.author.name, activity))
        else:
            exception_data(INSERT, ctx.author.id, activity)
            await ctx.send("{}님의 {}활동은 예외로 등록되었습니다.".format(ctx.author.name, activity))
    else:
        await ctx.send("{}님은 감시대상이 아닙니다.".format(ctx.author.name))

# 적발 예외 목록
@slash.slash(name="ExceptionActivity", description="적발 예외 활동을 보여줍니다.", guild_ids=guild_id)
async def exception(ctx):

    udata = user_data(SELECT, ctx.author.id, 0)
    if udata:
        edata = exception_data(SELECT, ctx.author.id, '')
        catalog = create_msg(ctx.author.name, edata, EXCEPTION)

        if catalog == '':
            await ctx.send("{}님 예외 활동을 등록해주세요.".format(ctx.author.name))
        else:
            await ctx.send(catalog)
    else:
        await ctx.send("{}님은 감시대상이 아닙니다.".format(ctx.author.name))


# 적발 예외 삭제
@slash.slash(name="DeleteExceptionActivity", description="적발 예외 활동을 삭제합니다.", guild_ids=guild_id)
async def delete_except(ctx, activity: str):

    udata = user_data(SELECT, ctx.author.id, 0)
    if udata:
        edata = exception_data(SELECT, ctx.author.id, activity)
        if edata:
            exception_data(DELETE, ctx.author.id, activity)
            await ctx.send("{}님의 {}활동은 예외에서 삭제되었습니다.".format(ctx.author.name, activity))
        else:
            await ctx.send("{}님의 {}활동은 예외로 등록되어있지 않습니다.".format(ctx.author.name, activity))
    else:
        await ctx.send("{}님은 감시대상이 아닙니다.".format(ctx.author.name))
  
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

def create_msg(name, data, type):
    if type == LOG:
        return "\n".join([f"{idx + 1}. {log[2]} {name}님이 {log[3]} 활동을 시작했습니다." for idx, log in enumerate(data)])
    elif type == EXCEPTION:
        return "\n".join([f"예외활동 {idx + 1}. {log[1]}" for idx, log in enumerate(data)])

# 적발 로그 출력
@slash.slash(name="Log", description="적발 로그를 출력 합니다.", guild_ids=guild_id)
async def my_log(ctx):

    # 적발로그를 묻는 대상이 감시 대상이라면
    udata = user_data(SELECT, ctx.author.id, 0)
    if udata:
        ldata = log_data(SELECT, ctx.author.id, 0, 0, 0)
        log = create_msg(ctx.author.name, ldata, LOG)

        if log == '':
            await ctx.send("적발된 내용이 없습니다.")
        else:
            await ctx.send(log)

    # 감시 대상이 아닌경우
    else:
        await ctx.send("{}님은 감시대상이 아닙니다. 감시 대상으로 등록해주세요.".format(ctx.author.name))

# 적발 로그 지우기
@slash.slash(name="RemoveLog", description="적발로그를 삭제합니다.", guild_ids=guild_id)
async def remove_log(ctx, name: discord.Member, num):

    # 방장만 로그 삭제 가능
    if any('방장' == role.name for idx, role in enumerate(ctx.author.roles)):
        # 감시 대상 O
        udata = user_data(SELECT, name.id, 0)
        if udata:
            ldata = log_data(SELECT, name.id, 0, 0, 0)
            if ldata:
                if int(num) > 0 and int(num) <= len(ldata):
                    log_data(DELETE, name.id, 0, 0, ldata[int(num)-1][0])
                    user_data(UPDATE, name.id, udata[0][1]-1)
                    await ctx.send("{}님의 {}번째 적발은 철회 되었습니다.".format(name.name, num))
                    log = create_msg(name.name, log_data(SELECT, name.id, 0, 0, 0), LOG)
                    if log == '':
                        await ctx.send("적발된 내용이 없습니다.")
                    else:
                        await ctx.send(log)
                elif int(num) == -1:
                    for cnt in range(len(ldata)):
                        log_data(DELETE, name.id, 0, 0, ldata[cnt][0])
                        user_data(UPDATE, name.id, udata[0][1]-1)
                    await ctx.send("{}님의 모든 적발이 철회 되었습니다.".format(name.name))
                    log = create_msg(name.name, log_data(SELECT, name.id, 0, 0, 0), LOG)
                    if log == '':
                        await ctx.send("적발된 내용이 없습니다.")
                    else:
                        await ctx.send(log)
                else:
                    await ctx.send("{}님의 {}번째 적발은 존재하지 않습니다.".format(name.name, num))
        # 감시 대상 X
        else:
            await ctx.send("{}님은 감시 대상이 아닙니다.".format(ctx.author.name))
    # 방장이 아님
    else:
        await ctx.send("{}님은 적발철회 권한이 없습니다. 방장에게 문의해주세요.".format(ctx.author.name))

# 방장 전용 적발 로그 출력
@slash.slash(name="Member_Log", description="멤버의 적발 로그를 출력 합니다.", guild_ids=guild_id)
async def member_log(ctx, name: discord.Member):

    if any('방장' == role.name for idx, role in enumerate(ctx.author.roles)):
        # 적발로그를 묻는 대상이 감시 대상이라면
        udata = user_data(SELECT, name.id, 0)
        if udata:
            ldata = log_data(SELECT, name.id, 0, 0, 0)
            log = create_msg(name.name, ldata, LOG)

            if log == '':
                await ctx.send("적발된 내용이 없습니다.")
            else:
                await ctx.send(log)
        # 감시 대상이 아닌경우
        else:
            await ctx.send("{}님은 감시대상이 아닙니다. 감시 대상으로 등록해주세요.".format(ctx.author.name))
    else:
        await ctx.send("방장만 사용할수있는 기능입니다.")

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
            if cnt >= 1:
                membersName += ', '
            membersName += bot.get_user(data[cnt][0]).name
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

        ldata = log_data(SELECT, ctx.author.id, 0, 0, 0)
        if ldata:
            log_data(DELETE, ctx.author.id, 0, 0, -1)
        """
        length = len(ldata)
        for num in length:
            log_data(DELETE, ctx.author.id, 0, 0, ldata[num][0])
            """
        user_data(DELETE, ctx.author.id, 0)
        edata = exception_data(SELECT, ctx.author.id, '')
        if edata:
            exception_data(DELETE, ctx.author.id, '')
        await ctx.send('{}님 감시를 해제합니다.'.format(ctx.author.name))
    else :
        await ctx.send('{}님은 이미 감시대상이 아닙니다.'.format(ctx.author.name))


# 봇 실행
bot.run(TOKEN)

con.close()