from pyrogram import Client, filters
from main import app, user_queue
from config import Config
from helpers.ffmpeg_tools import (
    compress_video, extract_audio, generate_thumbnail, 
    merge_av, join_videos, trim_video, 
    add_watermark, extract_subtitle, add_subtitle
)
import os

# --- 1. COMPRESS ---
@app.on_message(filters.command("compress"))
async def compress_cmd(client, message):
    video_msg = user_queue.get(message.from_user.id)
    if not video_msg: return await message.reply("❌ Pehle ek video bhejein!")
    msg = await message.reply("⏳ Downloading...")
    path = await video_msg.download(Config.DOWNLOAD_DIR)
    out_path = f"{Config.DOWNLOAD_DIR}compressed_{message.from_user.id}.mp4"
    try:
        await msg.edit("🗜 Compressing (HEVC)...")
        await compress_video(path, out_path)
        thumb = await generate_thumbnail(out_path, f"{Config.DOWNLOAD_DIR}thumb.jpg")
        await msg.edit("📤 Uploading...")
        await client.send_video(message.chat.id, video=out_path, caption="**Compressed** ✅", thumb=thumb)
    except Exception as e: await msg.edit(f"Error: {e}")
    finally:
        if os.path.exists(path): os.remove(path)
        if os.path.exists(out_path): os.remove(out_path)

# --- 2. TRIM ---
@app.on_message(filters.command("trim"))
async def trim_cmd(client, message):
    video_msg = user_queue.get(message.from_user.id)
    if not video_msg: return await message.reply("❌ Pehle ek video bhejein!")
    args = message.text.split(" ")
    if len(args) != 3: return await message.reply("❌ Use: `/trim 00:00:10 00:00:20`")
    start, end = args[1], args[2]
    msg = await message.reply(f"⏳ Trimming {start} to {end}...")
    path = await video_msg.download(Config.DOWNLOAD_DIR)
    out_path = f"{Config.DOWNLOAD_DIR}trimmed_{message.from_user.id}.mp4"
    try:
        await trim_video(path, out_path, start, end)
        thumb = await generate_thumbnail(out_path, f"{Config.DOWNLOAD_DIR}thumb.jpg")
        await msg.edit("📤 Uploading...")
        await client.send_video(message.chat.id, video=out_path, caption=f"**Trimmed** ✂️\n{start} - {end}", thumb=thumb)
    except Exception as e: await msg.edit(f"Error: {e}")
    finally:
        if os.path.exists(path): os.remove(path)
        if os.path.exists(out_path): os.remove(out_path)

# --- 3. EXTRACT AUDIO ---
@app.on_message(filters.command("extract_audio"))
async def audio_cmd(client, message):
    video_msg = user_queue.get(message.from_user.id)
    if not video_msg: return await message.reply("❌ Pehle ek video bhejein!")
    msg = await message.reply("⏳ Downloading...")
    path = await video_msg.download(Config.DOWNLOAD_DIR)
    out_path = f"{Config.DOWNLOAD_DIR}audio_{message.from_user.id}.mp3"
    try:
        await msg.edit("🎵 Extracting Audio...")
        await extract_audio(path, out_path)
        await msg.edit("📤 Uploading...")
        await client.send_audio(message.chat.id, audio=out_path)
    except Exception as e: await msg.edit(f"Error: {e}")
    finally:
        if os.path.exists(path): os.remove(path)
        if os.path.exists(out_path): os.remove(out_path)

