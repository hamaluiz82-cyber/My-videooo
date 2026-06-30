import telebot
import yt_dlp
import os
import requests
import time
import uuid

TOKEN = os.getenv("TOKEN")
CHANNEL_USERNAME = "@myviideo"

bot = telebot.TeleBot(TOKEN)

def is_joined(user_id):
    try:
        member = bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False

def load_users():
    try:
        with open("users.txt", "r") as f:
            return set(f.read().splitlines())
    except:
        return set()

users = load_users()

def fix_url(url):
    if "vt.tiktok.com" in url or "vm.tiktok.com" in url:
        r = requests.get(
            url,
            headers={"User-Agent": "Mozilla/5.0"},
            allow_redirects=True,
            timeout=15
        )
        return r.url
    return url

def download_with_ytdlp(url):
    file_id = str(uuid.uuid4())

    ydl_opts = {
        "format": "best[ext=mp4]/best",
        "outtmpl": f"{file_id}.%(ext)s",
        "quiet": True,
        "noplaylist": True,
        "nocheckcertificate": True,
        "extractor_retries": 10,
        "retries": 10,
        "fragment_retries": 10,
        "socket_timeout": 30,
        "http_headers": {
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15"
        }
    }

    if os.path.exists("cookies.txt"):
        ydl_opts["cookiefile"] = "cookies.txt"

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)

    return filename

@bot.message_handler(commands=["start"])
def start(message):
    if not is_joined(message.from_user.id):
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(
            telebot.types.InlineKeyboardButton(
                "📢 Join Channel",
                url=f"https://t.me/{CHANNEL_USERNAME.replace('@','')}"
            )
        )
        bot.reply_to(message, "📢 تکایە سەرەتا Join ـی چەناڵ بکە", reply_markup=markup)
        return

    user_id = str(message.from_user.id)

    if user_id not in users:
        users.add(user_id)
        with open("users.txt", "a") as f:
            f.write(user_id + "\n")

    bot.reply_to(message, f"""
👋 بەخێربێیت بۆ بۆتی داونلۆدی ڤیدیۆ

👥 Users: {len(users)}

📥 پشتگیری:
✅ TikTok
✅ Instagram
✅ Facebook
✅ YouTube
✅ X / Twitter

🔗 تەنها لینک بنێرە
""")

@bot.message_handler(func=lambda message: True)
def handle_link(message):
    if not is_joined(message.from_user.id):
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(
            telebot.types.InlineKeyboardButton(
                "📢 Join Channel",
                url=f"https://t.me/{CHANNEL_USERNAME.replace('@','')}"
            )
        )
        bot.reply_to(message, "📢 بۆ بەکارهێنانی بۆت، Join ـی چەناڵ بکە", reply_markup=markup)
        return

    url = message.text.strip()

    if not url.startswith("http"):
        bot.reply_to(message, "❌ تکایە لینکێکی دروست بنێرە")
        return

    wait = bot.reply_to(message, "⏳ چاوەڕێبە، ڤیدیۆکە دادەگیرێت...")

    filename = None

    try:
        url = fix_url(url)
        filename = download_with_ytdlp(url)

        try:
            bot.delete_message(message.chat.id, wait.message_id)
        except:
            pass

        with open(filename, "rb") as video:
            bot.send_video(
                message.chat.id,
                video,
                caption="✅ داونلۆد کرا"
            )

    except Exception as e:
        try:
            bot.edit_message_text(
                "❌ هەڵە ڕوویدا\n\n"
                "ئەگەر لینکەکە Instagram/Facebook ـە، پێویستی بە cookies.txt هەیە.\n\n"
                f"{str(e)}",
                message.chat.id,
                wait.message_id
            )
        except:
            bot.reply_to(message, f"❌ هەڵە:\n{str(e)}")

    finally:
        if filename and os.path.exists(filename):
            os.remove(filename)

print("Bot Running...")

while True:
    try:
        bot.infinity_polling(timeout=20, long_polling_timeout=10)
    except Exception as e:
        print("Polling Error:", e)
        time.sleep(5)
