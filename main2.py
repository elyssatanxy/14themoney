import decimal
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
    bot.send_message(message.chat.id, "First time here ah? Come, I teach you how use.\n/add to add a new budget... any number also can\n/spend to track when you spend, but don't anyhow spam this one! later your money gone\n/view can view your spending - hopefully got no negatives ah\n/delete help you remove category... spend less save more\n/settings allow you switch between weekly and monthly tracking... very useful de!\n/help if you need help lor, buey paiseh de")


@bot.message_handler(commands=['help'])
def help_message(message):
    bot.send_message(message.chat.id, "No need so shy... Everybody needs help one.")
    bot.send_message(message.chat.id, "Come I tell you again:\n/add to add a new budget... any number also can\n/spend to track when you spend, but don't anyhow spam this one! later your money gone\n/view to view your spending - hopefully got no negatives ah\n/delete help you remove category... spend less save more\n/settings allow you switch between weekly and monthly tracking... very useful de!")
    bot.send_message(message.chat.id, "Still need help ah? Okay lor bopes... go find @elyssatanxy help you ba.")


@bot.message_handler(commands=['settings'])
def settings(message):
    bot.send_message(message.chat.id, "Okay come, how you want to set budget?")
    msg = bot.send_message(message.chat.id, "Send me 'W' for weekly and 'M' for monthly... Thank you ah.")
    bot.register_next_step_handler(msg, process_settings)


def process_settings(message):
    msg = message.text.upper()
    if msg in "W":
        bot.reply_to(message, "Swee! I help you change to weekly tracking liao.")
    elif msg in "M":
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
        all += f"{list}. Left ${row[2]} for {row[1]}\n"
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

            c.execute("INSERT INTO budget (category_name, budget, username) VALUES (%s, %s, %s);", (category, budget, username))
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
        spent = decimal.Decimal(separated[1])

        c.execute("SELECT budget FROM budget WHERE category_name = %s AND username = %s", (category, username))
        budget = c.fetchone()[0]
        budget = budget - spent
        c.execute("UPDATE budget SET budget = %s WHERE category_name = %s AND username = %s;", (budget, category, username))
        bot.reply_to(message, f"Wah so much ah? Siao liao... Rest of the month eat grass liao lor. Left ${budget} for {category}.")

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


@bot.message_handler(commands=['delete'])
def delete(message):
    msg = bot.send_message(message.chat.id, "Okay lai, tell me which category you want delete?")
    bot.register_next_step_handler(msg, process_delete)


def process_delete(message):
    username = message.from_user.id
    username = str(username)
    msg = message.text

    c.execute("DELETE FROM budget WHERE category_name = %s AND username = %s", (msg, username))
    bot.reply_to(message, "Can liao, delete for you already.")


bot.infinity_polling()