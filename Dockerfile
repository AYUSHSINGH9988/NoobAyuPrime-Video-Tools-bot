# Full Python version
FROM python:3.10

WORKDIR /app

# 1. System Updates aur FFmpeg install
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    && rm -rf /var/lib/apt/lists/*

# 2. Saari files copy karna
COPY . .

# --- IMPORTANT CHANGE ---
# Hum bot ko bata rahe hain ki files 'videobot' folder ke andar hain
WORKDIR /app/videobot

# 3. Requirements install karna (Ab ye folder ke andar dhoondega)
RUN pip3 install --no-cache-dir -r requirements.txt

# 4. Bot start karna
CMD ["python3", "main.py"]

