# handlers/leave_management.py

# Загружаем переменные из .env (DB_HOST, DB_USER и т.д.)
# Важно: файл .env не коммитится в репозиторий — безопасность соблюдена
import os
import psycopg2
from dotenv import load_dotenv
load_dotenv()

# Импорты aiogram для FSM и интерфейса
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton

# Создаём маршрутизатор для этого модуля
router = Router()

# Подключение к БД — синхронное (psycopg2), потому что asyncpg запрещён
def get_db_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASS")
    )

# FSM-состояния: пошаговое управление диалогом с пользователем
class LeaveManagement(StatesGroup):
    WaitingForTag = State()      # 1. Мастер вводит @tag сотрудника
    ViewingLeaves = State()      # 2. Бот показывает отпуска + кнопки действий
    CreatingLeave = State()      # 3. Мастер вводит период отпуска
    CancelingLeave = State()     # 4. Мастер вводит ID отпуска для отмены

# Кнопки для навигации (вместо текстовых команд — улучшает UX)
def get_main_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Назначить отпуск")],
            [KeyboardButton(text="Отменить отпуск")],
            [KeyboardButton(text="Вернуться")]
        ],
        resize_keyboard=True
    )

# Команда /manage_leaves — запускает процесс
@router.message(F.text == "/manage_leaves")
async def start_leave_management(message: Message, state: FSMContext):
    await message.answer("Введите @tag сотрудника (например, @ivan):")
    await state.set_state(LeaveManagement.WaitingForTag)

# Шаг 1: поиск сотрудника по @tag и показ его отпусков
@router.message(LeaveManagement.WaitingForTag)
async def show_leaves(message: Message, state: FSMContext):
    tag = message.text.strip()
    if not tag.startswith('@'):
        await message.answer("Введите корректный @tag (начинается с @)")
        return

    # Запускаем синхронный код в асинхронном контексте (aiogram 3.x требует этого)
    import asyncio
    loop = asyncio.get_event_loop()
    try:
        conn = await loop.run_in_executor(None, get_db_connection)
        cur = conn.cursor()

        # Проверяем, существует ли сотрудник
        cur.execute("SELECT full_name FROM users WHERE telegram_tag = %s", (tag,))
        user = cur.fetchone()
        if not user:
            await message.answer(f"Сотрудник {tag} не найден.")
            await state.clear()
            return

        # Получаем все отпуска этого сотрудника
        cur.execute("""
            SELECT id, start_date, end_date, type
            FROM leave_records
            WHERE user_telegram_tag = %s
            ORDER BY start_date DESC
        """, (tag,))
        leaves = cur.fetchall()

        # Формируем ответ
        if not leaves:
            text = f"У сотрудника {user[0]} ({tag}) нет отпусков."
        else:
            text = f"Отпуска сотрудника {user[0]} ({tag}):\n"
            for lid, start, end, typ in leaves:
                text += f"#{lid}: {start} — {end} ({typ})\n"

        await message.answer(text, reply_markup=get_main_keyboard())
        await state.update_data(tag=tag, full_name=user[0])
        await state.set_state(LeaveManagement.ViewingLeaves)

    except Exception as e:
        await message.answer(f"❌ Ошибка БД: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

# Шаг 2: выбор действия — "Назначить отпуск"
@router.message(LeaveManagement.ViewingLeaves, F.text == "Назначить отпуск")
async def start_create_leave(message: Message, state: FSMContext):
    await message.answer(
        "📅 Введите период отпуска в формате:\n"
        "`дд.мм.гггг - дд.мм.гггг`\n"
        "Пример: `22.11.2025 - 30.11.2025`\n\n"
        "⚠️ Чтобы отменить — введите слово **отмена**.",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="Вернуться")]],
            resize_keyboard=True
        )
    )
    await state.set_state(LeaveManagement.CreatingLeave)

