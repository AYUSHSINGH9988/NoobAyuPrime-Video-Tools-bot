from pyrogram import Client, filters
from config import Config
from helpers.downloader import download_url
import os

@Client.on_message(filters.regex(r'^(http|https)://'))
async def url_handler(client, message):
    url = message.text
    msg = await message.reply("🔎 URL Detected. Processing...")
    
    try:
        await msg.edit("📥 Downloading content...")
        file_path = await download_url(url, Config.DOWNLOAD_DIR)
        
        await msg.edit("📤 Uploading...")
        if file_path.endswith((".mp4", ".mkv", ".webm")):
            await client.send_video(message.chat.id, video=file_path, caption=f"Downloaded via @{Config.BOT_TOKEN.split(':')[0]}")
        else:
            await client.send_document(message.chat.id, document=file_path)
            
    except Exception as e:
        await msg.edit(f"❌ Error: {e}")
    finally:
        if 'file_path' in locals() and file_path and os.path.exists(file_path):
            os.remove(file_path)
          
