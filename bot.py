import os
import uuid
import aiofiles
import logging
from telegram import (
    Update, InlineKeyboardMarkup, InlineKeyboardButton, InputFile
)
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler,
    ContextTypes, filters
)
from deep_translator import GoogleTranslator

# Setup Logging
logging.basicConfig(level=logging.INFO)

# Paths & Memory
os.makedirs("temp", exist_ok=True)
user_data = {}
SUPPORTED_FORMATS = ['.srt', '.vtt', '.ass', '.sub', '.txt']

LANGUAGES = {
    "en": "🇺🇸 English", "bn": "🇧🇩 Bangla", "hi": "🇮🇳 Hindi",
    "fr": "🇫🇷 French", "ar": "🇸🇦 Arabic", "es": "🇪🇸 Spanish",
    "ru": "🇷🇺 Russian", "zh": "🇨🇳 Chinese"
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Send a subtitle file (SRT/VTT/ASS/SUB/TXT) to translate.")

async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    doc = update.message.document
    file_name = doc.file_name
    file_ext = os.path.splitext(file_name)[1].lower()

    if file_ext not in SUPPORTED_FORMATS:
        await update.message.reply_text("Unsupported format! Supported: SRT, VTT, ASS, SUB, TXT")
        return

    uid = str(uuid.uuid4())
    file_path = f"temp/{uid}_{file_name}"
    await doc.get_file().download_to_drive(file_path)

    user_data[update.effective_chat.id] = {
        "file": file_path,
        "ext": file_ext,
        "name": file_name
    }

    # Language Buttons
    buttons = [[InlineKeyboardButton(name, callback_data=f"lang_{code}")]
               for code, name in LANGUAGES.items()]
    await update.message.reply_text(
        "Choose target language:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

async def handle_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    chat_id = query.message.chat_id
    user = user_data.get(chat_id)

    if not user:
        await query.edit_message_text("Please send a subtitle file again.")
        return

    lang_code = query.data.split("_")[1]
    await query.edit_message_text(f"Translating to {LANGUAGES[lang_code]}...")

    # Read original file
    async with aiofiles.open(user["file"], "r", encoding="utf-8", errors="ignore") as f:
        original = await f.readlines()

    total = len(original)
    translated = []
    progress_msg = await context.bot.send_message(chat_id=chat_id, text="Progress: 0%")

    # Translate each line
    for i, line in enumerate(original):
        if '-->' in line or line.strip().isdigit() or line.strip() == "":
            translated.append(line)
        else:
            try:
                translated_text = GoogleTranslator(source='auto', target=lang_code).translate(line.strip())
                translated.append(translated_text + "\n")
            except Exception:
                translated.append(line)

        if i % 10 == 0 or i == total - 1:
            percent = int((i / total) * 100)
            await progress_msg.edit_text(f"Progress: {percent}% ({i}/{total})")

    # Save translated file
    output_path = f"temp/{uuid.uuid4()}_translated{user['ext']}"
    async with aiofiles.open(output_path, "w", encoding="utf-8") as f:
        await f.writelines(translated)

    # Send File
    await context.bot.send_document(
        chat_id=chat_id,
        document=InputFile(output_path),
        filename=f"Translated_{user['name']}",
        caption=f"Translation done to {LANGUAGES[lang_code]}"
    )

    # Cleanup
    os.remove(user["file"])
    os.remove(output_path)
    del user_data[chat_id]

# App Start
def main():
    token = os.getenv("BOT_TOKEN")
    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_file))
    app.add_handler(CallbackQueryHandler(handle_language))
    app.run_polling()

if __name__ == "__main__":
    main()
