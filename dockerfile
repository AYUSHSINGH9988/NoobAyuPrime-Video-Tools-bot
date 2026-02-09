FROM python:3.9-slim

# Install FFmpeg, 7-Zip, and ImageMagick (Required for Watermark/Edit)
RUN apt-get update && \
    apt-get install -y ffmpeg p7zip-full mediainfo git && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . .
RUN pip install -r requirements.txt

CMD ["python", "main.py"]
