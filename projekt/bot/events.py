import json
import random
import discord
from pathlib import Path
def load_messages():from pathlib import Path

def load_messages():
    path = Path(__file__).resolve().parent.parent / "data" / "welcome_messages.json"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
        return json.load(f)

messages = load_messages()

WELCOME_CHANNEL_ID = 1482089357165854891  # <-- HIER deine Channel ID einfügen

async def on_member_join(member):
    print(f"JOIN EVENT: {member.name}")

    channel = member.guild.get_channel(WELCOME_CHANNEL_ID)

    if channel is None:
        print("Channel not found")
        return

    message = random.choice(messages)
    message = message.replace("{user}", member.mention)

    await channel.send(message)