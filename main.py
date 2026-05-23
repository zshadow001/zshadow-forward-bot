import os
import json
import re
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

# STORE LAST SEARCH
last_query = None
last_user_id = None

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
       🕵️ 𝚉 𝚂𝙷𝙰𝙳𝙾𝚆 𝙸𝙽𝚃𝙴𝙻 🕵️
╚════════════════════════════╝

⚡ Welcome To ZShadow Intel System

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

    global last_query
    global last_user_id

    query = event.pattern_match.group(1)

    last_query = query
    last_user_id = event.sender_id

    await event.reply(
        "🔍 Searching..."
    )

    # SEND TO OFFICIAL GROUP
    await user.send_message(
        GROUP_ID,
        f"/num {query}"
    )

# LISTEN GROUP
@user.on(events.NewMessage(chats=GROUP_ID))
async def group_listener(event):

    global last_query
    global last_user_id

    text = event.raw_text

    # IGNORE EMPTY
    if not text:
        return

    # IGNORE COMMANDS
    if text.startswith("/"):
        return

    # ONLY OUR SEARCH
    if not last_query:
        return

    if last_query not in text:
        return

    # ONLY VALID RESULT
    if (
        "TARGET:" not in text
        or '"result"' not in text
        or '"data"' not in text
    ):
        return

    try:

        json_match = re.search(
            r'(\{.*\})',
            text,
            re.DOTALL
        )

        if not json_match:
            return

        parsed = json.loads(
            json_match.group(1)
        )

        records = parsed["result"]["data"]

        if not records:
            return

        result_text = """
╔════════════════════╗
     🕵️ Z SHADOW INTEL
╚════════════════════╝
"""

        count = 1

        for item in records:

            result_text += f"""

🔍 RECORD {count}
━━━━━━━━━━━━━━━━━━
👤 NAME     ➤ {item.get("NAME", "N/A")}
📞 MOBILE   ➤ {item.get("MOBILE", "N/A")}
🌐 CIRCLE   ➤ {item.get("circle", "N/A")}
🏠 ADDRESS  ➤ {item.get("ADDRESS", "N/A")}
🆔 ID       ➤ {item.get("id", "N/A")}
📧 EMAIL    ➤ {item.get("email", "N/A")}
"""

            count += 1

        result_text += """

━━━━━━━━━━━━━━━━━━
⚡ Powered By ZShadow
"""

        # SEND RESULT TO USER
        await bot.send_message(
            last_user_id,
            result_text
        )

        # RESET
        last_query = None
        last_user_id = None

    except Exception as e:

        print("PARSE ERROR:", e)

# FLASK WEB SERVER
app = Flask(__name__)

@app.route("/")
def home():
    return "ZShadow Intel Running 😎"

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

    print("ZShadow Intel Running 😎")

    await bot.run_until_disconnected()

with bot:

    bot.loop.run_until_complete(
        main()
    )