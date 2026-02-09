import os
import time
import asyncio
import subprocess
import shutil
import traceback
import re
from pyrogram import Client, filters, enums
from pyrogram.types import Message
from aiohttp import web

# ==========================================
#         CONFIG & VARIABLES
# ==========================================
API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")
PORT = int(os.environ.get("PORT", 8080))
DUMP_CHANNEL = int(os.environ.get("DUMP_CHANNEL", 0))

app = Client("media_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Merge Queue: {user_id: "path/to/first_file"}
MERGE_DICT = {}
PROCESSING_QUEUE = []

# ==========================================
#           HELPER FUNCTIONS
# ==========================================
def clean_up(path):
    try:
        if os.path.exists(path):
            if os.path.isdir(path): shutil.rmtree(path)
            else: os.remove(path)
    except: pass

async def run_ffmpeg(cmd):
    process = await asyncio.create_subprocess_exec(
        *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    await process.wait()
    return process.returncode

async def progress_bar(current, total, msg, action):
    now = time.time()
    if not hasattr(msg, 'last_update'): msg.last_update = 0
    if (now - msg.last_update) > 5 or current == total:
        percent = current * 100 / total
        try:
            await msg.edit_text(f"⚙️ **{action}**\n📊 Progress: `{round(percent, 1)}%`")
            msg.last_update = now
        except: pass

# ==========================================
#           MEDIA LOGIC (FFMPEG)
# ==========================================
async def compress_video(video_path):
    out = f"compressed_{os.path.basename(video_path)}"
    # CRF 28 is good compression/quality balance
    cmd = ["ffmpeg", "-i", video_path, "-vcodec", "libx264", "-crf", "28", "-preset", "fast", out, "-y"]
    if await run_ffmpeg(cmd) == 0: return out
    return None

async def extract_audio(video_path):
    out = f"{video_path}.mp3"
    cmd = ["ffmpeg", "-i", video_path, "-vn", "-acodec", "libmp3lame", "-q:a", "2", out, "-y"]
    if await run_ffmpeg(cmd) == 0: return out
    return None

async def extract_subtitle(video_path):
    out = f"{video_path}.srt"
    cmd = ["ffmpeg", "-i", video_path, "-map", "0:s:0", out, "-y"]
    if await run_ffmpeg(cmd) == 0: return out
    return None

async def take_screenshot(video_path):
    out = f"{video_path}.jpg"
    cmd = ["ffmpeg", "-ss", "00:00:05", "-i", video_path, "-vframes", "1", "-q:v", "2", out, "-y"]
    if await run_ffmpeg(cmd) == 0: return out
    return None

async def trim_video(video_path, start, end):
    out = f"trimmed_{os.path.basename(video_path)}"
    cmd = ["ffmpeg", "-ss", start, "-to", end, "-i", video_path, "-c", "copy", out, "-y"]
    if await run_ffmpeg(cmd) == 0: return out
    return None

async def add_watermark(video_path, img_path):
    out = f"watermarked_{os.path.basename(video_path)}"
    # Top-Right Corner (main_w-overlay_w-10:10)
    cmd = ["ffmpeg", "-i", video_path, "-i", img_path, "-filter_complex", "overlay=main_w-overlay_w-10:10", out, "-y"]
    if await run_ffmpeg(cmd) == 0: return out
    return None

async def merge_audio_video(video_path, audio_path):
    out = "merged_av.mp4"
    # Map video from file 0, audio from file 1. Shortest ends when shortest stream ends.
    cmd = ["ffmpeg", "-i", video_path, "-i", audio_path, "-c:v", "copy", "-c:a", "aac", "-map", "0:v:0", "-map", "1:a:0", "-shortest", out, "-y"]
    if await run_ffmpeg(cmd) == 0: return out
    return None

async def add_soft_subtitle(video_path, sub_path):
    out = "subbed_video.mkv"
    cmd = ["ffmpeg", "-i", video_path, "-i", sub_path, "-c", "copy", "-c:s", "srt", "-map", "0", "-map", "1", out, "-y"]
    if await run_ffmpeg(cmd) == 0: return out
    return None

async def join_videos(vid1, vid2):
    out = "joined.mp4"
    # Create list file
    with open("list.txt", "w") as f:
        f.write(f"file '{vid1}'\nfile '{vid2}'")
    cmd = ["ffmpeg", "-f", "concat", "-safe", "0", "-i", "list.txt", "-c", "copy", out, "-y"]
    if await run_ffmpeg(cmd) == 0: return out
    return None

# ==========================================
#           COMMAND HANDLERS
# ==========================================

@app.on_message(filters.command("start"))
async def start(c, m):
    await m.reply_text(
        "🛠 **Media Toolbox Bot**\n\n"
        "**Single File Commands (Reply to Video):**\n"
        "/compress - Reduce size\n"
        "/extract_audio - Get MP3\n"
        "/extract_sub - Get SRT\n"
        "/screenshot - Take SS\n"
        "/trim 00:00 00:10 - Cut video\n"
        "/rename NewName.mkv - Rename\n"
        "/zip - Create Zip\n"
        "/unzip - Extract Zip\n\n"
        "**Merge Commands (Two Steps):**\n"
        "1. Send Photo/Audio/Sub/Video FIRST.\n"
        "2. Reply to Video with:\n"
        "/watermark (needs Photo)\n"
        "/add_sub (needs SRT)\n"
        "/merge_audio (needs Audio)\n"
        "/merge_videos (needs Video)"
    )

# --- SAVE FIRST FILE FOR MERGE ---
@app.on_message(filters.private & (filters.document | filters.photo | filters.audio | filters.video))
async def save_for_merge(c, m):
    # This function passively listens. If user sends a file, we keep its ID.
    if m.document or m.photo or m.audio or m.video:
        # Don't download yet, just save ID/Message to check later
        MERGE_DICT[m.from_user.id] = m
        # We don't reply to avoid spam, user just sends file then commands.

# --- SINGLE FILE COMMANDS ---

@app.on_message(filters.command(["compress", "extract_audio", "extract_sub", "screenshot", "zip", "unzip"]))
async def process_media(c, m):
    if not m.reply_to_message:
        return await m.reply_text("❌ Reply to a file!")
    
    cmd = m.command[0]
    user_id = m.from_user.id
    msg = await m.reply_text("⬇️ **Downloading...**")
    
    try:
        file_path = await m.reply_to_message.download(progress=progress_bar, progress_args=(msg, "Downloading"))
        
        output = None
        upload_type = "doc"
        
        if cmd == "compress":
            await msg.edit_text("🗜 **Compressing...**")
            output = await compress_video(file_path)
            upload_type = "video"
        
        elif cmd == "extract_audio":
            await msg.edit_text("🎵 **Extracting Audio...**")
            output = await extract_audio(file_path)
            upload_type = "audio"

        elif cmd == "extract_sub":
            await msg.edit_text("📝 **Extracting Subtitles...**")
            output = await extract_subtitle(file_path)

        elif cmd == "screenshot":
            await msg.edit_text("📸 **Taking Screenshot...**")
            output = await take_screenshot(file_path)
            upload_type = "photo"

        elif cmd == "zip":
            await msg.edit_text("🤐 **Zipping...**")
            output = f"{file_path}.zip"
            await run_ffmpeg(["7z", "a", output, file_path])

        elif cmd == "unzip":
            if not file_path.endswith(".zip"):
                 await msg.edit_text("❌ Not a zip file!"); clean_up(file_path); return
            await msg.edit_text("📂 **Unzipping...**")
            await run_ffmpeg(["7z", "x", file_path])
            # For unzip, we just upload whatever extracted (simplified)
            output = "Extracted" # Placeholder logic

        if output and os.path.exists(output):
            await msg.edit_text("⬆️ **Uploading...**")
            
            if upload_type == "video":
                await m.reply_video(output)
            elif upload_type == "audio":
                await m.reply_audio(output)
            elif upload_type == "photo":
                await m.reply_photo(output)
            else:
                await m.reply_document(output)
                
            clean_up(output)
        else:
            await msg.edit_text("❌ Task Failed.")
            
    except Exception as e:
        await msg.edit_text(f"⚠️ Error: {e}")
        traceback.print_exc()
    
    clean_up(file_path)

# --- RENAME & TRIM ---

@app.on_message(filters.command("rename"))
async def rename_cmd(c, m):
    if not m.reply_to_message or len(m.command) < 2:
        return await m.reply_text("❌ Usage: Reply to file + `/rename NewName.mkv`")
    
    new_name = m.text.split(None, 1)[1]
    msg = await m.reply_text("⬇️ **Downloading...**")
    path = await m.reply_to_message.download(progress=progress_bar, progress_args=(msg, "Downloading"))
    
    try:
        os.rename(path, new_name)
        await msg.edit_text("⬆️ **Uploading...**")
        await m.reply_document(new_name, caption=f"Renamed to: `{new_name}`")
        clean_up(new_name)
    except Exception as e:
        await msg.edit_text(f"Error: {e}")

@app.on_message(filters.command("trim"))
async def trim_cmd(c, m):
    # Usage: /trim 00:00:10 00:00:20
    if not m.reply_to_message or len(m.command) < 3:
        return await m.reply_text("❌ Usage: `/trim 00:00:00 00:00:10` (Reply to Video)")
    
    start, end = m.command[1], m.command[2]
    msg = await m.reply_text("⬇️ **Downloading...**")
    path = await m.reply_to_message.download(progress=progress_bar, progress_args=(msg, "Downloading"))
    
    try:
        await msg.edit_text("✂️ **Trimming...**")
        out = await trim_video(path, start, end)
        if out:
            await msg.edit_text("⬆️ **Uploading...**")
            await m.reply_video(out)
            clean_up(out)
        else:
            await msg.edit_text("❌ Trim failed.")
    except Exception as e:
        await msg.edit_text(f"Error: {e}")
    clean_up(path)

# --- MERGE FEATURES (2-STEP) ---

@app.on_message(filters.command(["watermark", "add_sub", "merge_audio", "merge_videos"]))
async def merge_cmd(c, m):
    # Check if user sent a file previously
    if m.from_user.id not in MERGE_DICT:
        return await m.reply_text("❌ Pehle ek file (Photo/Audio/Sub) bhejo, fir Video pe reply karke command do.")
    
    if not m.reply_to_message:
        return await m.reply_text("❌ Video par reply karo!")

    cmd = m.command[0]
    first_msg = MERGE_DICT[m.from_user.id]
    msg = await m.reply_text("⬇️ **Downloading Files...**")

    try:
        # Download MAIN Video (replied to)
        vid_path = await m.reply_to_message.download(progress=progress_bar, progress_args=(msg, "DL Video"))
        
        # Download SECONDARY File (saved in dict)
        file_2_path = await first_msg.download(progress=progress_bar, progress_args=(msg, "DL Asset"))

        output = None
        
        if cmd == "watermark":
            await msg.edit_text("🖼 **Adding Watermark...**")
            output = await add_watermark(vid_path, file_2_path)

        elif cmd == "add_sub":
            await msg.edit_text("📝 **Adding Subtitles...**")
            output = await add_soft_subtitle(vid_path, file_2_path)

        elif cmd == "merge_audio":
            await msg.edit_text("🎵 **Merging Audio...**")
            output = await merge_audio_video(vid_path, file_2_path)

        elif cmd == "merge_videos":
            await msg.edit_text("🎞 **Joining Videos...**")
            output = await join_videos(file_2_path, vid_path) # Join First + Second

        if output and os.path.exists(output):
            await msg.edit_text("⬆️ **Uploading...**")
            await m.reply_video(output)
            clean_up(output)
        else:
            await msg.edit_text("❌ Merge Failed.")
        
        clean_up(file_2_path)

    except Exception as e:
        await msg.edit_text(f"⚠️ Error: {e}")
        traceback.print_exc()
    
    clean_up(vid_path)
    # Clear memory
    del MERGE_DICT[m.from_user.id]

# ==========================================
#           SERVER & STARTUP
# ==========================================
async def web_server():
    async def handle(request): return web.Response(text="Bot Running")
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()

if __name__ == "__main__":
    print("🤖 Bot Started!")
    loop = asyncio.get_event_loop()
    loop.run_until_complete(app.start())
    loop.run_until_complete(web_server())
    idle()
  
