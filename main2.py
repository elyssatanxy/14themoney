import telebot
from telebot import types
import sqlite3
import Constants as keys
import telegram
from flask import Flask, request
import os

bot = telebot.TeleBot(keys.API_KEY)
server = Flask(__name__)

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
        global category
        category = separated[0]
        global budget
        budget = float(separated[1])

        c.execute(f"INSERT OR IGNORE INTO BUDGET (username) VALUES ({username})")
        c.execute("INSERT INTO CATEGORY (category_name, budget, username) VALUES (?, ?, ?)", (category, budget, username))
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

@server.route('/' + keys.API_KEY, methods=['POST'])
def getMessage():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "!", 200

@server.route("/")
def webhook():
    bot.remove_webhook()
    bot.set_webhook(url='https://calm-savannah-80748.herokuapp.com/' + keys.API_KEY)
    return "!", 200

if __name__ == "__main__":
    server.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))
