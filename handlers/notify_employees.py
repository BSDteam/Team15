# Не понадобится
import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from config import bd_conn

# Роутер
notify_router = Router()


class NotifyEmployee(StatesGroup):
    SelectingEmployee = State()
    EnteringMessage = State()


def make_employee_keyboard(employees):
    """employees = [(full_name, telegram_tag, id_telegram), ...]"""
    buttons = []
    for full_name, tag, id_telegram in employees:
        buttons.append([InlineKeyboardButton(
            text=f"{full_name} ({tag})",
            callback_data=f"notify_emp:{id_telegram}"
        )])
    buttons.append([InlineKeyboardButton(text="❌ Отмена", callback_data="notify_cancel")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


@notify_router.callback_query(F.data == "search_employees")
async def show_employees_for_notify(callback: CallbackQuery, state: FSMContext):
    supervisor_tag = "@" + (callback.from_user.username or str(callback.from_user.id))

    cur = bd_conn.cursor()
    try:
        # Проверяем роль
        cur.execute("SELECT role FROM users WHERE telegram_tag = %s", (supervisor_tag,))
        row = cur.fetchone()
        if not row or row[0] != 'supervisor':
            await callback.answer("❌ Только для начальников.", show_alert=True)
            return

        # Получаем подчинённых с id_telegram
        cur.execute("""
            SELECT u.full_name, u.telegram_tag, u.id_telegram
            FROM employee_supervisor es
            JOIN users u ON u.telegram_tag = es.employee_telegram_tag
            WHERE es.supervisor_telegram_tag = %s AND u.id_telegram != 0
            ORDER BY u.full_name
        """, (supervisor_tag,))
        employees = cur.fetchall()

        if not employees:
            await callback.answer()
            await callback.message.answer(
                "У вас нет подчинённых с активным Telegram ID.\n"
                "Сотрудники должны написать боту хотя бы раз."
            )
            return

        await callback.answer()
        await callback.message.answer(
            "Выберите сотрудника для отправки сообщения:",
            reply_markup=make_employee_keyboard(employees)
        )
        await state.set_state(NotifyEmployee.SelectingEmployee)

    except Exception as e:
        logging.exception("Ошибка при загрузке списка сотрудников")
        await callback.answer("❌ Ошибка при загрузке списка.", show_alert=True)
    finally:
        cur.close()


@notify_router.callback_query(NotifyEmployee.SelectingEmployee, F.data.startswith("notify_emp:"))
async def employee_selected(callback: CallbackQuery, state: FSMContext):
    try:
        target_id = int(callback.data.split(":", 1)[1])
    except (ValueError, IndexError):
        await callback.answer("❌ Некорректный ID.", show_alert=True)
        return

    await state.update_data(target_id=target_id)
    await callback.answer()
    await callback.message.answer("Напишите текст сообщения:")
    await state.set_state(NotifyEmployee.EnteringMessage)


@notify_router.callback_query(NotifyEmployee.SelectingEmployee, F.data == "notify_cancel")
async def notify_cancel(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.answer()
    await callback.message.answer("Операция отменена.")


@notify_router.message(NotifyEmployee.EnteringMessage)
async def send_message_to_employee(message: Message, state: FSMContext):
    data = await state.get_data()
    target_id = data.get("target_id")

    if not target_id:
        await message.answer("❌ Ошибка: получатель не выбран.")
        await state.clear()
        return

    try:
        await message.bot.send_message(
            chat_id=target_id,
            text=f"🔔 Вам сообщение от начальника:\n\n{message.text}"
        )
        await message.answer("✅ Сообщение отправлено!")
    except Exception as e:
        logging.exception(f"Не удалось отправить сообщение пользователю {target_id}")
        await message.answer(
            "❌ Не удалось отправить сообщение.\n"
            "Возможно, сотрудник не писал боту или заблокировал его."
        )
    finally:
        await state.clear()