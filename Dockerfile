FROM python:3.10

WORKDIR /app

RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    && rm -rf /var/lib/apt/lists/*

COPY . .

RUN pip3 install --no-cache-dir -r requirements.txt

WORKDIR /app/videobot

CMD ["python3", "main.py"]


