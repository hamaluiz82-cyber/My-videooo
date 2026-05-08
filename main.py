import telebot
import yt_dlp
import os
import requests
import time

def load_users():
    try:
        with open("users.txt", "r") as f:
            return set(f.read().splitlines())
    except:
        return set()

users = load_users()

TOKEN = os.getenv("TOKEN")

bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def start(message):
user_id = str(message.from_user.id)

    if user_id not in users:
        users.add(user_id)

        with open("users.txt", "a") as f:
            f.write(user_id + "\n")

    bot.reply_to(
        message,
        f"👋 Welcome\n👥 Users: {len(users)}"
    text = """
👋 بەخێربێیت بۆ بۆتی داونلۆدی ڤیدیۆ

📥 پشتگیری:
✅ TikTok
✅ Facebook
✅ Instagram
✅ YouTube

🔗 تەنها لینک بنێرە
"""

    bot.reply_to(message, text)

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
            'format': 'best',
            'outtmpl': '%(title)s.%(ext)s',
            'quiet': True,
            'noplaylist': True
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:

            info = ydl.extract_info(url, download=True)

            filename = ydl.prepare_filename(info)

        with open(filename, 'rb') as video:

            bot.send_video(message.chat.id, open(filename, 'rb'))

os.remove(filename)

    except Exception as e:

        bot.reply_to(message, f"❌ هەڵە:\n{e}")

print("Bot Running...")

while True:
    try:
        bot.infinity_polling(timeout=10, long_polling_timeout=5)
    except Exception as e:
        print(f"Error: {e}")
        time.sleep(5)
