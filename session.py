from telethon.sync import TelegramClient
from telethon.sessions import StringSession

api_id = 38557820
api_hash = "81a5e811402b71e31839f0263c466c57"

with TelegramClient(
    StringSession(),
    api_id,
    api_hash
) as client:

    print(
        client.session.save()
    )