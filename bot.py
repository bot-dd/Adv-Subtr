import os
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
)
from deep_translator import GoogleTranslator
from langdetect import detect
from flask import Flask
import threading
import aiofiles

# Config
TOKEN = os.getenv("BOT_TOKEN", "7560563197:AAHmmIygYMElUtUPnYc2Iu05v5y1KOTWpnY")
PORT = int(os.environ.get("PORT", 5000))
SUPPORTED_EXTENSIONS = ['.srt', '.vtt', '.ass', '.sub']

# Flask App
app = Flask(__name__)

@app.route('/')
def index():
    return "Subtitle Bot Running - Created by Rahat"

def start_flask():
    app.run(host="0.0.0.0", port=PORT)

# Start Command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "**Welcome to Subtitle Translator Bot!**\n\nSend a subtitle file (.srt, .vtt, .ass, .sub) and I'll translate it automatically.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Developer", url="https://t.me/RahatMx")],
            [InlineKeyboardButton("Main Channel", url="https://t.me/RM_Movie_Flix")]
        ])
    )

# Subtitle Translator
async def handle_subtitle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    doc = update.message.document
    filename = doc.file_name.lower()
    file_ext = os.path.splitext(filename)[1]

    if file_ext not in SUPPORTED_EXTENSIONS:
        await update.message.reply_text("Unsupported file format! Use: `.srt`, `.vtt`, `.ass`, `.sub`")
        return

    await update.message.reply_text("Downloading and translating subtitle...")

    file_path = f"temp/{filename}"
    os.makedirs("temp", exist_ok=True)

    file = await context.bot.get_file(doc.file_id)
    await file.download_to_drive(file_path)

    try:
        async with aiofiles.open(file_path, mode="r", encoding="utf-8", errors="ignore") as f:
            content = await f.read()
    except Exception as e:
        await update.message.reply_text(f"Error reading file: {e}")
        return

    try:
        detected_lang = detect(content)
    except:
        detected_lang = "auto"

    # Target lang auto-switch
    target_lang = "en" if detected_lang != "en" else "bn"

    # Translation logic
    lines = content.splitlines()
    translated_lines = []
    for line in lines:
        if line.strip().isdigit() or "-->" in line or not line.strip():
            translated_lines.append(line)
        else:
            try:
                translated = GoogleTranslator(source='auto', target=target_lang).translate(line)
                translated_lines.append(translated)
            except Exception:
                translated_lines.append(line)

    translated_text = "\n".join(translated_lines)
    output_path = f"temp/translated_{filename}"

    async with aiofiles.open(output_path, mode="w", encoding="utf-8") as f:
        await f.write(translated_text)

    await update.message.reply_document(
        document=InputFile(output_path),
        filename=f"translated_{filename}",
        caption=f"Translated from `{detected_lang}` to `{target_lang}`"
    )

    # Cleanup
    os.remove(file_path)
    os.remove(output_path)

# Bot Runner
def main():
    app_tg = ApplicationBuilder().token(TOKEN).build()
    app_tg.add_handler(CommandHandler("start", start))
    app_tg.add_handler(MessageHandler(filters.Document.ALL, handle_subtitle))

    threading.Thread(target=start_flask).start()
    app_tg.run_polling()

if __name__ == "__main__":
    main()
