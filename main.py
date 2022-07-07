import sqlite3
from telegram import Update, bot, ChatAction, update
import Constants as keys
from telegram.ext import *

print("Bot started")

def start(update: Update, context: CallbackContext) -> None:
    """Sends a message when /start command is sent"""
    update.message.reply_text("Welcome to ONE FOR THE MONEY Telegram chat bot!")

def help(update: Update, context:CallbackContext) -> None:
    """Sends a message when /help command is sent"""
    update.message.reply_text("Feel free to PM @elyssatanxy!")

def error(update: Update, context: CallbackContext) -> None:
    """Prints what the errors are to terminal"""
    print(f"Update {update} caused error {context.error}")

# def handle_message(update, context):
#     text = str(update.message.text).lower()
#     response = R.sample_response(text)
#
#     update.message.reply_text(response)

def add_budget(update: Update, context: CallbackContext) -> None:
    """Adds budget to the DB"""
    # bot.send_chat_action(chat_id=update.message.chat_id, action=ChatAction.TYPING)

    # connects to DB
    conn = sqlite3.connect('budgetDatabase.db')
    c = conn.cursor()

    chat_id = update.message.chat_id
    chat_id = str(chat_id)
    msg = update.message.text.lower()

    try:
        msg = msg.removeprefix("/add_budget ")
        print(msg)
        budget = int(msg)
        rc = c.execute(f"INSERT INTO BUDGET VALUES ({chat_id}, {budget})")
        update.message.reply_text(f"Added ${budget}!")
    except ValueError:
        update.message.reply_text("Not a number...")

    conn.commit()
    conn.close

# def update_budget():

# def get_budget():
#     bot.send_chat_action(chat_id=update.message.chat_id, action=ChatAction.TYPING)
#
#     conn = sqlite3.connect('budgetDatabase.db')
#     c = conn.cursor()
#
#     chat_id = update.message.chat_id
#     chat_id = str(chat_id)

def main():
    updater = Updater(keys.API_KEY, use_context=True)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help))
    dispatcher.add_handler(CommandHandler("add_budget", add_budget))

    # dispatcher.add_handler(MessageHandler(Filters.text, handle_message))

    dispatcher.add_error_handler(error)

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    """use google cloud platform to keep it running"""
    main()