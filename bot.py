import os
import telebot
from telebot import types
from flask import Flask

# Get token from environment variable
BOT_TOKEN = os.environ.get("BOT_TOKEN")

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# In-memory store (dictionary)
files_db = {}

# --- BOT COMMANDS ---

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(
        message,
        "👋 Welcome!\n\n"
        "To save a ZIP:\n"
        "`/save keyname` and then upload your zip file.\n\n"
        "Other commands:\n"
        "/list - show saved files\n"
        "/delete keyname - delete a saved file",
        parse_mode="Markdown"
    )

# Step 1: Ask for keyname
@bot.message_handler(commands=['save'])
def save_command(message):
    try:
        keyname = message.text.split(maxsplit=1)[1]
    except IndexError:
        bot.reply_to(message, "❌ Usage: /save keyname")
        return

    bot.reply_to(message, f"📂 Now send me the ZIP file for `{keyname}`", parse_mode="Markdown")

    # Register next step handler
    bot.register_next_step_handler(message, lambda msg: save_file(msg, keyname))

# Step 2: Save file
def save_file(message, keyname):
    if not message.document or not message.document.file_name.endswith(".zip"):
        bot.reply_to(message, "❌ Please send a valid ZIP file.")
        return

    file_id = message.document.file_id
    files_db[keyname] = file_id

    link = f"https://t.me/{bot.get_me().username}?start={keyname}"
    bot.reply_to(message, f"✅ File saved as `{keyname}`\n🔗 Link: {link}", parse_mode="Markdown")

# Handle deep-linking
@bot.message_handler(func=lambda m: m.text and m.text.startswith("/start "))
def send_file(message):
    keyname = message.text.split(maxsplit=1)[1]
    if keyname in files_db:
        bot.send_document(message.chat.id, files_db[keyname], caption=f"📦 Here is `{keyname}`", parse_mode="Markdown")
    else:
        bot.reply_to(message, "❌ File not found.")

# List saved files
@bot.message_handler(commands=['list'])
def list_files(message):
    if not files_db:
        bot.reply_to(message, "📭 No files saved.")
    else:
        file_list = "\n".join([f"- {k}" for k in files_db.keys()])
        bot.reply_to(message, f"📂 Saved files:\n{file_list}")

# Delete a file
@bot.message_handler(commands=['delete'])
def delete_file(message):
    try:
        keyname = message.text.split(maxsplit=1)[1]
    except IndexError:
        bot.reply_to(message, "❌ Usage: /delete keyname")
        return

    if keyname in files_db:
        del files_db[keyname]
        bot.reply_to(message, f"🗑️ Deleted `{keyname}`", parse_mode="Markdown")
    else:
        bot.reply_to(message, "❌ File not found.")

# --- FLASK SERVER (keep-alive on Render) ---
@app.route('/')
def home():
    return "Bot is running fine on Render!"

# --- RUN BOTH BOT + FLASK ---
if __name__ == "__main__":
    import threading

    def run_bot():
        print("🤖 Bot polling started...")
        bot.infinity_polling(timeout=60, long_polling_timeout=30)

    def run_flask():
        port = int(os.environ.get("PORT", 10000))
        app.run(host="0.0.0.0", port=port)

    threading.Thread(target=run_bot).start()
    run_flask()

