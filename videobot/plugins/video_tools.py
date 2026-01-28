from pyrogram import Client, filters
from main import app, user_queue
from config import Config
from helpers.ffmpeg_tools import compress_video, extract_audio, generate_thumbnail, merge_av, join_videos, trim_video
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

@app.on_message(filters.command("trim"))
async def trim_cmd(client, message):
    video_msg = user_queue.get(message.from_user.id)
    if not video_msg:
        return await message.reply("❌ Pehle ek video bhejein!")
    
    # Check arguments
    args = message.text.split(" ")
    if len(args) != 3:
        return await message.reply("❌ **Format:** `/trim 00:00:10 00:00:20`\n(Start Time aur End Time batayein)")

    start_time = args[1]
    end_time = args[2]
    
    msg = await message.reply(f"⏳ Trimming from {start_time} to {end_time}...")
    path = await video_msg.download(Config.DOWNLOAD_DIR)
    out_path = f"{Config.DOWNLOAD_DIR}trimmed_{message.from_user.id}.mp4"
    
    try:
        await trim_video(path, out_path, start_time, end_time)
        thumb = await generate_thumbnail(out_path, f"{Config.DOWNLOAD_DIR}thumb.jpg")
        
        await msg.edit("📤 Uploading...")
        await client.send_video(message.chat.id, video=out_path, caption=f"**Trimmed Video** ✂️\nFrom: {start_time} To: {end_time}", thumb=thumb)
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

@app.on_message(filters.command("merge_audio") & filters.reply)
async def merge_audio_handler(client, message):
    reply = message.reply_to_message
    if not (reply.video or reply.document) or not (message.audio or message.document):
        return await message.reply("❌ **Tareeka:** Pehle Video bhejein, fir us par **Audio file** reply karke `/merge_audio` likhein.")

    msg = await message.reply("⬇️ Downloading files...")
    
    vid_path = await reply.download(Config.DOWNLOAD_DIR)
    aud_path = await message.download(Config.DOWNLOAD_DIR)
    out_path = f"{Config.DOWNLOAD_DIR}merged_{message.from_user.id}.mp4"

    await msg.edit("🔀 Merging Video & Audio...")
    try:
        await merge_av(vid_path, aud_path, out_path)
        await msg.edit("⬆️ Uploading...")
        await client.send_video(message.chat.id, video=out_path, caption="**Video + Audio Merged!** ✅")
    except Exception as e:
        await msg.edit(f"Error: {e}")
    finally:
        for f in [vid_path, aud_path, out_path]:
            if os.path.exists(f): os.remove(f)

@app.on_message(filters.command("merge_videos") & filters.reply)
async def join_videos_handler(client, message):
    reply = message.reply_to_message
    if not (reply.video or reply.document) or not (message.video or message.document):
        return await message.reply("❌ **Tareeka:** Pehle Video 1 bhejein, fir us par **Video 2** reply karke `/merge_videos` likhein.")

    msg = await message.reply("⬇️ Downloading both videos...")
    
    vid1_path = await reply.download(Config.DOWNLOAD_DIR)
    vid2_path = await message.download(Config.DOWNLOAD_DIR)
    out_path = f"{Config.DOWNLOAD_DIR}joined_{message.from_user.id}.mp4"

    await msg.edit("🔗 Joining Videos...")
    try:
        await join_videos([vid1_path, vid2_path], out_path)
        await msg.edit("⬆️ Uploading...")
        await client.send_video(message.chat.id, video=out_path, caption="**Videos Joined!** ✅")
    except Exception as e:
        await msg.edit(f"Error: {e}")
    finally:
        for f in [vid1_path, vid2_path, out_path]:
            if os.path.exists(f): os.remove(f)

@app.on_message(filters.video | filters.document)
async def video_handler(client, message):
    user_queue[message.from_user.id] = message
    await message.reply_text(
        "✅ **File Received!**\n\n"
        "**Available Commands:**\n"
        "🔹 `/trim 00:00:10 00:00:30` - Video Kaatein ✂️\n"
        "🔹 `/compress` - Size kam karein\n"
        "🔹 `/rename name.mp4` - Naam badlein\n"
        "🔹 `/extract_audio` - MP3 banayein\n"
        "🔹 `/screenshot` - Photo lein\n"
        "🔹 `/zip` - Archive banayein\n\n"
        "**Merge Commands (Reply karke):**\n"
        "🔸 `/merge_audio` - Video me Audio lagayein\n"
        "🔸 `/merge_videos` - 2 Video jodein"
  )
  
