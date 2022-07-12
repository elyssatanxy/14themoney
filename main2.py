import decimal

import telebot
import Constants as keys
import psycopg2

bot = telebot.TeleBot(token=keys.API_KEY)


@bot.message_handler(commands=['start'])
def welcome_message(message):
    bot.send_message(message.chat.id, "Eh hello! Welcome to 14themoney!")
    bot.send_message(message.chat.id, "First time here ah? Come, I teach you how use.\n/add to add a new budget... any number also can\n/view to view your spending - hopefully got no negatives ah\n/help if you need help lor, buey paiseh de")


@bot.message_handler(commands=['help'])
def welcome_message(message):
    bot.send_message(message.chat.id, "No need so shy... Everybody needs help one.")
    bot.send_message(message.chat.id, "Come I tell you again:\n/add to add a new budget... any number also can\n/view to view your spending - hopefully got no negatives ah")
    bot.send_message(message.chat.id, "Still need help ah? Okay lor bopes... go find @elyssatanxy help you ba.")


@bot.message_handler(commands=['view'])
def view(message):
    conn = psycopg2.connect(
        host="ec2-3-219-229-143.compute-1.amazonaws.com",
        database="dacl3l363nbjcu",
        user="dcthdqavgensio",
        password="2f71fed74d2a555b9575615bfad5bf07d1f707f8ddac2391608f158bb7969c68"
    )
    c = conn.cursor()
    username = message.from_user.id
    username = str(username)

    c.execute("SELECT * FROM CATEGORY WHERE username = %s", (username,))
    print(c.fetchone())


@bot.message_handler(commands=['add'])
def add(message):
    msg = bot.send_message(message.chat.id,
                           text="Okay come, enter your budgets liddat:\ncategory1-budget1\ncategory2-budget2\n<b>(e.g. Food-200)</b>",
                           parse_mode='HTML')
    bot.register_next_step_handler(msg, process_budget)


def process_budget(message):
    conn = psycopg2.connect(
        host="ec2-3-219-229-143.compute-1.amazonaws.com",
        database="dacl3l363nbjcu",
        user="dcthdqavgensio",
        password="2f71fed74d2a555b9575615bfad5bf07d1f707f8ddac2391608f158bb7969c68"
    )
    c = conn.cursor()

    username = message.from_user.id
    username = str(username)
    msg = message.text

    try:
        separated = msg.split("-")
        global category
        category = separated[0]
        global budget
        budget = float(separated[1])

        c.execute(f"INSERT INTO BUDGET (username) VALUES ({username}) ON CONFLICT (username) DO NOTHING;")
        c.execute("INSERT INTO CATEGORY (category_name, budget, username) VALUES (%s, %s, %s);",
                  (category, budget, username))
        print("Added")
        bot.reply_to(message, f"Okay liao, added ${budget:.2f} for {category}! Don't overspend hor.")

        if budget > 500:
            bot.reply_to(message, "Eh... can spend so much meh? Got give money to your parents anot?")

        conn.commit()
        conn.close
    except ValueError:
        bot.reply_to(message, "Eh this one not a number leh... Don't anyhow!")
    except psycopg2.IntegrityError:
        msg = bot.reply_to(message,
                           f"Alamak... You already set a budget for {category} leh... You want update budget instead anot?\nType 'Y' for yas or 'N' for naur")
        bot.register_next_step_handler(msg, update_budget)
    except IndexError:
        msg = bot.reply_to(message, "Huh? Wo bu ming bai... Try again please...")
        bot.register_next_step_handler(msg, process_budget)


def update_budget(message):
    msg = message.text.upper()
    if msg in "Y":
        conn = psycopg2.connect(
            host="ec2-3-219-229-143.compute-1.amazonaws.com",
            database="dacl3l363nbjcu",
            user="dcthdqavgensio",
            password="2f71fed74d2a555b9575615bfad5bf07d1f707f8ddac2391608f158bb7969c68"
        )
        c = conn.cursor()
        username = message.from_user.id
        username = str(username)

        c.execute("UPDATE CATEGORY SET budget = ? WHERE category_name = ? AND username = ?",
                  (budget, category, username))
        bot.reply_to(message, f"Okay liao, I updated budget for {category} to ${budget} already!")

        conn.commit()
        conn.close
    elif msg in "N":
        bot.reply_to(message, "Can, I don't change anything lor.")


@bot.message_handler(commands=['spend'])
def spend(message):
    msg = bot.send_message(message.chat.id, "Aiyo spend money again... Sigh... How much now? Tell me like this ah:\ncategory1-amount")
    bot.register_next_step_handler(msg, process_spending)


def process_spending(message):
    conn = psycopg2.connect(
        host="ec2-3-219-229-143.compute-1.amazonaws.com",
        database="dacl3l363nbjcu",
        user="dcthdqavgensio",
        password="2f71fed74d2a555b9575615bfad5bf07d1f707f8ddac2391608f158bb7969c68"
    )
    c = conn.cursor()

    username = message.from_user.id
    username = str(username)
    msg = message.text

    try:
        separated = msg.split("-")
        category = separated[0]
        spent = decimal.Decimal(separated[1])
        c.execute("SELECT budget FROM CATEGORY WHERE category_name = %s AND username = %s", (category, username))
        budget = c.fetchone()[0]
        budget = budget - spent
        c.execute("UPDATE CATEGORY SET budget = %s WHERE category_name = %s AND username = %s;", (budget, category, username))
        print("Deducted")
        bot.reply_to(message, f"Wah so much ah? Siao liao... Rest of the month eat grass liao lor. Left ${budget} for {category}.")

        if budget <= 0:
            bot.reply_to(message, "How can liddat... Next time no money buy house lor. Die liao.")

        conn.commit()
        conn.close
    except ValueError:
        bot.reply_to(message, "Eh don't anyhow, type properly leh.")
    except psycopg2.IntegrityError:
        bot.reply_to(message, "Sure you got create budget for this anot? /add first ba.")

bot.infinity_polling()