# config.py
import os
from dotenv import load_dotenv

# Загрузить переменные окружения из файла .env в текущей директории
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
API_BASE_URL = os.getenv("API_BASE_URL")
REDIS_DSN = os.getenv("REDIS_DSN")
