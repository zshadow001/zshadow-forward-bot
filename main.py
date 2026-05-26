import os
import json
import re
import asyncio
from flask import Flask
from threading import Thread
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from supabase import create_client

# ======================
# ENV
# ======================
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
STRING_SESSION = os.getenv("STRING_SESSION")
GROUP_ID = int(os.getenv("GROUP_ID"))

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

ADMIN_ID = 8111461057

# ======================
# SUPABASE
# ======================
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ======================
# CLIENTS
# ======================
bot = TelegramClient("bot", API_ID, API_HASH)
user = TelegramClient(StringSession(STRING_SESSION), API_ID, API_HASH)

# ======================
# STORAGE
# ======================
active_searches = {}
message_parts = {}
dynamic_commands = {}
pending_admin = {}
last_text = None

# ======================
# AUTO DELETE
# ======================
async def auto_delete(msg, sec):
    await asyncio.sleep(sec)
    try:
        await msg.delete()
    except:
        pass

# ======================
# ADMIN CHECK
# ======================
def is_admin(event):
    return event.sender_id == ADMIN_ID

# ======================
# USERS
# ======================
def add_user(uid):
    try:
        supabase.table("users").upsert({"id": uid}).execute()
    except:
        pass

def get_users():
    try:
        return supabase.table("users").select("*").execute().data or []
    except:
        return []

# ======================
# COMMAND LOAD
# ======================
def load_commands():
    global dynamic_commands
    try:
        res = supabase.table("commands").select("*").execute()
        for c in res.data or []:
            dynamic_commands[c["id"]] = c["response"]
    except:
        pass

# ======================
# FORMAT ENGINE (NO SCROLL OF TRUTH)
# ======================
def format_response(records, target):

    output = f"""
𓆩 𝗭𝗜𝗡𝗧𝗘𝗟 𝗜𝗡𝗧𝗘𝗟 𝗦𝗬𝗦𝗧𝗘𝗠 𓆪

━━━━━━━━━━━━━━━━━━━━━━
🎯 TARGET ➜ {target}
📂 STATUS ➜ FOUND
━━━━━━━━━━━━━━━━━━━━━━
"""

    for i, r in enumerate(records, 1):
        output += f"""

🔍 RECORD {i}
━━━━━━━━━━━━━━━━━━━━━━
👤 NAME ➜ {r.get('NAME','N/A')}
📞 MOBILE ➜ {r.get('MOBILE','N/A')}
🌐 CIRCLE ➜ {r.get('circle','N/A')}
🏠 ADDRESS ➜ {r.get('ADDRESS','N/A')}
🆔 ID ➜ {r.get('id','N/A')}
"""

    output += """

━━━━━━━━━━━━━━━━━━━━━━
⚡ POWERED BY @Zshadow_legend
"""
    return output

# ======================
# START CLIENTS
# ======================
async def start_clients():
    await bot.start(bot_token=BOT_TOKEN)
    await user.start()
    load_commands()

# ======================
# /start
# ======================
@bot.on(events.NewMessage(pattern="/start"))
async def start(event):
    add_user(event.sender_id)

    name = event.sender.first_name or "User"

    await event.reply(f"""
👋 Hello {name}

🕵️ ZINTEL SYSTEM

/num <query>
/admin

⚡ Powered by @Zshadow_legend
""")

# ======================
# SEARCH ENGINE
# ======================
@bot.on(events.NewMessage(pattern=r"/num (.+)"))
async def num(event):

    if event.chat_id in active_searches:
        msg = await event.reply("⚠ Busy...")
        asyncio.create_task(auto_delete(msg, 10))
        return

    query = event.pattern_match.group(1).strip()

    search_msg = await event.reply("🔍 Searching...")

    active_searches[event.chat_id] = {
        "query": query,
        "msg": search_msg
    }

    await user.send_message(GROUP_ID, f"/num {query}")

# ======================
# DYNAMIC COMMANDS
# ======================
@bot.on(events.NewMessage)
async def dynamic_router(event):

    text = event.raw_text
    if not text.startswith("/"):
        return

    cmd = text.split(" ")[0][1:]
    args = " ".join(text.split(" ")[1:])

    if cmd in dynamic_commands:
        await event.reply(dynamic_commands[cmd].replace("{query}", args))

# ======================
# GROUP LISTENER
# ======================
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

    matched = None

    for cid, data in active_searches.items():
        if data["query"] in text:
            matched = (cid, data)
            break

    if not matched:
        return

    chat_id, data = matched
    search_msg = data["msg"]

    message_parts.setdefault(chat_id, "")
    message_parts[chat_id] += "\n" + text

    full = message_parts[chat_id].lower()

    if any(x in full for x in ["no data", "not found", "error", "invalid"]):

        msg = await bot.send_message(chat_id, "❌ No Data Found")
        asyncio.create_task(auto_delete(msg, 60))

        try:
            await search_msg.delete()
        except:
            pass

        active_searches.pop(chat_id, None)
        message_parts.pop(chat_id, None)
        return

    if '"success"' not in text and "Part 2" not in text:
        return

    try:
        json_match = re.search(r'(\{[\s\S]*\})', message_parts[chat_id])

        if not json_match:
            raise Exception()

        parsed = json.loads(json_match.group(1))

        records = parsed.get("result", {}).get("data") or parsed.get("result")

        if not records:
            raise Exception()

        target = data["query"]

        final_text = format_response(records, target)

        msg = await bot.send_message(chat_id, final_text)

        asyncio.create_task(auto_delete(msg, 60))

        await search_msg.delete()

        active_searches.pop(chat_id, None)
        message_parts.pop(chat_id, None)

    except:
        await bot.send_message(chat_id, "❌ Parse Error")

# ======================
# FLASK
# ======================
app = Flask(__name__)

@app.route("/")
def home():
    return "ZIntel Running 😎"

Thread(target=lambda: app.run(host="0.0.0.0", port=int(os.getenv("PORT", 10000))), daemon=True).start()

# ======================
# MAIN
# ======================
async def main():
    await start_clients()
    print("ZIntel Running 😎")

    await asyncio.gather(
        bot.run_until_disconnected(),
        user.run_until_disconnected()
    )

asyncio.run(main())