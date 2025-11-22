from aiogram import Bot, Dispatcher, html
import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()


BOT_TOKEN = os.getenv("BOT_TOKEN")
bd_conn = psycopg2.connect(host=os.getenv("DB_HOST"),
                           database=os.getenv("DB_NAME"),
                           user=os.getenv("DB_USER"),
                           password=os.getenv("DB_PASS"))