# --- 4. RENAME ---
@app.on_message(filters.command("rename"))
async def rename_cmd(client, message):
    video_msg = user_queue.get(message.from_user.id)
    if not video_msg: return await message.reply("❌ Pehle ek file bhejein!")
    if len(message.command) < 2: return await message.reply("Use: `/rename name.mp4`")
    new_name = message.text.split(" ", 1)[1]
    msg = await message.reply("⏳ Downloading...")
    path = await video_msg.download(Config.DOWNLOAD_DIR)
    new_path = f"{Config.DOWNLOAD_DIR}{new_name}"
    try:
        os.rename(path, new_path)
        await msg.edit("📤 Uploading...")
        await client.send_document(message.chat.id, document=new_path, caption=f"**Renamed:** `{new_name}`")
    except Exception as e: await msg.edit(f"Error: {e}")
    finally:
        if os.path.exists(new_path): os.remove(new_path)

# --- 5. SCREENSHOT ---
@app.on_message(filters.command("screenshot"))
async def screenshot_cmd(client, message):
    video_msg = user_queue.get(message.from_user.id)
    if not video_msg: return await message.reply("❌ Pehle video bhejein!")
    msg = await message.reply("⏳ Processing...")
    path = await video_msg.download(Config.DOWNLOAD_DIR)
    thumb_path = f"{Config.DOWNLOAD_DIR}ss_{message.from_user.id}.jpg"
    try:
        ss = await generate_thumbnail(path, thumb_path)
        if ss: await client.send_photo(message.chat.id, photo=ss, caption="**Screenshot** 📸")
    except: await msg.edit("Failed.")
    finally:
        if os.path.exists(path): os.remove(path)
        if os.path.exists(thumb_path): os.remove(thumb_path)

# --- 6. MERGE AUDIO ---
@app.on_message(filters.command("merge_audio") & filters.reply)
async def merge_audio_handler(client, message):
    reply = message.reply_to_message
    if not (reply.video or reply.document) or not (message.audio or message.document):
        return await message.reply("❌ **Use:** Video par Audio reply karein + `/merge_audio`")
    msg = await message.reply("⬇️ Downloading...")
    vid_path = await reply.download(Config.DOWNLOAD_DIR)
    aud_path = await message.download(Config.DOWNLOAD_DIR)
    out_path = f"{Config.DOWNLOAD_DIR}merged_{message.from_user.id}.mp4"
    try:
        await msg.edit("🔀 Merging...")
        await merge_av(vid_path, aud_path, out_path)
        await msg.edit("⬆️ Uploading...")
        await client.send_video(message.chat.id, video=out_path, caption="**Audio Merged!** ✅")
    except Exception as e: await msg.edit(f"Error: {e}")
    finally:
        for f in [vid_path, aud_path, out_path]:
            if os.path.exists(f): os.remove(f)

# --- 7. MERGE VIDEOS (JOIN) ---
@app.on_message(filters.command("merge_videos") & filters.reply)
async def join_videos_handler(client, message):
    reply = message.reply_to_message
    if not (reply.video or reply.document) or not (message.video or message.document):
        return await message.reply("❌ **Use:** Video 1 par Video 2 reply karein + `/merge_videos`")
    msg = await message.reply("⬇️ Downloading...")
    vid1_path = await reply.download(Config.DOWNLOAD_DIR)
    vid2_path = await message.download(Config.DOWNLOAD_DIR)
    out_path = f"{Config.DOWNLOAD_DIR}joined_{message.from_user.id}.mp4"
    try:
        await msg.edit("🔗 Joining...")
        await join_videos([vid1_path, vid2_path], out_path)
        await msg.edit("⬆️ Uploading...")
        await client.send_video(message.chat.id, video=out_path, caption="**Joined!** ✅")
    except Exception as e: await msg.edit(f"Error: {e}")
    finally:
        for f in [vid1_path, vid2_path, out_path]:
            if os.path.exists(f): os.remove(f)

