# Bazaviy imijni aniqlash (Python 3.9 versiyasi misolida)
FROM python:3.9-slim

# Ishchi papkani belgilash
WORKDIR /app

# Loyihadagi barcha fayllarni konteynerga nusxalash
COPY . /app

# Zarur kutubxonalarni o‘rnatish
RUN pip install --no-cache-dir -r requirements.txt

# Ilovani ishga tushirish (asosiy fayl nomini o‘zgartiring)
CMD ["python", "anketa_bot_tizim.py"]
