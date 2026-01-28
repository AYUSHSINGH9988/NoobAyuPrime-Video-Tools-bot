from pyrogram import Client, filters
from config import Config
from helpers.database import db
import os

if not os.path.exists(Config.DOWNLOAD_DIR):
    os.makedirs(Config.DOWNLOAD_DIR)

app = Client(
    "VideoBot",
    api_id=Config.API_ID,
    api_hash=Config.API_HASH,
    bot_token=Config.BOT_TOKEN
)

@app.on_message(filters.command("start"))
async def start(client, message):
    await db.add_user(message.from_user.id)
    await message.reply_text(
        "👋 **Welcome!** I am an All-in-One Video Tool Bot.\n\n"
        "**Features:**\n"
        "🔹 /compress - HEVC Compress\n"
        "🔹 /rename - Rename File\n"
        "🔹 /trim - Trim Video\n"
        "🔹 /watermark - Add Watermark\n"
        "🔹 /extract_audio - Get MP3\n"
        "🔹 /screenshot - Generate SS\n\n"
        "Send me a video to get started!"
    )

@app.on_message(filters.command("broadcast") & filters.user(Config.OWNER_ID))
async def broadcast(client, message):
    if not message.reply_to_message:
        return await message.reply("Reply to a message to broadcast.")
    users = await db.get_all_users()
    count = 0
    async for user in users:
        try:
            await message.reply_to_message.copy(user['id'])
            count += 1
        except:
            pass
    await message.reply(f"Broadcasted to {count} users.")

# Load Plugins (Basic implementation within main for simplicity, 
# typically you would use 'plugins=dict(root="plugins")' in Client)
from plugins.video_tools import *

if __name__ == "__main__":
    print("Bot Started!")
    app.run()
  
