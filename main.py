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
            url=f"https://t.me/{CHANNEL_USERNAME.replace('@','')}"
        )
        markup.add(btn)

        bot.reply_to(
            message,
            "📢 تکایە سەرەتا Join ـی چەناڵ بکە",
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
✅ X (Twitter)

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
            url=f"https://t.me/{CHANNEL_USERNAME.replace('@','')}"
        )

        markup.add(btn)

        bot.reply_to(
            message,
            "📢 بۆ بەکارهێنانی بۆت، Join ـی چەناڵ بکە",
            reply_markup=markup
        )
        return

    url = message.text.strip()

    wait = bot.reply_to(message, "⏳ چاوەڕێبە...")

    try:

        # Fix TikTok short links
        if "vt.tiktok.com" in url:
            response = requests.get(
                url,
                headers={"User-Agent": "Mozilla/5.0"},
                allow_redirects=True,
                timeout=10
            )
            url = response.url

        ydl_opts = {
            "format": "bestvideo+bestaudio/best",
            "merge_output_format": "mp4",
            "outtmpl": "%(id)s.%(ext)s",
            "quiet": True,
            "noplaylist": True,
            "nocheckcertificate": True,
            "extractor_retries": 10,
            "socket_timeout": 30,
            "http_headers": {
                "User-Agent": "Mozilla/5.0"
            },
            # ئەگەر cookies.txt هەبێت خۆکارانە بەکاری دەهێنێت
            "cookiefile": "cookies.txt" if os.path.exists("cookies.txt") else None,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        bot.delete_message(message.chat.id, wait.message_id)

        with open(filename, "rb") as video:
            bot.send_video(message.chat.id, video)

        if os.path.exists(filename):
            os.remove(filename)

    except Exception as e:
        bot.edit_message_text(
            f"❌ هەڵە:\n\n{str(e)}",
            message.chat.id,
            wait.message_id
        )

# =========================
# Run Bot
# =========================
print("Bot Running...")

while True:
    try:
        bot.infinity_polling(timeout=20, long_polling_timeout=10)
    except Exception as e:
        print(e)
        time.sleep(5)
