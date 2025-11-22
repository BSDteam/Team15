from aiogram import Bot, Dispatcher, html
import psycopg2


BOT_TOKEN = "8325960245:AAH-1BCzV75nRQejyv_g68tC_3JDz8-QQbA"
bd_conn = psycopg2.connect(host="EtherealDream-MateBook.local", database="rus_al_shifts", user="postgres", password="MySecret123!")