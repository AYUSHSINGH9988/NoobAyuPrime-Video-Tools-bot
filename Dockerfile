# Python ka base version
FROM python:3.10-slim-buster

# 1. System Updates aur FFmpeg install karna
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    && rm -rf /var/lib/apt/lists/*

# 2. Working Directory set karna
WORKDIR /app

# 3. Saari files copy karna
COPY . .

# 4. Requirements install karna
RUN pip3 install --no-cache-dir -r requirements.txt

# 5. Bot start karna
CMD ["python3", "main.py"]
