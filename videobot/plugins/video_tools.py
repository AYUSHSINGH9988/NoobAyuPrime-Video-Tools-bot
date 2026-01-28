from pyrogram import Client, filters
from main import app
from config import Config
from helpers.ffmpeg_tools import compress_video, extract_audio, generate_thumbnail
import os
import time

# Store user state (simple dictionary for demo)
user_queue = {}

@app.on_message(filters.video | filters.document)
async def video_handler(client, message):
    # Save file info for later commands
    user_queue[message.from_user.id] = message
    await message.reply_text(
        "Video received! Now select an action:\n"
        "/compress - Compress Video\n"
        "/extract_audio - Extract Audio\n"
        "/screenshot - Get Screenshot"
    )

@app.on_message(filters.command("compress"))
async def compress_cmd(client, message):
    video_msg = user_queue.get(message.from_user.id)
    if not video_msg:
        return await message.reply("Send a video first!")
    
    msg = await message.reply("Downloading...")
    path = await video_msg.download(Config.DOWNLOAD_DIR)
    
    await msg.edit("Compressing (HEVC)... This may take time.")
    out_path = f"{Config.DOWNLOAD_DIR}compressed_{message.from_user.id}.mp4"
    
    try:
        compressed = await compress_video(path, out_path)
        thumb = await generate_thumbnail(compressed, f"{Config.DOWNLOAD_DIR}thumb.jpg")
        
        await msg.edit("Uploading...")
        await client.send_video(
            chat_id=message.chat.id,
            video=compressed,
            caption="**Compressed with HEVC**",
            thumb=thumb
        )
        # Log to Channel
        await client.send_video(Config.LOG_CHANNEL, video=compressed, caption=f"User: {message.from_user.id}")
    except Exception as e:
        await msg.edit(f"Error: {e}")
    finally:
        if os.path.exists(path): os.remove(path)
        if os.path.exists(out_path): os.remove(out_path)

@app.on_message(filters.command("extract_audio"))
async def audio_cmd(client, message):
    video_msg = user_queue.get(message.from_user.id)
    if not video_msg:
        return await message.reply("Send a video first!")
    
    msg = await message.reply("Downloading...")
    path = await video_msg.download(Config.DOWNLOAD_DIR)
    out_path = f"{Config.DOWNLOAD_DIR}audio_{message.from_user.id}.mp3"
    
    await msg.edit("Extracting Audio...")
    await extract_audio(path, out_path)
    
    await msg.edit("Uploading Audio...")
    await client.send_audio(message.chat.id, audio=out_path)
    
    os.remove(path)
    os.remove(out_path)
  
