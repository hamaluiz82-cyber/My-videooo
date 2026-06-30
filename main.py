import os
import time
import uuid
import requests
import telebot
import yt_dlp

# =========================
# Config
# =========================
TOKEN = os.getenv("TOKEN")
CHANNEL_USERNAME = os.getenv("CHANNEL_USERNAME", "@myviideo")
USERS_FILE = "users.txt"

if not TOKEN:
    raise RuntimeError("TOKEN environment variable is missing")

bot = telebot.TeleBot(TOKEN, parse_mode=None)

# =========================
# Users
# =========================
def load_users():
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return set(x.strip() for x in f.readlines() if x.strip())
    except FileNotFoundError:
        return set()

users = load_users()


def save_user(user_id):
    user_id = str(user_id)
    if user_id not in users:
        users.add(user_id)
        with open(USERS_FILE, "a", encoding="utf-8") as f:
            f.write(user_id + "\n")

# =========================
# Channel Join Check
# =========================
def is_joined(user_id):
    try:
        member = bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ["member", "administrator", "creator"]
    except Exception:
        return False


def join_markup():
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(
        telebot.types.InlineKeyboardButton(
            "ð¢ Join Channel",
            url=f"https://t.me/{CHANNEL_USERNAME.replace('@', '')}"
        )
    )
    return markup

# =========================
# URL Helpers
# =========================
def fix_url(url):
    url = url.strip()
    if "vt.tiktok.com" in url or "vm.tiktok.com" in url:
        try:
            r = requests.get(
                url,
                headers={"User-Agent": "Mozilla/5.0"},
                allow_redirects=True,
                timeout=20
            )
            return r.url
        except Exception:
            return url
    return url


def is_tiktok_url(url):
    return "tiktok.com" in url.lower()

# =========================
# TikTok fallback via tikwm
# =========================
def download_tiktok_fallback(url):
    api = "https://www.tikwm.com/api/"
    r = requests.get(
        api,
        params={"url": url},
        headers={"User-Agent": "Mozilla/5.0"},
        timeout=30
    )
    r.raise_for_status()
    data = r.json()

    video_url = data.get("data", {}).get("play") or data.get("data", {}).get("wmplay")
    if not video_url:
        raise Exception("TikTok fallback failed: video link not found")

    filename = f"{uuid.uuid4()}.mp4"
    v = requests.get(
        video_url,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Referer": "https://www.tiktok.com/"
        },
        timeout=90,
        stream=True
    )
    v.raise_for_status()

    with open(filename, "wb") as f:
        for chunk in v.iter_content(chunk_size=1024 * 1024):
            if chunk:
                f.write(chunk)

    if os.path.getsize(filename) < 1024:
        raise Exception("TikTok fallback failed: downloaded file is too small")

    return filename

# =========================
# yt-dlp downloader
# =========================
def download_with_ytdlp(url):
    file_id = str(uuid.uuid4())

    ydl_opts = {
        "format": "best[ext=mp4]/best",
        "outtmpl": f"{file_id}.%(ext)s",
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "nocheckcertificate": True,
        "extractor_retries": 10,
        "retries": 10,
        "fragment_retries": 10,
        "socket_timeout": 30,
        "merge_output_format": "mp4",
        "extractor_args": {
            "tiktok": {
                "api_hostname": ["api16-normal-c-useast1a.tiktokv.com"]
            }
        },
        "http_headers": {
            "User-Agent": (
                "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
                "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 "
                "Mobile/15E148 Safari/604.1"
            ),
            "Referer": "https://www.tiktok.com/",
            "Accept-Language": "en-US,en;q=0.9"
        }
    }

    if os.path.exists("cookies.txt"):
        ydl_opts["cookiefile"] = "cookies.txt"

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)

    if not os.path.exists(filename):
        # Sometimes yt-dlp changes extension after merge
        base = filename.rsplit(".", 1)[0]
        for ext in ["mp4", "mkv", "webm", "mov"]:
            possible = base + "." + ext
            if os.path.exists(possible):
                return possible

    return filename


def download_video(url):
    url = fix_url(url)

    try:
        return download_with_ytdlp(url)
    except Exception as e:
        # TikTok sometimes gives: Video not available, status code 0
        if is_tiktok_url(url):
            return download_tiktok_fallback(url)
        raise e

