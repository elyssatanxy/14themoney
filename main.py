import decimal
from math import remainder
import sched
from threading import Thread
from time import sleep
import telebot
import Constants as keys
import psycopg2
import os
import urllib.parse as urlparse
from datetime import date
import schedule
from apscheduler.schedulers.blocking import BlockingScheduler

url = urlparse.urlparse(os.environ['DATABASE_URL'])
dbname = url.path[1:]
user = url.username
password = url.password
host = url.hostname
port = url.port

sched = BlockingScheduler()

bot = telebot.TeleBot(token=keys.API_KEY)
conn = psycopg2.connect(
    dbname=dbname,
    user=user,
    password=password,
    host=host,
    port=port
)
c = conn.cursor()


@bot.message_handler(commands=['start'])
def welcome_message(message):
    bot.send_message(message.chat.id, "Eh hello! Welcome to 14themoney!")
    bot.send_message(message.chat.id, "First time here ah? Come, I teach you how use.\n/add to add a new budget... any number also can\n/spend to track when you spend, but don't anyhow spam this one! later your money gone\n/view can view your spending - hopefully got no negatives ah\n/delete help you remove category... spend less save more\n/settings allow you switch between weekly and monthly tracking... very useful de!\n/reset to manually reset your budget ba\n/help if you need help lor, buey paiseh de")


@bot.message_handler(commands=['help'])
def help_message(message):
    bot.send_message(message.chat.id, "No need so shy... Everybody needs help one.")
    bot.send_message(message.chat.id, "Come I tell you again:\n/add to add a new budget... any number also can\n/spend to track when you spend, but don't anyhow spam this one! later your money gone\n/view to view your spending - hopefully got no negatives ah\n/delete help you remove category... spend less save more\n/settings allow you switch between weekly and monthly tracking... very useful de!\n/reset to manually reset your budget ba")
    bot.send_message(message.chat.id, "Still need help ah? Okay lor bopes... go find @elyssatanxy help you ba.")


@bot.message_handler(commands=['settings'])
def settings(message):
    bot.send_message(message.chat.id, "Okay come, how you want to set budget?")
    msg = bot.send_message(message.chat.id, "Send me 'W' for weekly and 'M' for monthly... Thank you ah.")
    bot.register_next_step_handler(msg, process_settings)


def process_settings(message):
    username = message.from_user.id
    username = str(username)
    msg = message.text.upper()
    if msg in "W":
        c.execute("UPDATE budget SET update_monthly = False WHERE username = %s", (username,))
        bot.reply_to(message, "Swee! I help you change to weekly tracking liao.")
    elif msg in "M":
        c.execute("UPDATE budget SET update_monthly = True WHERE username = %s", (username,))
        bot.reply_to(message, "Solid ah, I change to monthly tracking for you le.")
    else:
        bot.reply_to(message, "Dont play play leh, I give you 2 options only...")


@bot.message_handler(commands=['view'])
def view(message):
    bot.send_message(message.chat.id, "Wah moment of truth...")

    username = message.from_user.id
    username = str(username)

    c.execute("SELECT * FROM budget WHERE username = %s", (username,))
    user_budgets = c.fetchall()
    all = ""
    list = 1
    negativeflag = False

    for row in user_budgets:
        remainder = row[2] - row[3]
        all += f"{list}. Left ${remainder} for {row[1]}\n"
        list += 1
        if row[2] < 0:
            negativeflag = True

    conn.commit()
    c.execute("rollback")
    conn.close
    bot.send_message(message.chat.id, all)

    if negativeflag:
        bot.send_message(message.chat.id, "Aiya you overspend liao. Stop it ah!")
    else:
        bot.send_message(message.chat.id, "Wah still within budget leh! Good job ah.")


@bot.message_handler(commands=['add'])
def add(message):
    msg = bot.send_message(message.chat.id,
                           text="Okay come, enter your budgets liddat:\ncategory1-budget1\ncategory2-budget2\n<b>(e.g. Food-200)</b>",
                           parse_mode='HTML')
    bot.register_next_step_handler(msg, process_budget)


def process_budget(message):
    username = message.from_user.id
    username = str(username)
    msg = message.text
    multilinecheck = msg.split("\n")

    for line in multilinecheck:
        try:
            separated = line.split("-")
            global category
            category = separated[0]
            global budget
            budget = float(separated[1])
            spend = 0
            update_monthly = True

            c.execute("INSERT INTO budget (category_name, budget, spend, username, update_monthly) VALUES (%s, %s, %s, %s, %s);", (category, budget, spend, username, update_monthly))
            bot.reply_to(message, f"Okay liao, added ${budget:.2f} for {category}! Don't overspend hor.")

            if budget > 500:
                bot.reply_to(message, "Eh... can spend so much meh? Got give money to your parents anot?")

            conn.commit()
            c.execute("rollback")
            conn.close
        except ValueError:
            bot.reply_to(message, "Eh this one not a number leh... Don't anyhow!")
            c.execute("rollback")
        except psycopg2.IntegrityError:
            msg = bot.reply_to(message,
                           f"Alamak... You already set a budget for {category} leh... You want update budget instead anot?\nType 'Y' for yas or 'N' for naur")
            c.execute("rollback")
            bot.register_next_step_handler(msg, update_budget)
        except IndexError:
            msg = bot.reply_to(message, "Huh? Wo bu ming bai... Try again please...")
            c.execute("rollback")
            bot.register_next_step_handler(msg, process_budget)


