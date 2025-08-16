import os
import telebot
from flask import Flask, request

# Get bot token from environment variable
BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN is not set in environment variables!")

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# Store keyname temporarily until file is uploaded
user_keys = {}

# Command: /save keyname
@bot.message_handler(commands=['save'])
def save_key(message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        bot.reply_to(message, "❌ Usage: /save <keyname>")
        return
    keyname = parts[1].strip()
    user_keys[message.from_user.id] = keyname
    bot.reply_to(message, f"✅ Keyname saved: `{keyname}`\nNow send me a ZIP file.", parse_mode="Markdown")

# Handle ZIP upload
@bot.message_handler(content_types=['document'])
def handle_zip(message):
    if message.document.mime_type != "application/zip":
        bot.reply_to(message, "❌ Please upload a valid ZIP file.")
        return

    user_id = message.from_user.id
    if user_id not in user_keys:
        bot.reply_to(message, "⚠️ Please set a keyname first using `/save keyname`.")
        return

    keyname = user_keys[user_id]

    # Get Telegram file_id (this stays permanent on Telegram servers)
    file_id = message.document.file_id

    # Generate a direct link format
    file_link = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_id}"

    bot.reply_to(
        message,
        f"✅ Your file has been saved!\n\n🔑 Key: `{keyname}`\n📂 File Link: {file_link}",
        parse_mode="Markdown"
    )

    # Clear keyname for next time
    del user_keys[user_id]

# Root route to check server
@app.route("/", methods=['GET'])
def home():
    return "🤖 Bot is running with Webhook!", 200

# Webhook route
@app.route(f'/{BOT_TOKEN}', methods=['POST'])
def webhook():
    update = telebot.types.Update.de_json(request.stream.read().decode("utf-8"))
    bot.process_new_updates([update])
    return "OK", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    WEBHOOK_URL = f"https://{os.environ.get('RENDER_EXTERNAL_URL')}/{BOT_TOKEN}"

    # Remove old webhook before setting new one
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL)

    print(f"🤖 Webhook set to {WEBHOOK_URL}")
    app.run(host="0.0.0.0", port=port)

