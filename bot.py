import os
import logging
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
)
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)
from flask import Flask
from threading import Thread
from googletrans import Translator
from langdetect import detect
from datetime import datetime

# === Config ===
BOT_TOKEN = os.environ.get("BOT_TOKEN", "7560563197:AAHmmIygYMElUtUPnYc2Iu05v5y1KOTWpnY")
PORT = int(os.environ.get("PORT", 8080))
translator = Translator()

LANGUAGES = {
    'en': 'English', 'bn': 'বাংলা', 'hi': 'हिंदी', 'ur': 'اردو', 'ta': 'தமிழ்',
    'te': 'తెలుగు', 'fr': 'Français', 'de': 'Deutsch', 'es': 'Español', 'ru': 'Русский',
    'ar': 'العربية', 'zh-cn': '中文', 'ja': '日本語', 'it': 'Italiano', 'pt': 'Português'
}

user_files = {}

# === Logging ===
logging.basicConfig(level=logging.INFO)

# === Flask App ===
flask_app = Flask(__name__)
@flask_app.route('/')
def index():
    return "Subtitle Translator Bot by @RahatMx Running!", 200

def run_flask():
    flask_app.run(host="0.0.0.0", port=PORT)

# === Helpers ===
def is_subtitle(filename):
    return os.path.splitext(filename)[1].lower() in ['.srt', '.vtt', '.ass']

def format_translated_filename(path, lang):
    name, ext = os.path.splitext(os.path.basename(path))
    return f"downloads/{name}_translated_{lang}{ext}"

async def translate_file(path, lang_code):
    translated_lines = []
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line_strip = line.strip()
            if '-->' in line or line_strip.isdigit() or not line_strip:
                translated_lines.append(line)
            else:
                try:
                    translated = translator.translate(line_strip, dest=lang_code).text
                    translated_lines.append(translated + '\n')
                except Exception:
                    translated_lines.append(line)
    out_path = format_translated_filename(path, lang_code)
    with open(out_path, 'w', encoding='utf-8') as f:
        f.writelines(translated_lines)
    return out_path

# === Handlers ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    buttons = [
        [InlineKeyboardButton("Translate Subtitle", url="https://t.me/RM_Movie_Flix")],
        [InlineKeyboardButton("Developer", url="https://t.me/RahatMx")]
    ]
    text = (
        "**Welcome to the Advanced Subtitle Translator Bot!**\n\n"
        "Just send any `.srt`, `.vtt`, or `.ass` file, and select a language to get the translated subtitle file."
    )
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(buttons), parse_mode="Markdown")

async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    doc = update.message.document
    user_id = update.effective_user.id
    filename = doc.file_name

    if not is_subtitle(filename):
        return await update.message.reply_text("Only .srt, .vtt, .ass files are allowed.")

    os.makedirs("downloads", exist_ok=True)
    download_path = f"downloads/{user_id}_{filename}"
    await doc.get_file().download_to_drive(download_path)
    user_files[user_id] = download_path

    buttons = []
    for code, name in LANGUAGES.items():
        buttons.append([InlineKeyboardButton(name, callback_data=f"lang_{code}")])
    
    await update.message.reply_text(
        f"Received **{filename}**\nNow select the language you want to translate to:",
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode="Markdown"
    )

async def handle_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = query.data.split("_")[1]
    user_id = query.from_user.id

    if user_id not in user_files:
        return await query.edit_message_text("Subtitle file not found. Please send a valid file again.")

    input_path = user_files[user_id]
    await query.edit_message_text("Translating subtitle, please wait...")

    try:
        translated_path = await translate_file(input_path, lang)
        translated_filename = os.path.basename(translated_path)

        await context.bot.send_document(
            chat_id=user_id,
            document=InputFile(translated_path),
            filename=translated_filename,
            caption=(
                f"Translated to **{LANGUAGES[lang]}**\n"
                f"Created by [Rahat](https://t.me/RahatMx) | "
                f"[RM Movie Flix](https://t.me/RM_Movie_Flix)"
            ),
            parse_mode="Markdown"
        )

        os.remove(input_path)
        os.remove(translated_path)
        del user_files[user_id]
    except Exception as e:
        await query.edit_message_text(f"Failed to translate: {e}")

async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Please send a valid subtitle file!")

# === Main Runner ===
if __name__ == '__main__':
    Thread(target=run_flask).start()
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_file))
    app.add_handler(CallbackQueryHandler(handle_language, pattern="^lang_"))
    app.add_handler(MessageHandler(filters.ALL, unknown))

    print("Bot is running on polling...")
    app.run_polling()
