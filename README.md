# Advanced Telegram Subtitle Translator Bot

A smart, powerful, and beautifully designed Telegram bot to translate `.srt`, `.vtt`, `.ass` subtitle files into multiple languages using Google Translate.

---

## Features

- Supports `.srt`, `.vtt`, and `.ass` files
- Auto-detects language
- Translates to 15+ languages
- Fast translation using Google Translate
- Clean and stylish interface
- Sends translated subtitle with proper filename
- Temporary file cleanup
- Flask server for uptime
- Dockerfile + Procfile included for deployment
- Credits & Channel links embedded

---

## Preview

1. Send a subtitle file (e.g., `movie.srt`)
2. Bot detects the file and asks for target language
3. You select e.g. `বাংলা (bn)`
4. Bot returns `movie_translated_bn.srt` with translated text

---

## Deploy Guide

### 1. Telegram Bot Setup

- Go to [BotFather](https://t.me/BotFather)
- Create a bot, get your **BOT_TOKEN**

---

### 2. Run Locally

```bash
git clone https://github.com/your-username/subtitle-translator-bot.git
cd subtitle-translator-bot
pip install -r requirements.txt
export BOT_TOKEN=your_token_here
python bot.py
