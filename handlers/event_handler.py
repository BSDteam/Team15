from datetime import datetime

from aiogram import Router, F
from aiogram.types import Message
from aiogram.methods import SendMessage
from config import bd_conn

router = Router()

@router.message(F.not_contains('/'))
async def cmd_not_contains(message: Message):
    if message.reply_to_message:
        cur = bd_conn.cursor()
        SQL = 'SELECT supervisor_telegram_tag FROM employee_supervisor WHERE employee_telegram_tag = %s'
        cur.execute(SQL, (f'@{message.from_user.username}',))
        supervisor_tag = cur.fetchone()
        SQL = 'SELECT id FROM users WHERE telegram_tag = %s'
        cur.execute(SQL, (supervisor_tag,))
        person = cur.fetchone()
        SQL = 'INSERT INTO notifications (sender_telegram_tag, recipient_telegram_tag, message) VALUES (%s, %s, %s)'
        cur.execute(SQL, (f'@{message.from_user.username}', supervisor_tag[0], message.text))
        cur.close()
        return SendMessage(chat_id=person[0], text=message.text)
