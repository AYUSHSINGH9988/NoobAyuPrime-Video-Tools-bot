from pyrogram import Client, filters
from config import Config
from helpers.database import db
import os

# Create Download Directory if it doesn't exist
if not os.path.exists(Config.DOWNLOAD_DIR):
    os.makedirs(Config.DOWNLOAD_DIR)

# Initialize Bot Client
app = Client(
    "VideoBot",
    api_id=Config.API_ID,
    api_hash=Config.API_HASH,
    bot_token=Config.BOT_TOKEN,
    plugins=dict(root="plugins") # Automatically loads the plugins folder
)

# User Queue Dictionary
user_queue = {}

@app.on_message(filters.command("start"))
async def start(client, message):
    # Add user to database
    await db.add_user(message.from_user.id)
    
    # Welcome Message in English with Emojis
    welcome_text = (
        "👋 **Welcome to the Ultimate Video Bot!** 🤖\n"
        "I am your All-in-One powerhouse for video editing, managing, and downloading.\n\n"
        "**🎬 Video Actions (Send a Video first):**\n"
        "🔹 `/compress` » Reduce size (HEVC) 📉\n"
        "🔹 `/trim 00:01 00:10` » Cut video ✂️\n"
        "🔹 `/screenshot` » Get Thumbnail 📸\n"
        "🔹 `/extract_audio` » Convert to MP3 🎵\n"
        "🔹 `/extract_sub` » Get Subtitles (.srt) 📝\n\n"
        "**🛠️ Pro Features (Reply to a Video):**\n"
        "🔸 `/watermark` » Reply with **Photo** to add Logo 🖼️\n"
        "🔸 `/add_sub` » Reply with **Subtitle** file 📜\n"
        "🔸 `/merge_audio` » Reply with **Audio** to Mix 🔀\n"
        "🔸 `/merge_videos` » Reply with **Video** to Join 🎞️\n\n"
        "**📂 File Manager:**\n"
        "🔹 `/rename NewName` » Change Filename ✏️\n"
        "🔹 `/zip` » Create Archive 📦\n"
        "🔹 `/unzip` » Extract Archive 🔓\n\n"
        "**🚀 URL Downloader:**\n"
        "Just send any **Link** (Instagram, YouTube, etc.) to download instantly! 📥"
    )
    
    await message.reply_text(welcome_text)

# Broadcast Command (Owner Only)
@app.on_message(filters.command("broadcast") & filters.user(Config.OWNER_ID))
async def broadcast(client, message):
    if not message.reply_to_message:
        return await message.reply("⚠️ Please reply to a message to broadcast.")
    
    users = await db.get_all_users()
    count = 0
    await message.reply("🚀 **Broadcast Started...**")
    
    async for user in users:
        try:
            await message.reply_to_message.copy(user['id'])
            count += 1
        except:
            pass
            
    await message.reply(f"✅ **Broadcast Complete!**\nSent to {count} users.")

if __name__ == "__main__":
    print("🤖 Bot Started Successfully! System Online.")
    app.run()
  
