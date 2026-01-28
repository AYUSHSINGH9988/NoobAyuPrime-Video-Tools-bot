import asyncio
import os

async def generate_thumbnail(video_path, output_path):
    cmd = [
        "ffmpeg", "-i", video_path, "-ss", "00:00:02", 
        "-vframes", "1", output_path
    ]
    process = await asyncio.create_subprocess_exec(*cmd)
    await process.communicate()
    return output_path if os.path.exists(output_path) else None

async def compress_video(input_path, output_path):
    cmd = [
        "ffmpeg", "-i", input_path, 
        "-c:v", "libx265", "-crf", "28", "-preset", "fast",
        "-c:a", "copy", output_path
    ]
    process = await asyncio.create_subprocess_exec(*cmd)
    await process.communicate()
    return output_path

async def extract_audio(video_path, output_path):
    cmd = ["ffmpeg", "-i", video_path, "-vn", "-acodec", "libmp3lame", output_path]
    process = await asyncio.create_subprocess_exec(*cmd)
    await process.communicate()
    return output_path

async def trim_video(video_path, output_path, start_time, end_time):
    cmd = [
        "ffmpeg", "-i", video_path, "-ss", start_time, "-to", end_time,
        "-c", "copy", output_path
    ]
    process = await asyncio.create_subprocess_exec(*cmd)
    await process.communicate()
    return output_path

async def merge_av(video_path, audio_path, output_path):
    cmd = [
        "ffmpeg", "-i", video_path, "-i", audio_path,
        "-c:v", "copy", "-c:a", "aac", "-map", "0:v:0", "-map", "1:a:0",
        "-shortest", output_path
    ]
    process = await asyncio.create_subprocess_exec(*cmd)
    await process.communicate()
    return output_path

async def join_videos(video_list, output_path):
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

async def add_watermark(video_path, image_path, output_path):
    # Logo ko top-left (10:10) par lagata hai
    cmd = [
        "ffmpeg", "-i", video_path, "-i", image_path,
        "-filter_complex", "overlay=10:10",
        "-c:a", "copy", output_path
    ]
    process = await asyncio.create_subprocess_exec(*cmd)
    await process.communicate()
    return output_path

async def extract_subtitle(video_path, output_path):
    # Video se pehla subtitle track nikalta hai
    cmd = ["ffmpeg", "-i", video_path, "-map", "0:s:0", output_path]
    process = await asyncio.create_subprocess_exec(*cmd)
    await process.communicate()
    return output_path

async def add_subtitle(video_path, sub_path, output_path):
    # Video me subtitle add karta hai (Softsub - Fast)
    cmd = [
        "ffmpeg", "-i", video_path, "-i", sub_path,
        "-c", "copy", "-map", "0", "-map", "1",
        "-metadata:s:s:0", "language=eng", output_path
    ]
    process = await asyncio.create_subprocess_exec(*cmd)
    await process.communicate()
    return output_path
  