def update_budget(message):
    msg = message.text.upper()
    if msg in "Y":
        username = message.from_user.id
        username = str(username)

        c.execute("UPDATE budget SET budget = %s WHERE category_name = %s AND username = %s;", (budget, category, username))
        bot.reply_to(message, f"Okay liao, I updated budget for {category} to ${budget} already!")

        conn.commit()
        c.execute("rollback")
        conn.close
    elif msg in "N":
        bot.reply_to(message, "Can, I don't change anything lor.")
    else:
        bot.reply_to(message, "Don't test my patience hor, only got 2 choices...")


@bot.message_handler(commands=['spend'])
def spend(message):
    msg = bot.send_message(message.chat.id, "Aiyo spend money again... Sigh... How much now? Tell me like this ah:\ncategory1-amount")
    bot.register_next_step_handler(msg, process_spending)


def process_spending(message):
    username = message.from_user.id
    username = str(username)
    msg = message.text

    try:
        separated = msg.split("-")
        category = separated[0]
        spend = decimal.Decimal(separated[1])

        c.execute("UPDATE budget SET spend = %s WHERE category_name = %s AND username = %s;", (spend, category, username))

        c.execute("SELECT budget FROM budget WHERE category_name = %s AND username = %s", (category, username))
        budget = c.fetchone()[0]
        remainder = budget - spend
        bot.reply_to(message, f"Wah so much ah? Siao liao... Rest of the month eat grass liao lor. Spent ${spend}, so now left ${remainder} for {category}.")

        if budget <= 0:
            bot.reply_to(message, "How can liddat... Next time no money buy house lor. Die liao.")

        conn.commit()
        c.execute("rollback")
        conn.close
    except ValueError:
        bot.reply_to(message, "Eh don't anyhow, type numbers la.")
        c.execute("rollback")
    except IndexError:
        bot.reply_to(message, "Walao fella really anyhow... Type properly bro.")
        c.execute("rollback")
    except TypeError:
        bot.reply_to(message, "Sure you got create budget for this anot? /add first ba.")
        c.execute("rollback")


@bot.message_handler(commands=['reset'])
def reset(message):
    msg = bot.send_message(message.chat.id, "Okay lai, tell me which budget category you want to reset.\nReset means that it goes back to the original amount hor.")
    bot.register_next_step_handler(msg, process_reset)


def process_reset(message):
    username = message.from_user.id
    username = str(username)
    category = message.text
    spend = 0

    try:
        c.execute("UPDATE budget SET spend = %s WHERE category_name = %s and username = %s", (spend, category, username))
        
        c.execute("SELECT budget FROM budget WHERE category_name = %s AND username = %s", (category, username))
        budget = c.fetchone()[0]
        bot.reply_to(message, f"Done. Your budget reset to ${budget} already!")

        conn.commit()
        c.execute("rollback")
        conn.close
    except TypeError:
        bot.reply_to(message, "Hmm... cannot find the category leh. You /add already anot?")
        c.execute("rollback")


# def monthly_job(message): 
#     username = message.from_user.id
#     username = str(username)
#     c.execute("SELECT update_monthly FROM budget WHERE username = %s", (username,))
#     flag = c.fetchone()[0]

#     if flag == True: 

#     for user in user_list:
#         if date.today().day == 1:
#             user = str(user)
#             spend = 0
#             c.execute("UPDATE budget SET spend = %s WHERE username = %s", (spend, user))
#             conn.commit()
#             c.execute("rollback")
#             conn.close

#             return bot.send_message(message.chat.id, "New month new budget! I have reset all your budgets already!")


def weekly_job():
    flag = False
    c.execute("SELECT username FROM budget where update_monthly = %s", (flag,))
    user_list = c.fetchall()

    for row in user_list:
        user = row[0]
        user = str(user)
        spend = 0
        c.execute("UPDATE budget SET spend = %s WHERE username = %s", (spend, user))
        conn.commit()
        c.execute("rollback")
        conn.close
        bot.send_messaage(user, "Time really flies... Monday blues again... I make it less blue by resetting your budget ba.")


@bot.message_handler(commands=['delete'])
def delete(message):
    msg = bot.send_message(message.chat.id, "Okay lai, tell me which category you want delete?")
    bot.register_next_step_handler(msg, process_delete)


def process_delete(message):
    username = message.from_user.id
    username = str(username)
    msg = message.text

    # c.execute("DELETE FROM budget WHERE category_name = %s AND username = %s", (msg, username))
    flag = False
    c.execute("SELECT username FROM budget where update_monthly = %s", (flag,))
    user_list = c.fetchall()
    names = ""
    for row in user_list:
        user = row[0]
        names += user
        bot.send_message(user, "hi")
    conn.commit()
    c.execute("rollback")
    conn.close
    #bot.reply_to(message, f"Can liao, delete for you already. {names}")


def schedule_checker():
    while True:
        schedule.run_pending()
        sleep(1)


if __name__ == '__main__':
    bot.infinity_polling()
    sched.add_job(weekly_job, trigger="cron", day_of_week="tue", hour=1, minute=12)
    sched.start()
