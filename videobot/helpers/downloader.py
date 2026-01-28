import yt_dlp
import asyncio

async def download_url(url, download_path):
    opts = {
        'format': 'best',
        'outtmpl': f'{download_path}/%(title)s.%(ext)s',
        'quiet': True,
    }
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return ydl.prepare_filename(info)
      
