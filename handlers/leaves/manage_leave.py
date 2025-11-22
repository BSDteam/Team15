# handlers/leaves/manage_leave.py
"""
Назначение отпуска/больничного.
"""

import re
from datetime import datetime
from typing import Optional
from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext

from services.user_service import get_user_by_tag
from services.leave_service import create_leave
from states import LeaveManagement
from keyboards import confirm_kb, back_to_main_kb, leave_type_kb
from callbacks import LeaveCallback

router = Router()


def parse_date_range(text: str) -> Optional[tuple[datetime.date, datetime.date]]:
    """Парсит диапазон: ДД.ММ.ГГГГ-ДД.ММ.ГГГГ"""
    if '-' not in text:
        return None
    start_str, end_str = text.split('-', 1)
    try:
        start = datetime.strptime(start_str.strip(), "%d.%m.%Y").date()
        end = datetime.strptime(end_str.strip(), "%d.%m.%Y").date()
        return start, end
    except ValueError:
        return None


@router.callback_query(F.data == LeaveCallback.CREATE)
async def start_create_leave(callback: types.CallbackQuery, state: FSMContext):
    telegram_tag = f"@{callback.from_user.username}"
    user = get_user_by_tag(telegram_tag)
    if not user or user[1] != "supervisor":
        await callback.message.edit_text("❌ Только начальники могут назначать отпуска.")
        await callback.answer()
        return

    await callback.message.edit_text(
        "Введите Telegram-тег сотрудника (например, @ivan):",
        reply_markup=back_to_main_kb()
    )
    await state.set_state(LeaveManagement.choosing_employee)
    await callback.answer()


@router.message(LeaveManagement.choosing_employee)
async def process_employee_tag(message: types.Message, state: FSMContext):
    employee_tag = message.text.strip()
    if not employee_tag.startswith('@'):
        await message.answer("Тег должен начинаться с @. Попробуйте снова:")
        return

    await state.update_data(employee_tag=employee_tag)
    await message.answer(
        "Введите даты отсутствия в формате ДД.ММ.ГГГГ-ДД.ММ.ГГГГ (например, 22.11.2025-01.12.2025):",
        reply_markup=back_to_main_kb()
    )
    await state.set_state(LeaveManagement.choosing_dates)


@router.message(LeaveManagement.choosing_dates)
async def process_dates(message: types.Message, state: FSMContext):
    date_range = parse_date_range(message.text)
    if not date_range:
        await message.answer("Неверный формат. Используйте ДД.ММ.ГГГГ-ДД.ММ.ГГГГ:")
        return

    start_date, end_date = date_range
    await state.update_data(start_date=start_date, end_date=end_date)

    await message.answer(
        "Выберите тип отсутствия:",
        reply_markup=leave_type_kb()
    )
    await state.set_state(LeaveManagement.choosing_type)


@router.callback_query(LeaveManagement.choosing_type)
async def process_leave_type(callback: types.CallbackQuery, state: FSMContext):
    if not callback.data.startswith("leave_type:"):
        await callback.answer("Неверный выбор.")
        return

    leave_type = callback.data.split(":", 1)[1]
    if leave_type not in ("vacation", "sick", "absent"):
        await callback.answer("Неверный тип.")
        return

    await state.update_data(leave_type=leave_type)

    data = await state.get_data()
    start_str = data['start_date'].strftime("%d.%m.%Y")
    end_str = data['end_date'].strftime("%d.%m.%Y")
    type_display = {"vacation": "Отпуск", "sick": "Больничный", "absent": "Прочее отсутствие"}[leave_type]

    await callback.message.edit_text(
        f"Подтвердите создание:\n"
        f"Сотрудник: {data['employee_tag']}\n"
        f"Период: {start_str} – {end_str}\n"
        f"Тип: {type_display}",
        reply_markup=confirm_kb()
    )
    await state.set_state(LeaveManagement.confirm)


@router.callback_query(LeaveManagement.confirm, F.data == "confirm_yes")
async def confirm_leave_creation(callback: types.CallbackQuery, state: FSMContext):
    telegram_tag = f"@{callback.from_user.username}"
    data = await state.get_data()

    success = create_leave(
        employee_tag=data["employee_tag"],
        start_date=data["start_date"],
        end_date=data["end_date"],
        leave_type=data["leave_type"],
        supervisor_tag=telegram_tag
    )

    if success:
        await callback.message.edit_text(
            "✅ Отсутствие успешно назначено!",
            reply_markup=back_to_main_kb()
        )
    else:
        await callback.message.edit_text(
            "❌ Не удалось назначить отсутствие. Возможные причины:\n"
            "• Сотрудник не подчинён вам\n"
            "• Даты пересекаются с существующим отпуском\n"
            "• Некорректные даты",
            reply_markup=back_to_main_kb()
        )

    await state.clear()
    await callback.answer()


@router.callback_query(LeaveManagement.confirm, F.data == "confirm_no")
async def cancel_leave_creation(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Назначение отменено.", reply_markup=back_to_main_kb())
    await callback.answer()