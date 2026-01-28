Here is a professional, high-quality README.md file for your GitHub repository. It includes all the features we added, nice emojis, and clear instructions.
Steps:
 * Create a file named README.md in your folder.
 * Paste the code below into it.
# 🎬 Ultimate Video Tools Bot

<p align="center">
  <img src="https://img.shields.io/badge/Language-Python3-blue?style=flat&logo=python">
  <img src="https://img.shields.io/badge/Library-Pyrogram-orange?style=flat&logo=telegram">
  <img src="https://img.shields.io/badge/Media-FFmpeg-green?style=flat&logo=ffmpeg">
  <img src="https://img.shields.io/badge/Database-MongoDB-green?style=flat&logo=mongodb">
</p>

<p align="center">
  <b>A powerful All-in-One Telegram Bot to manage, edit, compress, and download videos.</b>
</p>

---

## 🌟 Features

This bot is packed with **12+ advanced features** to handle all your video needs directly from Telegram!

### 🎥 Video Editing Tools
- **📉 Fast Compression:** Compress video size using HEVC (H.265) without losing quality.
- **✂️ Video Trimmer:** Cut specific parts of a video easily.
- **📸 Screenshot Generator:** Get a high-quality thumbnail from any video.
- **🎵 Audio Extraction:** Convert Video to MP3 audio.
- **📝 Subtitle Extraction:** Extract embedded soft subtitles (`.srt`).

### 🛠️ Advanced Editing (Reply Based)
- **🖼️ Watermark Adder:** Add your custom logo/photo to any video.
- **📜 Add Subtitles:** Soft-code `.srt` subtitles into video files.
- **🔀 Audio Mixer:** Replace video audio with a custom audio file.
- **🎞️ Video Joiner:** Merge two videos into one.

### 📥 Downloader & Manager
- **🚀 URL Downloader:** Download content from Instagram, YouTube, and direct links.
- **✏️ File Renamer:** Rename any file extension or name.
- **📦 Archive Tools:** Zip and Unzip files easily.

---

## 🤖 Bot Commands

| Feature | Command | Usage |
| :--- | :--- | :--- |
| **Start Bot** | `/start` | Check if bot is online |
| **Compress** | `/compress` | Reply to Video |
| **Extract Audio** | `/extract_audio` | Reply to Video |
| **Extract Subtitle** | `/extract_sub` | Reply to Video |
| **Screenshot** | `/screenshot` | Reply to Video |
| **Trim Video** | `/trim start end` | `/trim 00:01 00:10` (Reply to Video) |
| **Rename File** | `/rename name` | `/rename movie.mkv` (Reply to File) |
| **Zip File** | `/zip` | Reply to any file |
| **Unzip File** | `/unzip` | Reply to a `.zip` file |
| **Add Watermark** | `/watermark` | Reply to Video (Send Photo first) |
| **Add Subtitle** | `/add_sub` | Reply to Video (Send .srt first) |
| **Merge Audio** | `/merge_audio` | Reply to Video (Send Audio first) |
| **Join Videos** | `/merge_videos` | Reply to Video 1 (Send Video 2 first) |

---

## ⚙️ Installation & Deployment

You can deploy this bot on a **VPS**, **Local PC**, or **Heroku**.

### 1️⃣ Prerequisites
- Python 3.9+
- FFmpeg (Essential for video processing)
- MongoDB Database URL
- Telegram API ID & Hash

### 2️⃣ Local / VPS Setup

1. **Clone the Repository:**
   ```bash
   git clone [https://github.com/YourUsername/Video-Tools-Bot.git](https://github.com/YourUsername/Video-Tools-Bot.git)
   cd Video-Tools-Bot

 * Install Dependencies:
   pip3 install -r requirements.txt

 * Install FFmpeg:
   * Ubuntu/Debian: sudo apt install ffmpeg
   * Windows: Download and add to PATH.
 * Configure Variables:
   Open config.py and add your values:
   * API_ID & API_HASH: Get from my.telegram.org
   * BOT_TOKEN: Get from @BotFather
   * MONGO_URL: Get from MongoDB Atlas
   * OWNER_ID: Your Telegram User ID
 * Run the Bot:
   python3 main.py

🚀 Deploy on Heroku
 * Fork this repository.
 * Create a new app on Heroku.
 * Add the following Buildpacks in Settings:
   * heroku/python
   * https://github.com/jonathanong/heroku-buildpack-ffmpeg-latest.git
 * Add Config Vars (API_ID, API_HASH, etc.).
 * Deploy the branch!
📝 Credits
 * Language: Python
 * Framework: Pyrogram
 * Media Engine: FFmpeg
<p align="center">
Made with ❤️ by <b>You</b>
</p>

