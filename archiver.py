import os
import zipfile
import shutil
from pyrogram import Client, filters
from config import Config
from main import user_queue

# Helper to zip a file
def zip_file(input_path, output_path):
    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        zipf.write(input_path, os.path.basename(input_path))
    return output_path

# Helper to unzip
def unzip_file(input_path, output_dir):
    with zipfile.ZipFile(input_path, 'r') as zip_ref:
        zip_ref.extractall(output_dir)
    return output_dir

@Client.on_message(filters.command("zip"))
async def zip_handler(client, message):
    video_msg = user_queue.get(message.from_user.id)
    if not video_msg:
        return await message.reply("Send a file first, then use /zip")

    msg = await message.reply("Downloading file to zip...")
    path = await video_msg.download(Config.DOWNLOAD_DIR)
    
    # Create Output Path
    output_path = f"{path}.zip"
    
    await msg.edit("Zipping file...")
    try:
        zip_file(path, output_path)
        await msg.edit("Uploading Zip archive...")
        await client.send_document(
            chat_id=message.chat.id,
            document=output_path,
            caption="**Here is your Archive!** 🗜"
        )
    except Exception as e:
        await msg.edit(f"Error: {e}")
    finally:
        if os.path.exists(path): os.remove(path)
        if os.path.exists(output_path): os.remove(output_path)

@Client.on_message(filters.command("unzip"))
async def unzip_handler(client, message):
    video_msg = user_queue.get(message.from_user.id)
    if not video_msg:
        return await message.reply("Send a .zip file first, then use /unzip")
        
    msg = await message.reply("Downloading Archive...")
    path = await video_msg.download(Config.DOWNLOAD_DIR)
    extract_dir = f"{Config.DOWNLOAD_DIR}{message.from_user.id}_extracted/"
    
    if not os.path.exists(extract_dir):
        os.makedirs(extract_dir)

    await msg.edit("Extracting...")
    try:
        unzip_file(path, extract_dir)
        
        # Send all extracted files back to user
        files = os.listdir(extract_dir)
        if not files:
            await msg.edit("Archive was empty.")
        else:
            await msg.edit(f"Found {len(files)} files. Uploading...")
            for file in files:
                file_path = os.path.join(extract_dir, file)
                await client.send_document(message.chat.id, document=file_path)
    except Exception as e:
        await msg.edit(f"Error: {e}")
    finally:
        if os.path.exists(path): os.remove(path)
        if os.path.exists(extract_dir): shutil.rmtree(extract_dir)
          
