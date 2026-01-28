import asyncio
import os

async def generate_thumbnail(video_path, output_path):
    # Screenshot leta hai 2nd second par
    cmd = [
        "ffmpeg", "-i", video_path, "-ss", "00:00:02", 
        "-vframes", "1", output_path
    ]
    process = await asyncio.create_subprocess_exec(*cmd)
    await process.communicate()
    return output_path if os.path.exists(output_path) else None

async def compress_video(input_path, output_path):
    # Video size kam karta hai (HEVC)
    cmd = [
        "ffmpeg", "-i", input_path, 
        "-c:v", "libx265", "-crf", "28", "-preset", "fast",
        "-c:a", "copy", output_path
    ]
    process = await asyncio.create_subprocess_exec(*cmd)
    await process.communicate()
    return output_path

async def extract_audio(video_path, output_path):
    # Audio nikalta hai
    cmd = ["ffmpeg", "-i", video_path, "-vn", "-acodec", "libmp3lame", output_path]
    process = await asyncio.create_subprocess_exec(*cmd)
    await process.communicate()
    return output_path

async def merge_av(video_path, audio_path, output_path):
    # Video aur Audio ko mix karta hai
    cmd = [
        "ffmpeg", "-i", video_path, "-i", audio_path,
        "-c:v", "copy", "-c:a", "aac", "-map", "0:v:0", "-map", "1:a:0",
        "-shortest", output_path
    ]
    process = await asyncio.create_subprocess_exec(*cmd)
    await process.communicate()
    return output_path

async def join_videos(video_list, output_path):
    # 2 Videos ko jodta hai
    input_txt = "input_list.txt"
    with open(input_txt, 'w') as f:
        for video in video_list:
            f.write(f"file '{video}'\n")
    
    cmd = [
        "ffmpeg", "-f", "concat", "-safe", "0", "-i", input_txt,
        "-c", "copy", output_path
    ]
    process = await asyncio.create_subprocess_exec(*cmd)
    await process.communicate()
    
    if os.path.exists(input_txt): os.remove(input_txt)
    return output_path
    
