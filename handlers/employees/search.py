# handlers/employees/search.py
"""
Поиск сотрудников по ФИО.
"""

from aiogram import Router, F, types

from services.user_service import get_user_by_tag
from services.employee_service import search_employees_by_full_name, get_employee_detailed_status
from keyboards import back_to_main_kb
from callbacks import MainMenuCallback

router = Router()


@router.callback_query(F.data == MainMenuCallback.SEARCH_EMPLOYEES)
async def start_employee_search(callback: types.CallbackQuery):
    telegram_tag = f"@{callback.from_user.username}"
    user = get_user_by_tag(telegram_tag)
    if not user or user[1] != "supervisor":
        await callback.message.edit_text("❌ Доступ запрещён.")
        await callback.answer()
        return

    await callback.message.edit_text(
        "Введите ФИО сотрудника (можно часть имени):",
        reply_markup=back_to_main_kb()
    )
    await callback.answer()


@router.message(F.text)
async def handle_employee_search(message: types.Message):
    # Проверка роли
    telegram_tag = f"@{message.from_user.username}"
    user = get_user_by_tag(telegram_tag)
    if not user or user[1] != "supervisor":
        await message.answer("❌ Доступ запрещён.", reply_markup=back_to_main_kb())
        return

    query = message.text.strip()
    if len(query) < 2:
        await message.answer("Введите минимум 2 символа.", reply_markup=back_to_main_kb())
        return

    employees = search_employees_by_full_name(query)
    if not employees:
        await message.answer("Сотрудники не найдены.", reply_markup=back_to_main_kb())
        return

    lines = ["📋 Найденные сотрудники:\n"]
    for emp in employees:
        detailed_status = get_employee_detailed_status(emp["telegram_tag"])
        lines.append(f"• {emp['full_name']} ({emp['telegram_tag']})\n  {detailed_status}")

    await message.answer("\n\n".join(lines), reply_markup=back_to_main_kb())