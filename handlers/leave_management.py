# handlers/leave_management.py
# Не понадобится
import logging
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery, Message

from config import bd_conn
from inline_kbds import vacations_list

router = Router()

class LeaveManagement(StatesGroup):
    WaitingForTag = State()
    ViewingLeaves = State()
    CreatingLeave = State()
    CancelingLeave = State()


# Функция
def get_main_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=vacations_list
    )

def get_cancel_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[vacations_list[-1]]
    )

@router.callback_query(F.data == "main_view_vacation")
async def start_leave_management_from_menu(callback: CallbackQuery, state: FSMContext):
    # Проверяем, что пользователь — начальник
    cur = bd_conn.cursor()
    tag = "@" + callback.from_user.username
    cur.execute("SELECT role FROM users WHERE telegram_tag = %s", (tag,))
    user = cur.fetchone()
    cur.close()

    if not user or user[0] != "supervisor":
        await callback.answer("❌ У вас нет прав на управление отпусками.", show_alert=True)
        return

    await callback.answer()
    await callback.message.answer("Введите @tag сотрудника (например, @ivan):")
    await state.set_state(LeaveManagement.WaitingForTag)

@router.message(LeaveManagement.WaitingForTag)
async def show_leaves(message: Message, state: FSMContext):
    tag = message.text.strip()
    if not tag.startswith('@'):
        await message.answer("❌ Введите корректный @tag (начинается с @).")
        return

    cur = bd_conn.cursor()
    try:
        cur.execute("SELECT full_name FROM users WHERE telegram_tag = %s", (tag,))
        user = cur.fetchone()
        if not user:
            await message.answer(f"Сотрудник с тегом {tag} не найден.")
            await state.clear()
            return

        cur.execute("""
            SELECT id, start_date, end_date, type
            FROM leave_records
            WHERE user_telegram_tag = %s
            ORDER BY start_date DESC
        """, (tag,))
        leaves = cur.fetchall()

        if leaves:
            text = f"Отпуска сотрудника {user[0]} ({tag}):\n"
            for lid, start, end, typ in leaves:
                text += f"#{lid}: {start} – {end} ({typ})\n"
        else:
            text = f"У сотрудника {user[0]} ({tag}) нет отпусков."

        await message.answer(text, reply_markup=get_main_keyboard())
        await state.update_data(tag=tag, full_name=user[0])
        await state.set_state(LeaveManagement.ViewingLeaves)

    except Exception as e:
        await message.answer(f"❌ Ошибка БД: {e}")
    finally:
        cur.close()

@router.callback_query(LeaveManagement.ViewingLeaves, F.data == "action:create_leave")
async def start_create_leave(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.answer(
        "📅 Введите период отпуска в формате:\n"
        "`дд.мм.гггг - дд.мм.гггг`\n"
        "Пример: `22.11.2025 - 30.11.2025`\n\n"
        "Чтобы отменить — введите слово **отмена**."
        # ❗ НЕТ reply_markup=get_cancel_keyboard() здесь, если используешь инлайн — не нужна клавиатура внизу
    )
    await state.set_state(LeaveManagement.CreatingLeave)

@router.message(LeaveManagement.CreatingLeave)
async def create_leave(message: Message, state: FSMContext):
    text = message.text.strip()

    if text.lower() == "отмена":
        await message.answer("Операция отменена.", reply_markup=get_main_keyboard())
        await state.set_state(LeaveManagement.ViewingLeaves)
        return

    # Разбор дат
    parts = text.split(' - ')
    if len(parts) != 2:
        await message.answer("❌ Неверный формат. Используйте: дд.мм.гггг - дд.мм.гггг")
        return

    try:
        from datetime import datetime
        start = datetime.strptime(parts[0].strip(), '%d.%m.%Y').date()
        end = datetime.strptime(parts[1].strip(), '%d.%m.%Y').date()
        if start > end:
            raise ValueError("Дата начала не может быть позже даты окончания.")
    except Exception as e:
        await message.answer(f"📅 Ошибка в датах:\n{e}")
        return

    data = await state.get_data()
    tag = data['tag']

    cur = bd_conn.cursor()
    try:
        cur.execute("""
            INSERT INTO leave_records (user_telegram_tag, start_date, end_date, type)
            VALUES (%s, %s, %s, 'vacation')
        """, (tag, start, end))

        cur.execute("""
            UPDATE users SET status = 'on_vacation'
            WHERE telegram_tag = %s
        """, (tag,))
        bd_conn.commit()

        await message.answer("✅ Отпуск успешно назначен. Статус обновлён.", reply_markup=get_main_keyboard())
        await state.set_state(LeaveManagement.ViewingLeaves)

    except Exception as e:
        bd_conn.rollback()
        await message.answer(f"❌ Не удалось создать отпуск: {e}")
    finally:
        cur.close()

@router.message(LeaveManagement.ViewingLeaves, F.text == "Отменить отпуск")
async def start_cancel_leave(message: Message, state: FSMContext):
    """
    ToDo: Поменять обёртку и логику!
    :param message:
    :param state:
    :return:
    """
    await message.answer("Введите ID отпуска для отмены (например, 2):")
    await state.set_state(LeaveManagement.CancelingLeave)

@router.message(LeaveManagement.CancelingLeave)
async def cancel_leave(message: Message, state: FSMContext):
    try:
        leave_id = int(message.text.strip())
    except ValueError:
        await message.answer("❌ Введите целое число (ID отпуска).")
        return

    data = await state.get_data()
    tag = data['tag']

    cur = bd_conn.cursor()
    try:
        cur.execute("""
            DELETE FROM leave_records
            WHERE id = %s AND user_telegram_tag = %s
        """, (leave_id, tag))
        deleted = cur.rowcount

        if deleted > 0:
            cur.execute("""
                UPDATE users SET status = 'available'
                WHERE telegram_tag = %s
            """, (tag,))
            bd_conn.commit()
            await message.answer("✅ Отпуск отменён. Статус сотрудника обновлён.")
        else:
            await message.answer("❌ Отпуск с таким ID не найден или не принадлежит сотруднику.")

        await message.answer("Возврат в меню отпусков:", reply_markup=get_main_keyboard())
        await state.set_state(LeaveManagement.ViewingLeaves)

    except Exception as e:
        bd_conn.rollback()
        await message.answer(f"❌ Ошибка при отмене отпуска: {e}")
    finally:
        cur.close()

@router.message(LeaveManagement.ViewingLeaves, F.text == "Вернуться")
async def back_to_main(message: Message, state: FSMContext):
    await message.answer("Вы вернулись в главное меню.")
    await state.clear()