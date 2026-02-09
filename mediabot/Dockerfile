FROM python:3.9-slim

# Install FFmpeg, 7-Zip, and required system tools
RUN apt-get update && \
    apt-get install -y ffmpeg p7zip-full aria2 git && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "main.py"]
