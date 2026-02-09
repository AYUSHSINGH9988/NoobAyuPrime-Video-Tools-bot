FROM python:3.9-slim

# Install FFmpeg, 7-Zip, Aria2 (System Tools)
RUN apt-get update && \
    apt-get install -y ffmpeg p7zip-full aria2 git && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY . .

# Install Python Libraries
RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "main.py"]
