import telebot
import yt_dlp
import os
import requests

TOKEN = "8659428362:AAGCTsgpgstiPG8kJRToGI2uidKh2lRdIhg"
bot = telebot.TeleBot(TOKEN)

# =========================
# Load Users
# =========================

users = set()

if os.path.exists("users.txt"):
    with open("users.txt", "r") as f:
        users = set(f.read().splitlines())

# =========================
# Start Command
# =========================

@bot.message_handler(commands=['start'])
def start(message):

    user_id = str(message.chat.id)

    if user_id not in users:

        users.add(user_id)

        with open("users.txt", "a") as f:
            f.write(user_id + "\n")

    text = f"""
👋 بەخێربێیت بۆ بۆتی داونلۆدی ڤیدیۆ

📥 پشتگیری:
✅ TikTok
✅ Facebook
✅ Instagram
✅ YouTube

👥 ژمارەی بەکارهێنەران: {len(users)}

🔗 تەنها لینک بنێرە
"""

    bot.reply_to(message, text)

# =========================
# Download Video
# =========================

@bot.message_handler(func=lambda message: True)
def download_video(message):

    url = message.text

    bot.reply_to(message, "⏳ چاوەڕێبە...")

    try:

        # TikTok short link fix
        if "vt.tiktok.com" in url:

            headers = {
                "User-Agent": "Mozilla/5.0"
            }

            r = requests.get(url, headers=headers, allow_redirects=True)

            url = r.url

        ydl_opts = {
            'format': 'mp4[height<=720]',
            'outtmpl': '%(id)s.%(ext)s',
            'quiet': True,
            'noplaylist': True
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:

            info = ydl.extract_info(url, download=True)

            filename = ydl.prepare_filename(info)

        with open(filename, 'rb') as video:

            bot.send_video(message.chat.id, video)

        os.remove(filename)

    except Exception as e:

        bot.reply_to(message, f"❌ هەڵە:\n{e}")

print("Bot Running...")

bot.infinity_polling()
