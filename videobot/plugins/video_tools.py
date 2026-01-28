from pyrogram import Client, filters
from main import app, user_queue
from config import Config
from helpers.ffmpeg_tools import compress_video, extract_audio, generate_thumbnail
import os

@app.on_message(filters.command("compress"))
async def compress_cmd(client, message):
    video_msg = user_queue.get(message.from_user.id)
    if not video_msg:
        return await message.reply("❌ Pehle ek video bhejein!")
    
    msg = await message.reply("⏳ Downloading...")
    path = await video_msg.download(Config.DOWNLOAD_DIR)
    
    await msg.edit("🗜 Compressing (HEVC)...")
    out_path = f"{Config.DOWNLOAD_DIR}compressed_{message.from_user.id}.mp4"
    
    try:
        compressed = await compress_video(path, out_path)
        thumb = await generate_thumbnail(compressed, f"{Config.DOWNLOAD_DIR}thumb.jpg")
        await msg.edit("📤 Uploading...")
        await client.send_video(message.chat.id, video=compressed, caption="**Compressed** ✅", thumb=thumb)
    except Exception as e:
        await msg.edit(f"Error: {e}")
    finally:
        if os.path.exists(path): os.remove(path)
        if os.path.exists(out_path): os.remove(out_path)

@app.on_message(filters.command("extract_audio"))
async def audio_cmd(client, message):
    video_msg = user_queue.get(message.from_user.id)
    if not video_msg:
        return await message.reply("❌ Pehle ek video bhejein!")
    
    msg = await message.reply("⏳ Downloading...")
    path = await video_msg.download(Config.DOWNLOAD_DIR)
    out_path = f"{Config.DOWNLOAD_DIR}audio_{message.from_user.id}.mp3"
    
    await msg.edit("🎵 Extracting Audio...")
    await extract_audio(path, out_path)
    
    await msg.edit("📤 Uploading...")
    await client.send_audio(message.chat.id, audio=out_path)
    
    os.remove(path)
    os.remove(out_path)

@app.on_message(filters.command("rename"))
async def rename_cmd(client, message):
    video_msg = user_queue.get(message.from_user.id)
    if not video_msg:
        return await message.reply("❌ Pehle ek file bhejein!")
    
    if len(message.command) < 2:
        return await message.reply("Use format: `/rename new_filename.mp4`")
    
    new_name = message.text.split(" ", 1)[1]
    
    msg = await message.reply("⏳ Downloading...")
    path = await video_msg.download(Config.DOWNLOAD_DIR)
    new_path = f"{Config.DOWNLOAD_DIR}{new_name}"
    
    os.rename(path, new_path)
    
    await msg.edit("📤 Uploading with new name...")
    await client.send_document(message.chat.id, document=new_path, caption=f"**Renamed to:** `{new_name}`")
    
    if os.path.exists(new_path): os.remove(new_path)

@app.on_message(filters.command("screenshot"))
async def screenshot_cmd(client, message):
    video_msg = user_queue.get(message.from_user.id)
    if not video_msg:
        return await message.reply("❌ Pehle ek video bhejein!")
    
    msg = await message.reply("⏳ Downloading...")
    path = await video_msg.download(Config.DOWNLOAD_DIR)
    thumb_path = f"{Config.DOWNLOAD_DIR}ss_{message.from_user.id}.jpg"
    
    await msg.edit("📸 Taking Screenshot...")
    ss = await generate_thumbnail(path, thumb_path)
    
    if ss:
        await client.send_photo(message.chat.id, photo=ss, caption="**Here is your screenshot**")
    else:
        await msg.edit("Failed to take screenshot.")
        
    if os.path.exists(path): os.remove(path)
    if os.path.exists(thumb_path): os.remove(thumb_path)

@app.on_message(filters.video | filters.document)
async def video_handler(client, message):
    user_queue[message.from_user.id] = message
    await message.reply_text(
        "✅ **File Received!**\n\n"
        "Ab command choose karein:\n"
        "🔹 `/compress` - Size kam karein\n"
        "🔹 `/rename filename.ext` - Naam badlein\n"
        "🔹 `/extract_audio` - MP3 banayein\n"
        "🔹 `/screenshot` - Photo lein\n"
        "🔹 `/zip` - Archive banayein"
  )
  