# --- 8. WATERMARK (NEW) ---
@app.on_message(filters.command("watermark") & filters.reply)
async def watermark_handler(client, message):
    reply = message.reply_to_message
    # Check: Reply Video hona chahiye aur Command message Photo hona chahiye (ya vice versa)
    if not (reply.video or reply.document) or not message.photo:
         return await message.reply("❌ **Use:** Video par **Photo (Logo)** reply karein + `/watermark`")
    
    msg = await message.reply("⬇️ Downloading Video & Logo...")
    vid_path = await reply.download(Config.DOWNLOAD_DIR)
    img_path = await message.download(Config.DOWNLOAD_DIR)
    out_path = f"{Config.DOWNLOAD_DIR}watermarked_{message.from_user.id}.mp4"
    
    try:
        await msg.edit("🖼️ Adding Watermark...")
        await add_watermark(vid_path, img_path, out_path)
        thumb = await generate_thumbnail(out_path, f"{Config.DOWNLOAD_DIR}thumb.jpg")
        await msg.edit("⬆️ Uploading...")
        await client.send_video(message.chat.id, video=out_path, caption="**Watermark Added!** ✅", thumb=thumb)
    except Exception as e: await msg.edit(f"Error: {e}")
    finally:
        for f in [vid_path, img_path, out_path]:
            if os.path.exists(f): os.remove(f)

# --- 9. EXTRACT SUBTITLE (NEW) ---
@app.on_message(filters.command("extract_sub"))
async def extract_sub_handler(client, message):
    video_msg = user_queue.get(message.from_user.id)
    if not video_msg: return await message.reply("❌ Pehle video bhejein!")
    msg = await message.reply("⬇️ Downloading...")
    path = await video_msg.download(Config.DOWNLOAD_DIR)
    out_path = f"{Config.DOWNLOAD_DIR}sub_{message.from_user.id}.srt"
    try:
        await msg.edit("📝 Extracting Subtitles...")
        await extract_subtitle(path, out_path)
        if os.path.exists(out_path):
            await msg.edit("⬆️ Uploading...")
            await client.send_document(message.chat.id, document=out_path, caption="**Subtitle Extracted** (.srt)")
        else:
            await msg.edit("❌ No subtitles found.")
    except Exception as e: await msg.edit(f"Error: {e}")
    finally:
        if os.path.exists(path): os.remove(path)
        if os.path.exists(out_path): os.remove(out_path)

# --- 10. ADD SUBTITLE (NEW) ---
@app.on_message(filters.command("add_sub") & filters.reply)
async def add_sub_handler(client, message):
    reply = message.reply_to_message
    if not (reply.video or reply.document) or not message.document:
        return await message.reply("❌ **Use:** Video par **Subtitle file (.srt)** reply karein + `/add_sub`")
    
    msg = await message.reply("⬇️ Downloading...")
    vid_path = await reply.download(Config.DOWNLOAD_DIR)
    sub_path = await message.download(Config.DOWNLOAD_DIR)
    out_path = f"{Config.DOWNLOAD_DIR}subbed_{message.from_user.id}.mkv"
    
    try:
        await msg.edit("🎞️ Adding Subtitles...")
        await add_subtitle(vid_path, sub_path, out_path)
        await msg.edit("⬆️ Uploading...")
        await client.send_document(message.chat.id, document=out_path, caption="**Subtitle Added!** ✅")
    except Exception as e: await msg.edit(f"Error: {e}")
    finally:
        for f in [vid_path, sub_path, out_path]:
            if os.path.exists(f): os.remove(f)

# --- FILE HANDLER ---
@app.on_message(filters.video | filters.document)
async def video_handler(client, message):
    user_queue[message.from_user.id] = message
    await message.reply_text(
        "✅ **File Received! Commands:**\n"
        "🔹 `/compress`, `/rename`, `/trim`, `/screenshot`\n"
        "🔹 `/extract_audio`, `/extract_sub`\n"
        "🔹 `/zip`\n\n"
        "**Reply Commands:**\n"
        "🔸 `/watermark` (Photo reply)\n"
        "🔸 `/add_sub` (Subtitle reply)\n"
        "🔸 `/merge_audio` (Audio reply)\n"
        "🔸 `/merge_videos` (Video reply)"
                        )
      
