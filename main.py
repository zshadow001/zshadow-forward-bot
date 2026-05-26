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
bot = TelegramClient("bot", API_ID, API_HASH)
user = TelegramClient(StringSession(STRING_SESSION), API_ID, API_HASH)

# STORAGE
active_searches = {}
message_parts = {}
last_text = None

# AUTO DELETE
async def auto_delete(msg, seconds):
    await asyncio.sleep(seconds)
    try:
        await msg.delete()
    except:
        pass

# START CLIENTS
async def start_clients():
    await bot.start(bot_token=BOT_TOKEN)
    await user.start()

# START COMMAND
@bot.on(events.NewMessage(pattern="/start"))
async def start(event):
    name = event.sender.first_name or "User"

    await event.reply(f"""
👋 Hello {name}

╔════════════════════════════╗
   🕵️ Zshadow INTEL SYSTEM
╚════════════════════════════╝

📌 /num <number> ➜ Search Info

⚡ Powered by @Zshadow_legend
""")

# COMMAND
@bot.on(events.NewMessage(pattern=r"/num (.+)"))
async def num(event):

    if event.chat_id == GROUP_ID:
        return

    if event.out:
        return

    query = event.pattern_match.group(1).strip()

    if event.chat_id in active_searches:
        msg = await event.reply("⚠ Already searching...")
        asyncio.create_task(auto_delete(msg, 10))
        return

    search_msg = await event.reply("🔍 Searching...")

    active_searches[event.chat_id] = {
        "query": query,
        "search_msg": search_msg
    }

    await user.send_message(GROUP_ID, f"/num {query}")

# GROUP LISTENER
@user.on(events.NewMessage(chats=GROUP_ID))
async def group_listener(event):

    global last_text

    text = event.raw_text
    if not text:
        return

    if text == last_text:
        return

    last_text = text

    if text.startswith("/"):
        return

    matched_chat_id = None
    matched_data = None

    for chat_id, data in active_searches.items():
        if data["query"] in text:
            matched_chat_id = chat_id
            matched_data = data
            break

    if not matched_chat_id:
        return

    search_msg = matched_data["search_msg"]

    # BUFFER
    message_parts.setdefault(matched_chat_id, "")
    message_parts[matched_chat_id] += "\n" + text

    full_text = message_parts[matched_chat_id].lower()

    # ❌ NO DATA DETECTION (HIDDEN)
    no_data_keywords = [
        "no data", "no record", "not found",
        "invalid", "unavailable", "failed", "error"
    ]

    if any(k in full_text for k in no_data_keywords):

        fail_msg = await bot.send_message(
            matched_chat_id,
            """
╔════════════════════════════╗
   🕵️ Zshadow INTEL SYSTEM
╚════════════════════════════╝

❌ NO DATA FOUND

━━━━━━━━━━━━━━━━━━
⚠ No records available
for this request

━━━━━━━━━━━━━━━━━━
🔍 Try different input
━━━━━━━━━━━━━━━━━━
⚡ Powered by @Zshadow_legend
"""
        )

        asyncio.create_task(auto_delete(fail_msg, 60))

        try:
            await search_msg.delete()
        except:
            pass

        active_searches.pop(matched_chat_id, None)
        message_parts.pop(matched_chat_id, None)
        return

    # WAIT FOR FINAL PART
    if (
        '"success"' not in text
        and '"developer"' not in text
        and "Part 2" not in text
        and "Part 3" not in text
    ):
        return

    try:
        json_match = re.search(r'(\{[\s\S]*\})', message_parts[matched_chat_id])

        if not json_match:
            raise Exception("No JSON")

        parsed = json.loads(json_match.group(1))

        records = parsed.get("result", {}).get("data")
        if not records:
            records = parsed.get("result")

        if not records:
            raise Exception("Empty")

        result = """
╔════════════════════════════╗
   🕵️ Zshadow INTEL SYSTEM
╚════════════════════════════╝
"""

        for i, item in enumerate(records, 1):
            result += f"""

🔍 RECORD {i}
━━━━━━━━━━━━━━
👤 {item.get("NAME","N/A")}
📞 {item.get("MOBILE","N/A")}
🌐 {item.get("circle","N/A")}
🏠 {item.get("ADDRESS","N/A")}
🆔 {item.get("id","N/A")}
"""

        result += "\n━━━━━━━━━━━━━━\n⚡ Powered by @Zshadow_legend"

        msg = await bot.send_message(matched_chat_id, result)

        asyncio.create_task(auto_delete(msg, 60))

        try:
            await search_msg.delete()
        except:
            pass

        active_searches.pop(matched_chat_id, None)
        message_parts.pop(matched_chat_id, None)

    except Exception:
        fail_msg = await bot.send_message(
            matched_chat_id,
            """
╔════════════════════╗
   🕵️ Zshadow INTEL SYSTEM
╚════════════════════╝

❌ SEARCH FAILED
⚠ Unable to process response

━━━━━━━━━━━━━━━━━━
⚡ Powered by @Zshadow_legend
"""
        )

        asyncio.create_task(auto_delete(fail_msg, 60))

        try:
            await search_msg.delete()
        except:
            pass

        active_searches.pop(matched_chat_id, None)
        message_parts.pop(matched_chat_id, None)

# FLASK
app = Flask(__name__)

@app.route("/")
def home():
    return "ZIntel Running"

def run_web():
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 10000)))

Thread(target=run_web, daemon=True).start()

# MAIN
async def main():
    await start_clients()
    print("ZIntel Running 😎")

    await asyncio.gather(
        bot.run_until_disconnected(),
        user.run_until_disconnected()
    )

asyncio.run(main())