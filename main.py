import os
import time
import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# Progress Bar Import
from progress import progress_for_pyrogram

# --- CONFIGURATION ---
API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")

# --- OPTIMIZED CLIENT SETUP (Speed Boost) ---
app = Client(
    "my_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    workers=4, 
    max_concurrent_transmissions=4
)

# Global Queue for Merge
MERGE_QUEUE = {}

# --- START COMMAND ---
@app.on_message(filters.command(["start"]))
async def start(client, message):
    await message.reply_text(
        f"👋 Hello {message.from_user.mention}!\n\n"
        "I am a **Video Tool Bot** running on High Speed Mode 🚀.\n"
        "I can Compress, Merge, Trim, Rename and Extract Audio.\n\n"
        "Check commands via /help.",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("Developer", url="https://t.me/USER_AYUSH")]]
        )
    )

# --- HELP COMMAND ---
@app.on_message(filters.command(["help"]))
async def help_command(client, message):
    text = (
        "🛠 **Available Commands:**\n\n"
        "• /compress - Reply to video to compress (Fast)\n"
        "• /extract_audio - Reply to video to get MP3\n"
        "• /screenshot - Reply to video to take a screenshot\n"
        "• /rename [new_name] - Reply to file to rename it\n"
        "• /merge - Reply to multiple videos to join them\n"
        "• /trim [start] [duration] - Trim video (Ex: /trim 00:00:10 20)"
    )
    await message.reply_text(text)

# --- COMPRESS VIDEO ---
@app.on_message(filters.command(["compress"]))
async def compress(client, message):
    if not message.reply_to_message or not (message.reply_to_message.video or message.reply_to_message.document):
        return await message.reply_text("❌ Please reply to a video file.")
    
    msg = await message.reply_text("📥 **Downloading...**")
    c_time = time.time()
    
    try:
        file_path = await client.download_media(
            message.reply_to_message,
            progress=progress_for_pyrogram,
            progress_args=("📥 Downloading...", msg, c_time, "video.mp4")
        )
        
        out_file = f"compressed_{c_time}.mp4"
        await msg.edit("🗜️ **Compressing... (Ultrafast Mode)**")

        # FFmpeg Command (Ultrafast for Koyeb)
        cmd = [
            "ffmpeg", "-i", file_path, 
            "-c:v", "libx264", "-preset", "ultrafast", "-crf", "30",
            "-c:a", "copy", out_file, "-y"
        ]
        
        process = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        await process.communicate()

        if os.path.exists(out_file):
            await msg.edit("📤 **Uploading...**")
            await client.send_document(
                chat_id=message.chat.id,
                document=out_file,
                caption="✅ **Compressed Successfully!**",
                progress=progress_for_pyrogram,
                progress_args=("📤 Uploading...", msg, time.time(), out_file)
            )
            os.remove(out_file)
        else:
            await msg.edit("❌ Compression Failed.")
        
        if os.path.exists(file_path): os.remove(file_path)

    except Exception as e:
        await msg.edit(f"❌ Error: {e}")

# --- EXTRACT AUDIO ---
@app.on_message(filters.command(["extract_audio", "audio"]))
async def extract_audio(client, message):
    if not message.reply_to_message or not (message.reply_to_message.video or message.reply_to_message.document):
        return await message.reply_text("❌ Reply to a video.")
        
    msg = await message.reply_text("📥 **Downloading...**")
    c_time = time.time()
    
    vid_path = await client.download_media(
        message.reply_to_message,
        progress=progress_for_pyrogram,
        progress_args=("📥 Downloading...", msg, c_time, "video.mp4")
    )
    
    out_audio = f"audio_{c_time}.mp3"
    await msg.edit("🎵 **Extracting Audio...**")
    
    cmd = ["ffmpeg", "-i", vid_path, "-vn", "-acodec", "libmp3lame", "-q:a", "2", out_audio, "-y"]
    process = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    await process.communicate()
    
    if os.path.exists(out_audio):
        await msg.edit("📤 **Uploading Audio...**")
        await client.send_audio(
            chat_id=message.chat.id,
            audio=out_audio,
            caption="✅ **Audio Extracted**",
            progress=progress_for_pyrogram,
            progress_args=("📤 Uploading...", msg, time.time(), out_audio)
        )
        os.remove(out_audio)
    else:
        await msg.edit("❌ Extraction Failed.")
        
    os.remove(vid_path)

