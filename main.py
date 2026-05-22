import os
import re
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
📡 TXT Auto Parser
⚡ Fast Responses
🖥️ Auto Forward System

📌 Available Commands

/num ➜ Search Number

⚡ Powered By ZShadow
"""

    await event.reply(msg)

# /num command
@bot.on(events.NewMessage(pattern=r"/num (.+)"))
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

    # ONLY TXT FILE
    if not event.file:
        return

    if not str(event.file.name).endswith(".txt"):
        return

    # DOWNLOAD TXT
    file_path = await event.download_media()

    # READ TXT
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:

        data = f.read()

    # FORMAT RESULT
    formatted = f"""
🖥️ NEW SESSION CAPTURED 🖥️

{data}

⚡ Powered By ZShadow
"""

    # SEND TO LAST USER
    if pending_requests:

        last_user = list(
            pending_requests.keys()
        )[-1]

        await bot.send_message(
            last_user,
            formatted
        )

    # DELETE FILE
    os.remove(file_path)

# START EVERYTHING
async def main():

    await start_user()

    print("ZShadow Bot Running 😎")

    await bot.run_until_disconnected()

with bot:

    bot.loop.run_until_complete(
        main()
    )