# Шаг 3: сохранение отпуска
@router.message(LeaveManagement.CreatingLeave)
async def create_leave(message: Message, state: FSMContext):
    user_input = message.text.strip()

    # Проверка на отмену
    if user_input.lower() == "отмена":
        await message.answer("Операция отменена.", reply_markup=get_main_keyboard())
        await state.set_state(LeaveManagement.ViewingLeaves)
        return

    # Разделение на две даты
    parts = user_input.split(' - ')
    if len(parts) != 2:
        await message.answer(
            "❌ Неверный формат.\n"
            "Введите период в формате: **дд.мм.гггг - дд.мм.гггг**\n"
            "Пример: `22.11.2025 - 30.11.2025`\n\n"
            "Чтобы отменить — введите слово **отмена**."
        )
        return

    start_str, end_str = parts[0].strip(), parts[1].strip()

    try:
        from datetime import datetime
        start_date = datetime.strptime(start_str, '%d.%m.%Y').date()
        end_date = datetime.strptime(end_str, '%d.%m.%Y').date()
        if start_date > end_date:
            raise ValueError("Дата окончания не может быть раньше даты начала")
    except ValueError as e:
        await message.answer(
            f"❌ Ошибка в датах:\n{e}\n\n"
            "Формат: дд.мм.гггг - дд.мм.гггг\n"
            "Пример: `22.11.2025 - 30.11.2025`\n\n"
            "Чтобы отменить — введите **отмена**."
        )
        return

    # --- Сохранение в БД ---
    data = await state.get_data()
    tag = data['tag']

    import asyncio
    loop = asyncio.get_event_loop()
    try:
        conn = await loop.run_in_executor(None, get_db_connection)
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO leave_records (user_telegram_tag, start_date, end_date, type)
            VALUES (%s, %s, %s, 'vacation')
        """, (tag, start_date, end_date))
        conn.commit()

        cur.execute("""
            UPDATE users SET status = 'on_vacation'
            WHERE telegram_tag = %s
        """, (tag,))
        conn.commit()

        await message.answer("✅ Отпуск успешно назначен. Статус обновлён.", reply_markup=get_main_keyboard())
        await state.set_state(LeaveManagement.ViewingLeaves)

    except Exception as e:
        await message.answer(f"❌ Ошибка при создании отпуска: {e}", reply_markup=get_main_keyboard())
    finally:
        if 'conn' in locals():
            conn.close()

# Шаг 4: отмена отпуска
@router.message(LeaveManagement.ViewingLeaves, F.text == "Отменить отпуск")
async def start_cancel_leave(message: Message, state: FSMContext):
    await message.answer("Введите номер отпуска (ID), который нужно отменить:")
    await state.set_state(LeaveManagement.CancelingLeave)

@router.message(LeaveManagement.CancelingLeave)
async def cancel_leave(message: Message, state: FSMContext):
    try:
        leave_id = int(message.text.strip())
    except ValueError:
        await message.answer("Введите число (ID отпуска).")
        return

    data = await state.get_data()
    tag = data['tag']

    import asyncio
    loop = asyncio.get_event_loop()
    try:
        conn = await loop.run_in_executor(None, get_db_connection)
        cur = conn.cursor()

        # Удаляем запись об отпуске
        cur.execute("""
            DELETE FROM leave_records
            WHERE id = %s AND user_telegram_tag = %s
        """, (leave_id, tag))
        deleted = cur.rowcount
        conn.commit()

        if deleted == 0:
            await message.answer("❌ Отпуск с таким ID не найден или не принадлежит этому сотруднику.")
        else:
            # Возвращаем статус в "доступен"
            cur.execute("""
                UPDATE users SET status = 'available'
                WHERE telegram_tag = %s
            """, (tag,))
            conn.commit()
            await message.answer("✅ Отпуск отменён. Статус сотрудника обновлён.")

        await message.answer("Возврат в меню отпусков:", reply_markup=get_main_keyboard())
        await state.set_state(LeaveManagement.ViewingLeaves)

    except Exception as e:
        await message.answer(f"❌ Ошибка при отмене: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

# Возврат в главное меню
@router.message(LeaveManagement.ViewingLeaves, F.text == "Вернуться")
async def back_to_start(message: Message, state: FSMContext):
    await message.answer("Вы вернулись в главное меню.")
    await state.clear()