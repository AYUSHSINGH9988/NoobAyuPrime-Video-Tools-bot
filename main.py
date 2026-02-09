import os
import time
import asyncio
import subprocess
import shutil
import traceback
import re
from pyrogram import Client, filters, idle, enums
from aiohttp import web

# ==========================================
#         CONFIG VARIABLES
# ==========================================
API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")
PORT = int(os.environ.get("PORT", 8080))

app = Client("media_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Queue to store the first file for merging features
MERGE_DICT = {}

# ==========================================
#           HELPER FUNCTIONS
# ==========================================
def clean_up(path):
    try:
        if os.path.exists(path):
            if os.path.isdir(path): shutil.rmtree(path)
            else: os.remove(path)
    except: pass

async def progress_bar(current, total, msg, action):
    now = time.time()
    if not hasattr(msg, 'last_update'): msg.last_update = 0
    if (now - msg.last_update) > 5 or current == total:
        percent = current * 100 / total
        try:
            await msg.edit_text(f"⚙️ **{action}**\n📊 Progress: `{round(percent, 1)}%`")
            msg.last_update = now
        except: pass

async def run_cmd(cmd):
    process = await asyncio.create_subprocess_exec(
        *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    await process.wait()
    return process.returncode

# ==========================================
#           FFMPEG & 7ZIP LOGIC
# ==========================================
async def compress_video(path):
    out = f"compressed_{os.path.basename(path)}"
    cmd = ["ffmpeg", "-i", path, "-vcodec", "libx264", "-crf", "28", "-preset", "fast", out, "-y"]
    return out if await run_cmd(cmd) == 0 else None

async def extract_audio(path):
    out = f"{path}.mp3"
    cmd = ["ffmpeg", "-i", path, "-vn", "-acodec", "libmp3lame", "-q:a", "2", out, "-y"]
    return out if await run_cmd(cmd) == 0 else None

async def extract_subtitle(path):
    out = f"{path}.srt"
    cmd = ["ffmpeg", "-i", path, "-map", "0:s:0", out, "-y"]
    return out if await run_cmd(cmd) == 0 else None

async def take_screenshot(path):
    out = f"{path}.jpg"
    cmd = ["ffmpeg", "-ss", "00:00:02", "-i", path, "-vframes", "1", "-q:v", "2", out, "-y"]
    return out if await run_cmd(cmd) == 0 else None

async def trim_video(path, start, end):
    out = f"trimmed_{os.path.basename(path)}"
    cmd = ["ffmpeg", "-ss", start, "-to", end, "-i", path, "-c", "copy", out, "-y"]
    return out if await run_cmd(cmd) == 0 else None

async def add_watermark(vid_path, img_path):
    out = f"watermarked_{os.path.basename(vid_path)}"
    cmd = ["ffmpeg", "-i", vid_path, "-i", img_path, "-filter_complex", "overlay=main_w-overlay_w-10:10", out, "-y"]
    return out if await run_cmd(cmd) == 0 else None

async def add_subtitle(vid_path, sub_path):
    out = "subbed_video.mkv"
    cmd = ["ffmpeg", "-i", vid_path, "-i", sub_path, "-c", "copy", "-c:s", "srt", "-map", "0", "-map", "1", out, "-y"]
    return out if await run_cmd(cmd) == 0 else None

async def merge_audio(vid_path, aud_path):
    out = "merged_audio.mp4"
    cmd = ["ffmpeg", "-i", vid_path, "-i", aud_path, "-c:v", "copy", "-c:a", "aac", "-map", "0:v:0", "-map", "1:a:0", "-shortest", out, "-y"]
    return out if await run_cmd(cmd) == 0 else None

async def join_videos(vid1, vid2):
    out = "joined.mp4"
    with open("list.txt", "w") as f:
        f.write(f"file '{vid1}'\nfile '{vid2}'")
    cmd = ["ffmpeg", "-f", "concat", "-safe", "0", "-i", "list.txt", "-c", "copy", out, "-y"]
    return out if await run_cmd(cmd) == 0 else None

async def zip_file(path):
    out = f"{path}.zip"
    cmd = ["7z", "a", out, path]
    return out if await run_cmd(cmd) == 0 else None

async def unzip_file(path):
    if not path.endswith(".zip"): return None
    out_dir = "extracted_files"
    if not os.path.exists(out_dir): os.makedirs(out_dir)
    cmd = ["7z", "x", path, f"-o{out_dir}", "-y"]
    return out_dir if await run_cmd(cmd) == 0 else None

# ==========================================
#           COMMAND HANDLERS
# ==========================================
@app.on_message(filters.command("start"))
async def start(c, m):
    await m.reply_text("👋 **Media Toolkit Bot Online!**\nSend a file and reply with a command.")

@app.on_message(filters.command("rename"))
async def rename(c, m):
    if not m.reply_to_message: return await m.reply_text("❌ Reply to a file!")
    if len(m.command) < 2: return await m.reply_text("❌ Usage: `/rename NewName.mkv`")
    new_name = m.text.split(None, 1)[1]
    msg = await m.reply_text("⬇️ **Downloading...**")
    try:
        path = await m.reply_to_message.download(progress=progress_bar, progress_args=(msg, "DL"))
        os.rename(path, new_name)
        await msg.edit_text("⬆️ **Uploading...**")
        await m.reply_document(new_name, caption=f"Renamed: `{new_name}`")
        clean_up(new_name)
    except Exception as e: await msg.edit_text(f"Error: {e}")

@app.on_message(filters.command("trim"))
async def trim(c, m):
    if not m.reply_to_message: return await m.reply_text("❌ Reply to a video!")
    if len(m.command) < 3: return await m.reply_text("❌ Usage: `/trim 00:00:10 00:00:20`")
    start, end = m.command[1], m.command[2]
    msg = await m.reply_text("⬇️ **Downloading...**")
    try:
        path = await m.reply_to_message.download(progress=progress_bar, progress_args=(msg, "DL"))
        await msg.edit_text("✂️ **Trimming...**")
        out = await trim_video(path, start, end)
        if out:
            await msg.edit_text("⬆️ **Uploading...**")
            await m.reply_video(out)
            clean_up(out)
        else: await msg.edit_text("❌ Failed.")
        clean_up(path)
    except Exception as e: await msg.edit_text(f"Error: {e}")

@app.on_message(filters.command(["compress", "extract_audio", "extract_sub", "screenshot", "zip", "unzip"]))
async def single_file_cmds(c, m):
    if not m.reply_to_message: return await m.reply_text("❌ Reply to a file!")
    cmd = m.command[0]
    msg = await m.reply_text("⬇️ **Downloading...**")
    try:
        path = await m.reply_to_message.download(progress=progress_bar, progress_args=(msg, "DL"))
        out = None
        if cmd == "compress":
            await msg.edit_text("🗜 **Compressing...**")
            out = await compress_video(path)
        elif cmd == "extract_audio":
            await msg.edit_text("🎵 **Extracting Audio...**")
            out = await extract_audio(path)
        elif cmd == "extract_sub":
            await msg.edit_text("📝 **Extracting Subtitles...**")
            out = await extract_subtitle(path)
        elif cmd == "screenshot":
            await msg.edit_text("📸 **Taking Screenshot...**")
            out = await take_screenshot(path)
        elif cmd == "zip":
            await msg.edit_text("🤐 **Zipping...**")
            out = await zip_file(path)
        elif cmd == "unzip":
            await msg.edit_text("📂 **Unzipping...**")
            out = await unzip_file(path)
        
        if out:
            await msg.edit_text("⬆️ **Uploading...**")
            if cmd == "unzip" and os.path.isdir(out):
                files = os.listdir(out)
                if not files: await msg.edit_text("❌ Empty Zip.")
                else:
                    for f in files:
                        full_path = os.path.join(out, f)
                        await m.reply_document(full_path)
            elif cmd == "screenshot": await m.reply_photo(out)
            elif cmd == "extract_audio": await m.reply_audio(out)
            elif cmd == "compress": await m.reply_video(out)
            else: await m.reply_document(out)
            clean_up(out)
        else: await msg.edit_text("❌ Task Failed.")
        clean_up(path)
    except Exception as e: await msg.edit_text(f"Error: {e}")

@app.on_message(filters.private & (filters.document | filters.photo | filters.audio | filters.video))
async def cache_file(c, m):
    if m.document or m.photo or m.audio or m.video:
        MERGE_DICT[m.from_user.id] = m

@app.on_message(filters.command(["watermark", "add_sub", "merge_audio", "merge_videos"]))
async def merge_cmds(c, m):
    if m.from_user.id not in MERGE_DICT:
        return await m.reply_text("❌ Pehle file bhejo, fir Video pe reply karke command do.")
    if not m.reply_to_message: return await m.reply_text("❌ Video par reply karo!")
    cmd = m.command[0]
    file1_msg = MERGE_DICT[m.from_user.id]
    file2_msg = m.reply_to_message
    msg = await m.reply_text("⬇️ **Downloading Files...**")
    try:
        path1 = await file1_msg.download(progress=progress_bar, progress_args=(msg, "DL Asset"))
        path2 = await file2_msg.download(progress=progress_bar, progress_args=(msg, "DL Video"))
        out = None
        if cmd == "watermark":
            await msg.edit_text("🖼 **Adding Watermark...**")
            out = await add_watermark(path2, path1)
        elif cmd == "add_sub":
            await msg.edit_text("📝 **Adding Subtitles...**")
            out = await add_subtitle(path2, path1)
        elif cmd == "merge_audio":
            await msg.edit_text("🎵 **Merging Audio...**")
            out = await merge_audio(path2, path1)
        elif cmd == "merge_videos":
            await msg.edit_text("🎞 **Joining Videos...**")
            out = await join_videos(path2, path1)
        
        if out:
            await msg.edit_text("⬆️ **Uploading...**")
            await m.reply_video(out)
            clean_up(out)
        else: await msg.edit_text("❌ Merge Failed.")
        clean_up(path1); clean_up(path2)
        del MERGE_DICT[m.from_user.id]
    except Exception as e: await msg.edit_text(f"Error: {e}")

# ==========================================
#           SERVER & STARTUP (FIXED)
# ==========================================
async def main():
    # Start Bot
    print("🤖 Starting Bot Client...")
    await app.start()
    print("✅ Bot Started!")

    # Start Web Server
    print("🌍 Starting Web Server...")
    runner = web.AppRunner(web.Application())
    await runner.setup()
    
    # FIXED SYNTAX HERE: Complete line with IP and PORT
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    print(f"✅ Web Server running on Port {PORT}")

    # Keep Bot Running
    await idle()
    await app.stop()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
                                          