# =========================
# Messages
# =========================
@bot.message_handler(commands=["start"])
def start(message):
    if not is_joined(message.from_user.id):
        bot.reply_to(
            message,
            "ð¢ ØªÚ©Ø§ÛÛ Ø³ÛØ±ÛØªØ§ Join ÙÛ ÚÛÙØ§Úµ Ø¨Ú©Û",
            reply_markup=join_markup()
        )
        return

    save_user(message.from_user.id)

    bot.reply_to(message, f"""
ð Ø¨ÛØ®ÛØ±Ø¨ÛÛØª Ø¨Û Ø¨ÛØªÛ Ø¯Ø§ÙÙÙÛØ¯Û Ú¤ÛØ¯ÛÛ

ð¥ Users: {len(users)}

ð¥ Ù¾Ø´ØªÚ¯ÛØ±Û:
â TikTok
â Instagram
â Facebook
â YouTube
â X / Twitter

ð ØªÛÙÙØ§ ÙÛÙÚ© Ø¨ÙÛØ±Û
""")


@bot.message_handler(func=lambda message: True)
def handle_link(message):
    if not is_joined(message.from_user.id):
        bot.reply_to(
            message,
            "ð¢ Ø¨Û Ø¨ÛÚ©Ø§Ø±ÙÛÙØ§ÙÛ Ø¨ÛØªØ Join ÙÛ ÚÛÙØ§Úµ Ø¨Ú©Û",
            reply_markup=join_markup()
        )
        return

    save_user(message.from_user.id)

    url = (message.text or "").strip()
    if not url.startswith("http"):
        bot.reply_to(message, "â ØªÚ©Ø§ÛÛ ÙÛÙÚ©ÛÚ©Û Ø¯Ø±ÙØ³Øª Ø¨ÙÛØ±Û")
        return

    wait = bot.reply_to(message, "â³ ÚØ§ÙÛÚÛØ¨ÛØ Ú¤ÛØ¯ÛÛÚ©Û Ø¯Ø§Ø¯ÛÚ¯ÛØ±ÛØª...")
    filename = None

    try:
        filename = download_video(url)

        try:
            bot.delete_message(message.chat.id, wait.message_id)
        except Exception:
            pass

        with open(filename, "rb") as video:
            bot.send_video(
                message.chat.id,
                video,
                caption="â Ø¯Ø§ÙÙÙÛØ¯ Ú©Ø±Ø§",
                supports_streaming=True
            )

    except Exception as e:
        error_text = str(e)

        if "instagram" in error_text.lower() or "facebook" in error_text.lower():
            msg = (
                "â Ø¦ÛÙ ÙÛÙÚ©Û Ù¾ÛÙÛØ³ØªÛ Ø¨Û cookies.txt ÙÛÛÛ\n\n"
                "cookies.txt ÙÙÛ Ø¨Ú©Û Ù ÙÛ GitHub Ø¯Ø§Ø¨ÙÛ.\n\n"
                f"{error_text}"
            )
        elif "tiktok" in error_text.lower() or "status code 0" in error_text.lower():
            msg = (
                "â ÙÛÚµÛÛ TikTok ÚÙÙÛØ¯Ø§\n\n"
                "Ø¦ÛÙ ÚØ§Ø±ÛØ³ÛØ±Ø§ÙÛ Ø²ÛØ§Ø¯ Ú©Ø±Ø§ÙÙ: yt-dlp + fallback.\n"
                "Ø¦ÛÚ¯ÛØ± ÙÛØ´ØªØ§ Ú©Ø§Ø± ÙÛÚ©Ø±Ø¯Ø Ø¦ÛÙ Ú¤ÛØ¯ÛÛÛÛ ÙÛØ³ÛØ± Ø³ÛØ±Ú¤ÛØ±Û TikTok Ø¨ÛØ±Ø¯ÛØ³Øª ÙÛÛÛ ÛØ§Ù private/region blocked ÙÛ.\n\n"
                f"{error_text}"
            )
        else:
            msg = f"â ÙÛÚµÛ ÚÙÙÛØ¯Ø§:\n\n{error_text}"

        try:
            bot.edit_message_text(msg, message.chat.id, wait.message_id)
        except Exception:
            bot.reply_to(message, msg)

    finally:
        if filename and os.path.exists(filename):
            try:
                os.remove(filename)
            except Exception:
                pass

# =========================
# Run bot
# =========================
print("Bot Running...")

while True:
    try:
        bot.infinity_polling(timeout=20, long_polling_timeout=10)
    except Exception as e:
        print("Polling Error:", e)
        time.sleep(5)
