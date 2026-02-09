import os
import time
import asyncio
from aiohttp import web  # Koyeb Health Check ke liye
from pyrogram import Client, filters, idle
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# Progress Bar Import
from progress import progress_for_pyrogram

# --- CONFIGURATION ---
API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")
# Port environment variable se lenge (default 8000)
PORT = int(os.environ.get("PORT", 8000))

# --- CLIENT SETUP ---
app = Client(
    "my_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    workers=4, 
    max_concurrent_transmissions=4
)

MERGE_QUEUE = {}

# --- WEB SERVER FOR KOYEB HEALTH CHECK ---
async def health_check_server():
    async def handle_ping(request):
        return web.Response(text="Bot is Running correctly!")
    
    web_app = web.Application()
    web_app.router.add_get("/", handle_ping)
    
    runner = web.AppRunner(web_app)
    await runner.setup()
    # 0.0.0.0 par bind karna zaroori hai Koyeb ke liye
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    print(f"✅ Web Server started on Port {PORT}")

# --- BOT COMMANDS ---

@app.on_message(filters.command(["start"]))
async def start(client, message):
    await message.reply_text(
        f"👋 Hello {message.from_user.mention}!\n\n"
        "I am a **Video Tool Bot** active on Koyeb 🟢.\n"
        "Use /help to see commands.",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("Developer", url="https://t.me/USER_AYUSH")]]
        )
    )

@app.on_message(filters.command(["help"]))
async def help_command(client, message):
    text = (
        "🛠 **Available Commands:**\n\n"
        "• /compress - Reply to video (Fast)\n"
        "• /extract_audio - Get MP3\n"
        "• /screenshot - Take screenshot\n"
        "• /rename [name] - Rename file\n"
        "• /merge - Merge multiple videos"
    )
    await message.reply_text(text)

@app.on_message(filters.command(["compress"]))
async def compress(client, message):
    if not message.reply_to_message or not (message.reply_to_message.video or message.reply_to_message.document):
        return await message.reply_text("❌ Reply to a video file.")
    
    msg = await message.reply_text("📥 **Downloading...**")
    c_time = time.time()
    
    try:
        file_path = await client.download_media(
            message.reply_to_message,
            progress=progress_for_pyrogram,
            progress_args=("📥 Downloading...", msg, c_time, "video.mp4")
        )
        out_file = f"compressed_{c_time}.mp4"
        await msg.edit("🗜️ **Compressing...**")

        cmd = [
            "ffmpeg", "-i", file_path, 
            "-c:v", "libx264", "-preset", "ultrafast", "-crf", "30",
            "-c:a", "copy", out_file, "-y"
        ]
        process = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        await process.communicate()

        if os.path.exists(out_file):
            await msg.edit("📤 **Uploading...**")
            await client.send_document(
                chat_id=message.chat.id,
                document=out_file,
                caption="✅ **Done!**",
                progress=progress_for_pyrogram,
                progress_args=("📤 Uploading...", msg, time.time(), out_file)
            )
            os.remove(out_file)
        else:
            await msg.edit("❌ Failed.")
        if os.path.exists(file_path): os.remove(file_path)

    except Exception as e:
        await msg.edit(f"❌ Error: {e}")

@app.on_message(filters.command(["extract_audio", "audio"]))
async def extract_audio(client, message):
    if not message.reply_to_message: return await message.reply_text("❌ Reply to video.")
    msg = await message.reply_text("📥 **Downloading...**")
    c_time = time.time()
    vid = await client.download_media(message.reply_to_message, progress=progress_for_pyrogram, progress_args=("📥 DL...", msg, c_time, "vid.mp4"))
    out = f"aud_{c_time}.mp3"
    await msg.edit("🎵 **Extracting...**")
    await (await asyncio.create_subprocess_exec("ffmpeg", "-i", vid, "-vn", "-acodec", "libmp3lame", "-q:a", "2", out, "-y", stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)).communicate()
    if os.path.exists(out):
        await msg.edit("📤 **Uploading...**")
        await client.send_audio(chat_id=message.chat.id, audio=out, caption="✅ Audio", progress=progress_for_pyrogram, progress_args=("📤 UP...", msg, time.time(), out))
        os.remove(out)
    else: await msg.edit("❌ Fail")
    os.remove(vid)

