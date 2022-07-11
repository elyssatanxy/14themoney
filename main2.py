import telebot
from telebot import types
import sqlite3
import Constants as keys
import telegram

bot = telebot.TeleBot(keys.API_KEY)
global category
global budget

@bot.message_handler(commands=['start'])
def welcome_message(message):
    bot.send_message(message.chat.id, "Welcome to ONE FOR THE MONEY Telegram chat bot!")
    bot.send_message(message.chat.id, "Commands list:\n/add to add a new budget\n/view to view your spending")


@bot.message_handler(commands=['add'])
def add(message):
    msg = bot.send_message(message.chat.id, text="Okay! Enter your list of budgets (or just 1!) in this format:\ncategory1-budget1\ncategory2-budget2\n<b>(e.g. Food-200)</b>", parse_mode=telegram.ParseMode.HTML)
    bot.register_next_step_handler(msg, process_budget)

def process_budget(message):
    conn = sqlite3.connect('budgetDatabase.db')
    c = conn.cursor()

    username = message.from_user.id
    username = str(username)
    msg = message.text

    try:
        separated = msg.split("-")
        category = separated[0]
        budget = float(separated[1])

        rc = c.execute(f"INSERT OR IGNORE INTO BUDGET VALUES ({username})")
        rc = c.execute("INSERT INTO CATEGORY ('category_name', 'budget', 'username') VALUES (?, ?, ?)", (category, budget, username))
        print("Added")
        bot.reply_to(message, f"Added ${budget:.2f} for {category}!")
    except ValueError:
        bot.reply_to(message, "Not a number...")
    except sqlite3.InternalError:
        msg = bot.reply_to(message, "You have already created a budget for this category! Do you want to update the budget instead?\nType 'Y' to continue or 'N' to cancel")
        bot.register_next_step_handler(msg, update_budget)

def update_budget(message):
    msg = message.text.upper()
    if msg in "Y":
        conn = sqlite3.connect(('budgetDatabase.db'))
        c = conn.cursor()
        username = message.from_user.id
        username = str(username)

        rc = c.execute("UPDATE CATEGORY SET budget = ? WHERE category_name = ? AND username = ?", (budget, category, username))
    elif msg in "N":
        bot.reply_to(message, "Okay, no changes made!")

    conn.commit()
    conn.close

# @bot.message_handler(commands=['view'])
# def view(message):
#

bot.enable_save_next_step_handlers(delay=0)
bot.load_next_step_handlers()
bot.infinity_polling()