import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, constants
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from langdetect import detect
from deep_translator import GoogleTranslator
from flask import Flask
import threading

# Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

TOKEN = os.getenv("BOT_TOKEN", "7560563197:AAHmmIygYMElUtUPnYc2Iu05v5y1KOTWpnY")

LANGUAGES = {
    'bn': 'বাংলা', 'en': 'English', 'hi': 'हिन्दी', 'es': 'Español',
    'fr': 'Français', 'de': 'Deutsch', 'ru': 'Русский', 'ar': 'العربية',
    'zh-cn': '中文', 'pt': 'Português', 'ja': '日本語', 'ko': '한국어', 'tr': 'Türkçe'
}

# Start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [
        [InlineKeyboardButton("Join Channel", url="https://t.me/RM_Movie_Flix")],
        [InlineKeyboardButton("Developer", url="https://t.me/RahatMx")],
    ]
    await update.message.reply_text(
        "Welcome to the Advanced Subtitle Translator Bot!\n\n"
        "Send me any `.srt`, `.vtt`, or `.ass` subtitle file and I’ll translate it.",
        reply_markup=InlineKeyboardMarkup(kb)
    )

# Handle subtitle files
async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    doc = update.message.document
    if not doc.file_name.endswith(('.srt', '.vtt', '.ass')):
        await update.message.reply_text("Only `.srt`, `.vtt`, `.ass` files are supported.")
        return

    file_path = f"downloads/{doc.file_name}"
    os.makedirs("downloads", exist_ok=True)
    await doc.get_file().download_to_drive(file_path)
    context.user_data['file'] = file_path
    context.user_data['file_name'] = doc.file_name

    buttons = [
        [InlineKeyboardButton(v + f" ({k})", callback_data=k)] for k, v in LANGUAGES.items()
    ]
    await update.message.reply_text(
        "Select the target language to translate your subtitle:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

# Translate on language selection
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    target_lang = query.data
    file_path = context.user_data.get('file')

    if not file_path:
        await query.edit_message_text("No file found.")
        return

    translated_lines = []
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        for line in lines:
            try:
                if line.strip() and not line[0].isdigit() and "-->" not in line:
                    translated = GoogleTranslator(source='auto', target=target_lang).translate(line.strip())
                    translated_lines.append(translated + "\n")
                else:
                    translated_lines.append(line)
            except Exception as e:
                translated_lines.append(line)

    new_filename = f"{os.path.splitext(context.user_data['file_name'])[0]}_translated_{target_lang}.srt"
    new_path = f"downloads/{new_filename}"
    with open(new_path, 'w', encoding='utf-8') as f:
        f.writelines(translated_lines)

    await query.message.reply_document(document=open(new_path, 'rb'), filename=new_filename,
        caption=f"Translated to {LANGUAGES.get(target_lang)} ({target_lang})")
    
    os.remove(file_path)
    os.remove(new_path)
    context.user_data.clear()

# Run Flask for uptime
app = Flask(__name__)

@app.route('/')
def home():
    return 'Subtitle Bot is Alive!'

def run_flask():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

if __name__ == '__main__':
    threading.Thread(target=run_flask).start()
    app_tg = ApplicationBuilder().token(TOKEN).build()
    app_tg.add_handler(CommandHandler("start", start))
    app_tg.add_handler(MessageHandler(filters.Document.ALL, handle_file))
    app_tg.add_handler(CallbackQueryHandler(button))
    print("Bot running...")
    app_tg.run_polling()