@app.on_message(filters.command(["screenshot", "ss"]))
async def ss(client, message):
    if not message.reply_to_message: return await message.reply_text("❌ Reply to video.")
    msg = await message.reply_text("📥 **Downloading...**")
    vid = await client.download_media(message.reply_to_message)
    out = f"ss_{time.time()}.jpg"
    await msg.edit("📸 **Taking SS...**")
    await (await asyncio.create_subprocess_exec("ffmpeg", "-ss", "00:00:05", "-i", vid, "-vframes", "1", "-q:v", "2", out, "-y", stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)).communicate()
    if os.path.exists(out):
        await client.send_photo(message.chat.id, photo=out, caption="✅ Screenshot")
        os.remove(out)
        await msg.delete()
    else: await msg.edit("❌ Fail")
    os.remove(vid)

@app.on_message(filters.command(["merge"]))
async def merge(client, message):
    uid = message.from_user.id
    if message.reply_to_message:
        if uid not in MERGE_QUEUE: MERGE_QUEUE[uid] = []
        MERGE_QUEUE[uid].append(message.reply_to_message)
        await message.reply_text(f"✅ Added! Total: {len(MERGE_QUEUE[uid])}")
        return
    if uid not in MERGE_QUEUE or len(MERGE_QUEUE[uid]) < 2:
        return await message.reply_text("❌ Reply to 2+ videos first.")
    
    msg = await message.reply_text("📥 **Processing...**")
    files = []
    try:
        for i, m in enumerate(MERGE_QUEUE[uid]):
            files.append(await client.download_media(m, file_name=f"m_{uid}_{i}.mp4"))
        with open(f"list_{uid}.txt", "w") as f:
            for x in files: f.write(f"file '{x}'\n")
        out = f"final_{uid}.mp4"
        await msg.edit("🔀 **Merging...**")
        await (await asyncio.create_subprocess_exec("ffmpeg", "-f", "concat", "-safe", "0", "-i", f"list_{uid}.txt", "-c", "copy", out, "-y", stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)).communicate()
        if os.path.exists(out):
            await msg.edit("📤 **Uploading...**")
            await client.send_video(message.chat.id, video=out, caption="✅ Merged", progress=progress_for_pyrogram, progress_args=("📤 UP...", msg, time.time(), out))
            os.remove(out)
        else: await msg.edit("❌ Merge Failed (Codec Mismatch?)")
    except Exception as e: await msg.edit(f"Error: {e}")
    if os.path.exists(f"list_{uid}.txt"): os.remove(f"list_{uid}.txt")
    for f in files: 
        if os.path.exists(f): os.remove(f)
    if uid in MERGE_QUEUE: del MERGE_QUEUE[uid]

@app.on_message(filters.command(["rename"]))
async def ren(client, message):
    if not message.reply_to_message or len(message.command) < 2: return await message.reply_text("Usage: /rename new.ext")
    new_name = message.text.split(None, 1)[1]
    msg = await message.reply_text("📥 **Downloading...**")
    path = await client.download_media(message.reply_to_message, progress=progress_for_pyrogram, progress_args=("📥...", msg, time.time(), "file"))
    await msg.edit("📤 **Uploading...**")
    await client.send_document(message.chat.id, document=path, file_name=new_name, caption=f"✅ {new_name}", progress=progress_for_pyrogram, progress_args=("📤...", msg, time.time(), new_name))
    os.remove(path)

# --- MAIN EXECUTION ---
async def main():
    # 1. Start Web Server (Fix for Koyeb Health Check)
    await health_check_server()
    
    # 2. Start Bot
    print("🤖 Starting Bot...")
    await app.start()
    print("✅ Bot Started & Listening on Port 8000")
    
    # 3. Keep running
    await idle()
    await app.stop()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
            