# --- MERGE VIDEOS (FIXED) ---
@app.on_message(filters.command(["merge"]))
async def merge(client, message):
    user_id = message.from_user.id
    
    # 1. ADD TO QUEUE
    if message.reply_to_message:
        media = message.reply_to_message.video or message.reply_to_message.document
        if not media:
            return await message.reply_text("❌ Please reply to a Video file.")
            
        if user_id not in MERGE_QUEUE:
            MERGE_QUEUE[user_id] = []
            
        MERGE_QUEUE[user_id].append(message.reply_to_message)
        
        await message.reply_text(
            f"✅ **Added to Queue!**\n"
            f"🔢 Total: `{len(MERGE_QUEUE[user_id])}`\n"
            f"ℹ️ Reply to next video or send /merge to start."
        )
        return

    # 2. START MERGING
    if user_id not in MERGE_QUEUE or len(MERGE_QUEUE[user_id]) < 2:
        return await message.reply_text("❌ **Queue Empty!** Reply to at least 2 videos with /merge first.")

    msg = await message.reply_text(f"📥 **Downloading {len(MERGE_QUEUE[user_id])} Videos...**")
    files = []
    
    try:
        for idx, m in enumerate(MERGE_QUEUE[user_id]):
            await msg.edit(f"📥 Downloading Part {idx+1}/{len(MERGE_QUEUE[user_id])}...")
            f = await client.download_media(m, file_name=f"merge_{user_id}_{idx}.mp4")
            files.append(f)
            
        input_txt = f"list_{user_id}.txt"
        with open(input_txt, "w") as f:
            for item in files: f.write(f"file '{item}'\n")
            
        await msg.edit("🔀 **Merging Videos...**")
        out_vid = f"merged_{user_id}.mp4"
        
        cmd = [
            "ffmpeg", "-f", "concat", "-safe", "0", "-i", input_txt,
            "-c:v", "libx264", "-preset", "ultrafast", "-crf", "28",
            "-c:a", "aac", out_vid, "-y"
        ]
        
        process = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        stdout, stderr = await process.communicate()
        
        if os.path.exists(out_vid):
            await msg.edit("📤 **Uploading Merged Video...**")
            await client.send_video(
                chat_id=message.chat.id,
                video=out_vid,
                caption=f"✅ **Merged {len(files)} Videos**",
                progress=progress_for_pyrogram,
                progress_args=("📤 Uploading...", msg, time.time(), out_vid)
            )
            os.remove(out_vid)
        else:
            await msg.edit(f"❌ Merge Failed!\n`{stderr.decode()[:300]}`")
            
    except Exception as e:
        await msg.edit(f"❌ Error: {e}")
    
    # Cleanup
    if os.path.exists(f"list_{user_id}.txt"): os.remove(f"list_{user_id}.txt")
    for f in files:
        if os.path.exists(f): os.remove(f)
    if user_id in MERGE_QUEUE: del MERGE_QUEUE[user_id]

# --- RENAME FILE ---
@app.on_message(filters.command(["rename"]))
async def rename(client, message):
    if not message.reply_to_message:
        return await message.reply_text("❌ Reply to a file.")
    
    if len(message.command) < 2:
        return await message.reply_text("❌ Usage: /rename new_name.ext")
        
    new_name = message.text.split(None, 1)[1]
    msg = await message.reply_text("📥 **Downloading...**")
    
    file_path = await client.download_media(
        message.reply_to_message, 
        progress=progress_for_pyrogram,
        progress_args=("📥 Downloading...", msg, time.time(), "file")
    )
    
    await msg.edit("📤 **Uploading...**")
    await client.send_document(
        chat_id=message.chat.id,
        document=file_path,
        file_name=new_name,
        caption=f"✅ **Renamed to:** `{new_name}`",
        progress=progress_for_pyrogram,
        progress_args=("📤 Uploading...", msg, time.time(), new_name)
    )
    os.remove(file_path)

# --- SCREENSHOT ---
@app.on_message(filters.command(["screenshot", "ss"]))
async def screenshot(client, message):
    if not message.reply_to_message or not (message.reply_to_message.video or message.reply_to_message.document):
        return await message.reply_text("❌ Reply to a video.")
        
    msg = await message.reply_text("📥 **Downloading...**")
    c_time = time.time()
    
    file_path = await client.download_media(
        message.reply_to_message, 
        progress=progress_for_pyrogram,
        progress_args=("📥 Downloading...", msg, c_time, "video.mp4")
    )
    
    out_img = f"ss_{c_time}.jpg"
    await msg.edit("📸 **Taking Screenshot...**")
    
    cmd = ["ffmpeg", "-ss", "00:00:05", "-i", file_path, "-vframes", "1", "-q:v", "2", out_img, "-y"]
    process = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    await process.communicate()
    
    if os.path.exists(out_img):
        await msg.edit("📤 **Uploading...**")
        await client.send_photo(
            chat_id=message.chat.id,
            photo=out_img,
            caption="✅ **Screenshot Taken**"
        )
        os.remove(out_img)
    else:
        await msg.edit("❌ Screenshot Failed.")
    os.remove(file_path)

print("🤖 Bot Started!")
app.run()
    
