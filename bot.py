import os
import telebot
from flask import Flask, request

BOT_TOKEN = os.environ.get("BOT_TOKEN")
RENDER_URL = os.environ.get("RENDER_EXTERNAL_URL")

bot = telebot.TeleBot(BOT_TOKEN)
server = Flask(__name__)

# Dictionary to store keyname → link
storage = {}

# /start command
@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message,
                 "Welcome! 👋\n\n"
                 "Commands:\n"
                 "/save <keyname> → Upload a ZIP and save\n"
                 "/list → Show saved keys\n"
                 "/delete <keyname> → Remove a saved key\n")

# /save command
@bot.message_handler(commands=['save'])
def save(message):
    try:
        keyname = message.text.split(" ", 1)[1]
        # Temporarily store user’s state (key they want to save under)
        storage[message.chat.id] = {"key": keyname}
        bot.reply_to(message, f"Okay! Now send me the ZIP file for '{keyname}'.")
    except IndexError:
        bot.reply_to(message, "⚠️ Usage: /save keyname")

# ZIP file handler
@bot.message_handler(content_types=['document'])
def handle_docs(message):
    if message.document.mime_type == "application/zip":
        user_state = storage.get(message.chat.id)
        if not user_state or "key" not in user_state:
            bot.reply_to(message, "⚠️ First use /save <keyname> before sending the ZIP.")
            return

        keyname = user_state["key"]
        file_info = bot.get_file(message.document.file_id)
        file_link = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_info.file_path}"

        # Save link under the chosen key
        storage[keyname] = file_link
        storage.pop(message.chat.id, None)  # clear temp state

        bot.reply_to(message, f"✅ Saved! Access it anytime with:\n{file_link}")
    else:
        bot.reply_to(message, "⚠️ Please upload a valid ZIP file.")

# /list command
@bot.message_handler(commands=['list'])
def list_files(message):
    if not storage:
        bot.reply_to(message, "📂 No files saved yet.")
        return
    response = "📂 Saved files:\n"
    for key, link in storage.items():
        if isinstance(link, str):  # skip temp states
            response += f"🔑 {key} → {link}\n"
    bot.reply_to(message, response)

# /delete command
@bot.message_handler(commands=['delete'])
def delete(message):
    try:
        keyname = message.text.split(" ", 1)[1]
        if keyname in storage:
            del storage[keyname]
            bot.reply_to(message, f"🗑️ Deleted '{keyname}'.")
        else:
            bot.reply_to(message, f"⚠️ No file found with key '{keyname}'.")
    except IndexError:
        bot.reply_to(message, "⚠️ Usage: /delete keyname")

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
