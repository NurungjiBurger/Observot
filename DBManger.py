import os
import discord
import pymysql

from discord_slash import SlashCommand
from discord.ext import commands
from dotenv import load_dotenv
from datetime import datetime, timezone, timedelta

load_dotenv()
HOST = os.getenv('HOST')
USER = os.getenv('USER')
PASSWORD = os.getenv('PASSWORD')
DB = os.getenv('DB')

con = pymysql.connect(host=HOST, user=USER, password=PASSWORD, db=DB, charset='utf8')

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
COUNT = "count"

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
    elif type == COUNT:
        sql = "SELECT COUNT(*) FROM (SELECT * FROM log where user_id = %s) log"
        cur.execute(sql, user_id)
        result = cur.fetchall()
        con.commit()
        return result
