import telebot
import yt_dlp
import os
import requests
import time

# =========================
# Load Users
# =========================
def load_users():
    try:
        with open("users.txt", "r") as f:
            return set(f.read().splitlines())
    except:
        return set()

users = load_users()

# =========================
# Config
# =========================
TOKEN = os.getenv("TOKEN")
CHANNEL_USERNAME = "@myviideo"

bot = telebot.TeleBot(TOKEN)

# =========================
# Check Channel Join
# =========================
def is_joined(user_id):
    try:
        member = bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False

# =========================
# Start Command
# =========================
@bot.message_handler(commands=["start"])
def start(message):

    if not is_joined(message.from_user.id):

        markup = telebot.types.InlineKeyboardMarkup()

        btn = telebot.types.InlineKeyboardButton(
            "📢 Join Channel",
            url=f"https://t.me/{CHANNEL_USERNAME.replace('@', '')}"
        )

        markup.add(btn)

        bot.reply_to(
            message,
            "📢 تکایە سەرەتا join ـی چەناڵ بکە",
            reply_markup=markup
        )
        return

    user_id = str(message.from_user.id)

    if user_id not in users:
        users.add(user_id)

        with open("users.txt", "a") as f:
            f.write(user_id + "\n")

    text = f"""
👋 بەخێربێیت بۆ بۆتی داونلۆدی ڤیدیۆ

👥 Users: {len(users)}

📥 پشتگیری:
✅ TikTok
✅ Facebook
✅ Instagram
✅ YouTube

🚀 No Watermark
⚡ Fast Download

🔗 تەنها لینک بنێرە
"""

    bot.reply_to(message, text)

# =========================
# Download Video
# =========================
@bot.message_handler(func=lambda message: True)
def download_video(message):

    if not is_joined(message.from_user.id):

        markup = telebot.types.InlineKeyboardMarkup()

        btn = telebot.types.InlineKeyboardButton(
            "📢 Join Channel",
            url=f"https://t.me/{CHANNEL_USERNAME.replace('@', '')}"
        )

        markup.add(btn)

        bot.reply_to(
            message,
            "📢 بۆ بەکارهێنانی بۆت، join ـی چەناڵ بکە",
            reply_markup=markup
        )
        return

    url = message.text.strip()

    bot.reply_to(message, "⏳ چاوەڕێبە...")

    try:

        # TikTok Short Link Fix
        if "vt.tiktok.com" in url:
            headers = {
                "User-Agent": "Mozilla/5.0"
            }

            response = requests.get(
                url,
                headers=headers,
                allow_redirects=True,
                timeout=10
            )

            url = response.url

        ydl_opts = {
            "format": "best",
            "outtmpl": "video.%(ext)s",
            "quiet": True,
            "noplaylist": True,
            "nocheckcertificate": True,
            "extractor_retries": 5,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        with open(filename, "rb") as video:
            bot.send_video(message.chat.id, video)

        if os.path.exists(filename):
            os.remove(filename)

    except Exception as e:
        bot.reply_to(message, f"❌ هەڵە:\n{str(e)}")

# =========================
# Run Bot
# =========================
print("Bot Running...")

while True:
    try:
        bot.infinity_polling(
            timeout=10,
            long_polling_timeout=5
        )
    except Exception as e:
        print(f"Error: {e}")
        time.sleep(5)
