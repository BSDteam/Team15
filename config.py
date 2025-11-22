# config.py
import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не задан")

# Параметры БД — читаем из переменных окружения
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "database": os.getenv("DB_NAME", "myapp_db"),
    "user": os.getenv("DB_USER", "myapp_user"),
    "password": os.getenv("DB_PASSWORD", "secure_password"),
    "port": os.getenv("DB_PORT", "5432"),
}