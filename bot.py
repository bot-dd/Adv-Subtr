import os
from flask import Flask
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)
from langdetect import detect
from googletrans import Translator

# ========== Configuration ==========
TOKEN = os.environ.get("BOT_TOKEN", "your_bot_token_here")
LANGUAGES = {
    "en": "English", "bn": "Bengali", "hi": "Hindi",
    "ta": "Tamil", "te": "Telugu", "ml": "Malayalam",
    "ar": "Arabic"
}
SUPPORTED_EXTS = ["srt", "ass", "vtt", "sub"]
translator = Translator()
app = Flask(__name__)

# ========== Flask Web ==========
@app.route("/")
def index():
    return "Bot is running!"

# ========== Bot Commands ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Welcome to Subtitle Translator Bot!\nJust send me a `.srt`, `.ass`, `.vtt`, or `.sub` subtitle file.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Help", callback_data="help"),
             InlineKeyboardButton("About", callback_data="about")]
        ])
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Upload a subtitle file. Then choose a language. You'll get the translated subtitle back.")

async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Subtitle Translator Bot\nCreated by @RahatMx\nPowered by RM Movie Flix")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data in LANGUAGES:
        file_id = context.user_data.get("file_id")
        ext = context.user_data.get("file_ext")
        lang = data

        file = await context.bot.get_file(file_id)
        path = await file.download_to_drive()

        with open(path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        output = []
        for line in lines:
            if line.strip() and not line.strip().isdigit() and "-->" not in line:
                try:
                    src_lang = detect(line)
                    translated = translator.translate(line.strip(), src=src_lang, dest=lang).text
                    output.append(translated + "\n")
                except Exception:
                    output.append(line)
            else:
                output.append(line)

        out_file = f"translated_{LANGUAGES[lang]}.{ext}"
        with open(out_file, "w", encoding="utf-8") as f:
            f.writelines(output)

        await query.message.reply_document(
            document=open(out_file, "rb"),
            filename=out_file,
            caption=f"Translated to {LANGUAGES[lang]}"
        )
    elif data == "help":
        await query.edit_message_text("Send a subtitle file and choose the language you want it translated to.")
    elif data == "about":
        await query.edit_message_text("Created by @RahatMx | Powered by RM Movie Flix")

# ========== Subtitle Upload ==========
async def handle_subtitle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file = update.message.document
    ext = file.file_name.split(".")[-1].lower()
    if ext not in SUPPORTED_EXTS:
        await update.message.reply_text("Unsupported file format. Please send a valid subtitle file (srt, ass, vtt, sub).")
        return

    context.user_data["file_id"] = file.file_id
    context.user_data["file_ext"] = ext

    buttons = [[InlineKeyboardButton(name, callback_data=code)] for code, name in LANGUAGES.items()]
    await update.message.reply_text("Choose a language to translate to:", reply_markup=InlineKeyboardMarkup(buttons))

# ========== Run App ==========
def main():
    tg_app = ApplicationBuilder().token(TOKEN).build()

    tg_app.add_handler(CommandHandler("start", start))
    tg_app.add_handler(CommandHandler("help", help_command))
    tg_app.add_handler(CommandHandler("about", about))
    tg_app.add_handler(MessageHandler(filters.Document.ALL, handle_subtitle))
    tg_app.add_handler(CallbackQueryHandler(button_handler))

    tg_app.run_polling()

if __name__ == "__main__":
    main()
