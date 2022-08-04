from datetime import date
from threading import Thread
import threading
import time
import schedule
from time import sleep
import telebot
import Constants as keys
import psycopg2
import os
import urllib.parse as urlparse

url = urlparse.urlparse(os.environ['DATABASE_URL'])
dbname = url.path[1:]
user = url.username
password = url.password
host = url.hostname
port = url.port

bot = telebot.TeleBot(token=keys.API_KEY)

# conn = psycopg2.connect(
#     dbname="d4dek650nulj0j",
#     user="omehwxpztoyhcb",
#     password="f2630cbdf7bc87daa8cf13ec7d3f81baeadde14438d03a8f01e5c6b01b22ca60",
#     host="ec2-34-235-31-124.compute-1.amazonaws.com",
#     port="5432"
# )
conn = psycopg2.connect(
    dbname=dbname,
    user=user,
    password=password,
    host=host,
    port=port
)
c = conn.cursor()

def test_job():
    flag = False
    print("Hello")
    bot.send_message(691448132, "Hi")
    c.execute("SELECT DISTINCT username FROM budget where update_monthly = %s", (flag,))
    user_list = c.fetchall()

    for row in user_list:
        user = row[0]
        spend = 0
        c.execute("UPDATE budget SET spend = %s WHERE username = %s", (spend, user))
        bot.send_message(user, "Alamak Monday blues again... I make it less blue by resetting your budget ba.")
        conn.commit()
        c.execute("rollback")
        conn.close


if __name__ == '__main__':
    schedule.every().thursday.at("00:34").do(test_job)

    while True:
        schedule.run_pending()
        sleep(1)

