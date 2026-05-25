import os
import json
import re
import asyncio
from flask import Flask
from threading import Thread
from telethon import TelegramClient, events
from telethon.sessions import StringSession

# ENV
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
STRING_SESSION = os.getenv("STRING_SESSION")
GROUP_ID = int(os.getenv("GROUP_ID"))

# CLIENTS
bot = TelegramClient(
    "bot",
    API_ID,
    API_HASH
)

user = TelegramClient(
    StringSession(STRING_SESSION),
    API_ID,
    API_HASH
)

# AUTO DELETE
async def auto_delete(msg, seconds):

    await asyncio.sleep(seconds)

    try:
        await msg.delete()
    except:
        pass

# STORE
last_query = None
last_chat_id = None
last_text = None

# START CLIENTS
async def start_clients():

    await bot.start(bot_token=BOT_TOKEN)
    await user.start()

# /start
@bot.on(events.NewMessage(pattern="/start"))
async def start(event):

    name = event.sender.first_name or "User"

    text = f"""
👋 Hello {name}

╔════════════════════════════╗
       🕵️ Z SHADOW INTEL 🕵️
╚════════════════════════════╝

⚡ Welcome To ZShadow Intel

📌 Commands

/num ➜ Search Number

⚡ Powered By ZShadow
"""

    await event.reply(text)

# /num
@bot.on(events.NewMessage(pattern=r"/num (.+)"))
async def num(event):

    global last_query
    global last_chat_id

    # IGNORE OFFICIAL GROUP
    if event.chat_id == GROUP_ID:
        return

    # IGNORE BOT SELF
    if event.out:
        return

    query = event.pattern_match.group(1).strip()

    # DUPLICATE BLOCK
    if (
        last_query == query
        and last_chat_id == event.chat_id
    ):
        return

    # SAVE
    last_query = query
    last_chat_id = event.chat_id

    # SEARCHING
search_msg = await event.reply(
    "🔍 Searching..."
)
    # SEND TO OFFICIAL GROUP
    await user.send_message(
        GROUP_ID,
        f"/num {query}"
    )

# GROUP LISTENER
@user.on(events.NewMessage(chats=GROUP_ID))
async def group_listener(event):

    global last_query
    global last_chat_id
    global last_text

    text = event.raw_text

    # EMPTY
    if not text:
        return

    # DUPLICATE BLOCK
    if text == last_text:
        return

    last_text = text

    # IGNORE COMMANDS
    if text.startswith("/"):
        return

    # NO ACTIVE SEARCH
    if not last_query:
        return

    # ONLY OUR RESULT
    if last_query not in text:
        return

    # INVALID RESULT
    if (
        "TARGET:" not in text
        or '"result"' not in text
    ):

        await bot.send_message(
            last_chat_id,
            """
╔════════════════════╗
     🕵️ Z SHADOW INTEL
╚════════════════════╝

⚠ SEARCH FAILED

❌ No matching records found
📡 Server returned empty response

━━━━━━━━━━━━━━━━━━
⚡ Powered By ZShadow
"""
        )

        # RESET
        last_query = None
        last_chat_id = None

        return

    try:

        # EXTRACT JSON
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

        # SUPPORT BOTH TYPES
        records = parsed.get("result", {}).get("data")

        if not records:
            records = parsed.get("result")

        if not records:

            await bot.send_message(
                last_chat_id,
                """
╔════════════════════╗
     🕵️ Z SHADOW INTEL
╚════════════════════╝

⚠ SEARCH FAILED

❌ No matching records found
📡 Server returned empty response

━━━━━━━━━━━━━━━━━━
⚡ Powered By ZShadow
"""
            )

            return

        result = """
╔════════════════════╗
     🕵️ Z SHADOW INTEL
╚════════════════════╝
"""

        for i, item in enumerate(records, start=1):

            result += f"""

🔍 RECORD {i}
━━━━━━━━━━━━━━━━━━
👤 NAME ➤ {item.get("NAME", "N/A")}
📞 MOBILE ➤ {item.get("MOBILE", "N/A")}
🌐 CIRCLE ➤ {item.get("circle", "N/A")}
🏠 ADDRESS ➤ {item.get("ADDRESS", "N/A")}
🆔 ID ➤ {item.get("id", "N/A")}
📧 EMAIL ➤ {item.get("email", "N/A")}
"""

result += """

Powered By Zshadow 😎

━━━━━━━━━━━━━━━━━━
⚠ For safety reasons,
this message will auto delete in 1 minute 😎
"""

# SEND RESULT
result_msg = await bot.send_message(
    last_chat_id,
    result
)

# DELETE SEARCH MSG
try:
    await search_msg.delete()
except:
    pass

# AUTO DELETE RESULT
asyncio.create_task(
    auto_delete(result_msg, 60)
)

        # RESET
        last_query = None
        last_chat_id = None

    except Exception as e:

        print("PARSE ERROR:", e)

        await bot.send_message(
            last_chat_id,
            """
╔════════════════════╗
     🕵️ Z SHADOW INTEL
╚════════════════════╝

⚠ SEARCH FAILED

❌ Unable to parse server response
📡 Invalid or broken data received

━━━━━━━━━━━━━━━━━━
⚡ Powered By ZShadow
"""
        )

        # RESET
        last_query = None
        last_chat_id = None

# FLASK
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

# MAIN
async def main():

    await start_clients()

    print("ZShadow Intel Running 😎")

    await asyncio.gather(
        bot.run_until_disconnected(),
        user.run_until_disconnected()
    )

asyncio.run(main())