import telebot
from telebot import types
import Constants as keys
import telegram
import psycopg2

bot = telebot.TeleBot(keys.API_KEY)

@bot.message_handler(commands=['start'])
def welcome_message(message):
    bot.send_message(message.chat.id, "Welcome to ONE FOR THE MONEY Telegram chat bot!")
    bot.send_message(message.chat.id, "Commands list:\n/add to add a new budget\n/view to view your spending")


@bot.message_handler(commands=['add'])
def add(message):
    msg = bot.send_message(message.chat.id, text="Okay! Enter your list of budgets (or just 1!) in this format:\ncategory1-budget1\ncategory2-budget2\n<b>(e.g. Food-200)</b>", parse_mode=telegram.ParseMode.HTML)
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
        c.execute("INSERT INTO CATEGORY (category_name, budget, username) VALUES (%s, %s, %s);", (category, budget, username))
        print("Added")
        bot.reply_to(message, f"Added ${budget:.2f} for {category}!")

        conn.commit()
        conn.close
    except ValueError:
        bot.reply_to(message, "Not a number...")
    except sqlite3.IntegrityError:
        msg = bot.reply_to(message, "You have already created a budget for this category! Do you want to update the budget instead?\nType 'Y' to continue or 'N' to cancel")
        bot.register_next_step_handler(msg, update_budget)
    except IndexError:
        bot.reply_to(message, "Didn't quite get that... Please try again.")

def update_budget(message):
    msg = message.text.upper()
    if msg in "Y":
        conn = sqlite3.connect('budgetDatabase.db')
        c = conn.cursor()
        username = message.from_user.id
        username = str(username)

        c.execute("UPDATE CATEGORY SET budget = ? WHERE category_name = ? AND username = ?", (budget, category, username))
        bot.reply_to(message, f"Okay, budget for {category} udpated to ${budget}!")

        conn.commit()
        conn.close
    elif msg in "N":
        bot.reply_to(message, "Okay, no changes made!")

@bot.message_handler(commands=['view'])
def view(message):
    conn = sqlite3.connect('budgetDatabase.db')
    c = conn.cursor()
    username = message.from_user.id
    username = str(username)

    c.execute("SELECT * FROM CATEGORY WHERE username = ?", (username,))
    print(c.fetchone())

bot.enable_save_next_step_handlers(delay=0)
bot.load_next_step_handlers()
bot.infinity_polling()