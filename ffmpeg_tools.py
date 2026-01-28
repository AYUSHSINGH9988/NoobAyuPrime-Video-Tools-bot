import asyncio
import os
import subprocess

async def generate_thumbnail(video_path, output_path):
    # Generates a screenshot at 00:00:02
    cmd = [
        "ffmpeg", "-i", video_path, "-ss", "00:00:02", 
        "-vframes", "1", output_path
    ]
    process = await asyncio.create_subprocess_exec(*cmd)
    await process.communicate()
    return output_path if os.path.exists(output_path) else None

async def compress_video(input_path, output_path):
    # Encodes to HEVC (H.265) for compression
    cmd = [
        "ffmpeg", "-i", input_path, 
        "-c:v", "libx265", "-crf", "28", "-preset", "fast",
        "-c:a", "copy", output_path
    ]
    process = await asyncio.create_subprocess_exec(*cmd)
    await process.communicate()
    return output_path

async def add_watermark(video_path, watermark_path, output_path):
    # Adds watermark to top-left
    cmd = [
        "ffmpeg", "-i", video_path, "-i", watermark_path,
        "-filter_complex", "overlay=10:10", output_path
    ]
    process = await asyncio.create_subprocess_exec(*cmd)
    await process.communicate()
    return output_path

async def extract_audio(video_path, output_path):
    cmd = ["ffmpeg", "-i", video_path, "-vn", "-acodec", "libmp3lame", output_path]
    process = await asyncio.create_subprocess_exec(*cmd)
    await process.communicate()
    return output_path
  
