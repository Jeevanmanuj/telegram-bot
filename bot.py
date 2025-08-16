import telebot
import json
import os

# 🔹 Replace with your bot token
BOT_TOKEN = "YOUR_BOT_TOKEN"
bot = telebot.TeleBot(BOT_TOKEN)

INDEX_FILE = "file_index.json"

# Load saved file_ids from disk
if os.path.exists(INDEX_FILE):
    with open(INDEX_FILE, "r") as f:
        saved_files = json.load(f)
else:
    saved_files = {}

# Save file_ids back to disk
def save_index():
    with open(INDEX_FILE, "w") as f:
        json.dump(saved_files, f)

# --- Start ---
@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message,
                 "👋 Welcome!\n\n"
                 "Use these commands:\n"
                 "/save <key> + attach ZIP\n"
                 "/list - show saved keys\n"
                 "/get <key> - retrieve ZIP\n"
                 "/delete <key> - remove ZIP")

# --- Save file ---
@bot.message_handler(commands=['save'])
def save_file(message):
    parts = message.text.split()
    if len(parts) < 2:
        bot.reply_to(message, "⚠️ Usage: /save <key>")
        return
    key = parts[1]
    bot.reply_to(message, f"📩 Now send me the ZIP file for key: {key}")
    bot.register_next_step_handler(message, lambda m: receive_file(m, key))

def receive_file(message, key):
    if not message.document:
        bot.reply_to(message, "⚠️ Please send a ZIP file.")
        return
    file_id = message.document.file_id
    saved_files[key] = file_id
    save_index()
    bot.reply_to(message, f"✅ File saved with key: {key}")

# --- List files ---
@bot.message_handler(commands=['list'])
def list_files(message):
    if not saved_files:
        bot.reply_to(message, "📂 No files saved yet.")
    else:
        keys = "\n".join(saved_files.keys())
        bot.reply_to(message, f"📂 Saved keys:\n{keys}")

# --- Get file ---
@bot.message_handler(commands=['get'])
def get_file(message):
    parts = message.text.split()
    if len(parts) < 2:
        bot.reply_to(message, "⚠️ Usage: /get <key>")
        return
    key = parts[1]
    if key in saved_files:
        bot.send_document(message.chat.id, saved_files[key])
    else:
        bot.reply_to(message, "❌ File not found.")

# --- Delete file ---
@bot.message_handler(commands=['delete'])
def delete_file(message):
    parts = message.text.split()
    if len(parts) < 2:
        bot.reply_to(message, "⚠️ Usage: /delete <key>")
        return
    key = parts[1]
    if key in saved_files:
        del saved_files[key]
        save_index()
        bot.reply_to(message, f"🗑 File with key '{key}' deleted.")
    else:
        bot.reply_to(message, "❌ Key not found.")

# --- Run bot ---
print("🤖 Bot is running...")
bot.infinity_polling()
