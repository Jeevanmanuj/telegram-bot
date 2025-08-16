import os
import telebot
from flask import Flask, request

BOT_TOKEN = os.environ.get("BOT_TOKEN")
RENDER_URL = os.environ.get("RENDER_EXTERNAL_URL")

bot = telebot.TeleBot(BOT_TOKEN)
server = Flask(__name__)

# /start command
@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "Welcome! Send /save <keyname> and then upload a ZIP file.")

# /save command
@bot.message_handler(commands=['save'])
def save(message):
    try:
        keyname = message.text.split(" ", 1)[1]
        bot.reply_to(message, f"Great! Now send me the ZIP file for '{keyname}'.")
    except IndexError:
        bot.reply_to(message, "Usage: /save keyname")

# ZIP file handler
@bot.message_handler(content_types=['document'])
def handle_docs(message):
    if message.document.mime_type == "application/zip":
        file_info = bot.get_file(message.document.file_id)
        file_link = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_info.file_path}"
        bot.reply_to(message, f"Here’s your download link:\n{file_link}")
    else:
        bot.reply_to(message, "Please upload a ZIP file.")

# Flask webhook route
@server.route(f"/{BOT_TOKEN}", methods=['POST'])
def webhook():
    json_str = request.get_data().decode('UTF-8')
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "!", 200

@server.route("/")
def index():
    bot.remove_webhook()
    bot.set_webhook(url=f"{RENDER_URL}/{BOT_TOKEN}")
    return "Bot is running!", 200

if __name__ == "__main__":
    server.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
