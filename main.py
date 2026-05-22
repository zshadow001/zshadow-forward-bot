import os
from flask import Flask
from threading import Thread
from telethon import TelegramClient, events
from telethon.sessions import StringSession

# ENV VARIABLES
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
STRING_SESSION = os.getenv("STRING_SESSION")
GROUP_ID = int(os.getenv("GROUP_ID"))

# BOT CLIENT
bot = TelegramClient(
    "bot",
    API_ID,
    API_HASH
).start(bot_token=BOT_TOKEN)

# USER CLIENT
user = TelegramClient(
    StringSession(STRING_SESSION),
    API_ID,
    API_HASH
)

# STORE REQUESTS
pending_requests = {}

# START USER CLIENT
async def start_user():

    await user.start()

# /start
@bot.on(events.NewMessage(pattern="/start"))
async def start(event):

    first = event.sender.first_name or ""
    last = event.sender.last_name or ""

    msg = f"""
👋 Hello {first} {last}

╔════════════════════════════╗
       🖥️ 𝚉 𝚂𝙷𝙰𝙳𝙾𝚆 𝚃𝚁𝙰𝙲𝙴 🖥️
╚════════════════════════════╝

⚡ Welcome to the ultimate tracking system

✨ Features:
🔗 Number Lookup
⚡ Fast Responses
🖥️ Auto Forward System

📌 Available Commands

/num ➜ Search Number

⚡ Powered By ZShadow
"""

    await event.reply(msg)

# /num command
@bot.on(
    events.NewMessage(
        pattern=r"/num (.+)",
        func=lambda e: e.is_private
    )
)
async def num(event):

    query = event.pattern_match.group(1)

    user_id = event.sender_id

    pending_requests[user_id] = query

    await event.reply(
        "🔍 Searching..."
    )

    # SEND TO GROUP USING USER ACCOUNT
    await user.send_message(
        GROUP_ID,
        f"/num {query}"
    )

# LISTEN GROUP
@user.on(events.NewMessage(chats=GROUP_ID))
async def group_listener(event):

    text = event.raw_text

    # IGNORE COMMANDS
    if text.startswith("/"):
        return

    # ONLY TARGET RESULTS
    if "TARGET:" not in text:
        return

    # SEND RESULT
    if pending_requests:

        last_user = list(
            pending_requests.keys()
        )[-1]

        formatted = f"""
🖥️ NEW SESSION CAPTURED 🖥️

{text}

⚡ Powered By ZShadow
"""

        await bot.send_message(
            last_user,
            formatted
        )

# FLASK WEB SERVER
app = Flask(__name__)

@app.route("/")
def home():
    return "ZShadow Bot Running 😎"

def run_web():

    port = int(
        os.environ.get("PORT", 10000)
    )

    app.run(
        host="0.0.0.0",
        port=port
    )

Thread(target=run_web).start()

# START EVERYTHING
async def main():

    await start_user()

    print("ZShadow Bot Running 😎")

    await bot.run_until_disconnected()

with bot:

    bot.loop.run_until_complete(
        main()
    )