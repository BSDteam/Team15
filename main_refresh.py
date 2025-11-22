from aiogram import Router, F
from aiogram.types import Message
import psycopg2
from datetime import datetime
from inline_kbds import MainMenuEmployee
from config import bd_conn

router = Router()

@router.message(F.text == "Обновить информацию")
async def handle_refresh_info(message: Message):
    user_telegram_id = message.from_user.id
    now = datetime.now()

    cur = bd_conn.cursor()

    # 1. Получение данных пользователя
    cur.execute("SELECT id, full_name, role FROM users WHERE telegram_id = %s", (user_telegram_id,))
    user_data = cur.fetchone()

    if not user_data:
        await message.answer("Ошибка: Пользователь не найден в системе.")
        cur.close()
        return

    telegram_tag, full_name, role, status = user_data

    # 2. Подсчет предстоящих смен
    cur.execute("""
        SELECT COUNT(s.id) 
        FROM shifts s 
        JOIN events e ON s.event_id = e.id 
        WHERE s.end_time >= %s 
        AND (s.user_id = %s OR e.supervisor_user_id = %s)
    """, (now, telegram_tag, telegram_tag))

    upcoming_shifts_count = cur.fetchone()[0]

    # 3. Форматирование ответа
    first_name = full_name.split()[0] if full_name else "Пользователь"
    role_display = "Начальник" if role == 'supervisor' else "Сотрудник"

    output_text = (
        f"Добро пожаловать, *{first_name}*!\n\n"
        f"Ваша должность: *{role_display}*\n"
        f"Количество предстоящих (незавершенных) смен: *{upcoming_shifts_count}*\n"
    )

    await message.answer(
        output_text,
        parse_mode="MarkdownV2",
        reply_markup=MainMenuEmployee()
    )

    cur.close()