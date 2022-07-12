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


@bot.message_handler(commands=['add'])
def add(message):
    msg = bot.send_message(message.chat.id,
                           text="Okay! Enter your list of budgets (or just 1!) in this format:\ncategory1-budget1\ncategory2-budget2\n<b>(e.g. Food-200)</b>",
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
        bot.reply_to(message, f"Added ${budget:.2f} for {category}!")

        conn.commit()
        conn.close
    except ValueError:
        bot.reply_to(message, "Not a number...")
    except psycopg2.IntegrityError:
        msg = bot.reply_to(message,
                           "You have already created a budget for this category! Do you want to update the budget instead?\nType 'Y' to continue or 'N' to cancel")
        bot.register_next_step_handler(msg, update_budget)
    except IndexError:
        bot.reply_to(message, "Didn't quite get that... Please try again.")


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
        bot.reply_to(message, f"Okay, budget for {category} udpated to ${budget}!")

        conn.commit()
        conn.close
    elif msg in "N":
        bot.reply_to(message, "Okay, no changes made!")


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

    c.execute("SELECT * FROM CATEGORY WHERE username = ?", (username,))
    print(c.fetchone())


bot.infinity_polling()