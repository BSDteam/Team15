# handlers/shifts/create_shift.py
"""
Хендлер создания новой смены.
Доступен только мастерам.
"""

import re
from datetime import datetime
from typing import Optional

from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext

from services.user_service import get_user_by_tag
from services.shift_service import create_shift
from states import CreateShift
from keyboards import confirm_kb, back_to_main_kb
from callbacks import MainMenuCallback

router = Router()


def parse_date(date_str: str) -> Optional[datetime.date]:
    """Парсит дату в формате ДД.ММ.ГГГГ"""
    try:
        return datetime.strptime(date_str.strip(), "%d.%m.%Y").date()
    except ValueError:
        return None


def parse_time(time_str: str) -> Optional[datetime.time]:
    """Парсит время в формате ЧЧ:ММ"""
    try:
        return datetime.strptime(time_str.strip(), "%H:%M").time()
    except ValueError:
        return None


@router.callback_query(F.data == MainMenuCallback.NEW_SHIFT)
async def start_create_shift(callback: types.CallbackQuery, state: FSMContext):
    username = callback.from_user.username
    if not username:
        await callback.message.edit_text("❌ У вас не задан username.")
        await callback.answer()
        return

    telegram_tag = f"@{username}"
    user = get_user_by_tag(telegram_tag)
    if not user or user[1] != "supervisor":
        await callback.message.edit_text("❌ Только начальники могут создавать смены.")
        await callback.answer()
        return

    await callback.message.answer(
        "Введите дату смены в формате ДД.ММ.ГГГГ (например, 23.11.2025):",
        reply_markup=back_to_main_kb()
    )
    await state.set_state(CreateShift.waiting_for_date)
    await callback.answer()


@router.message(CreateShift.waiting_for_date)
async def process_date(message: types.Message, state: FSMContext):
    date_obj = parse_date(message.text)
    if not date_obj:
        await message.answer("Неверный формат даты. Используйте ДД.ММ.ГГГГ:")
        return

    await state.update_data(shift_date=date_obj)
    await message.answer(
        "Введите время начала смены в формате ЧЧ:ММ (например, 14:30):",
        reply_markup=back_to_main_kb()
    )
    await state.set_state(CreateShift.waiting_for_time)


@router.message(CreateShift.waiting_for_time)
async def process_time(message: types.Message, state: FSMContext):
    time_obj = parse_time(message.text)
    if not time_obj:
        await message.answer("Неверный формат времени. Используйте ЧЧ:ММ:")
        return

    await state.update_data(shift_time=time_obj)
    await message.answer(
        "Введите номер цеха (1, 2 или 3):",
        reply_markup=back_to_main_kb()
    )
    await state.set_state(CreateShift.waiting_for_workshop)


@router.message(CreateShift.waiting_for_workshop)
async def process_workshop(message: types.Message, state: FSMContext):
    try:
        workshop_id = int(message.text.strip())
        if workshop_id not in (1, 2, 3):
            raise ValueError
    except ValueError:
        await message.answer("Цех должен быть 1, 2 или 3. Попробуйте снова:")
        return

    await state.update_data(workshop_id=workshop_id)

    data = await state.get_data()
    date_str = data['shift_date'].strftime("%d.%m.%Y")
    time_str = data['shift_time'].strftime("%H:%M")

    await message.answer(
        f"Подтвердите создание смены:\n"
        f"Дата: {date_str}\n"
        f"Время: {time_str}\n"
        f"Цех: {workshop_id}",
        reply_markup=confirm_kb()
    )
    await state.set_state(CreateShift.confirm)


@router.callback_query(CreateShift.confirm, F.data == "confirm_yes")
async def confirm_shift_creation(callback: types.CallbackQuery, state: FSMContext):
    telegram_tag = f"@{callback.from_user.username}"
    data = await state.get_data()

    shift_id = create_shift(
        shift_date=data['shift_date'],
        shift_time=data['shift_time'],
        workshop_id=data['workshop_id'],
        supervisor_tag=telegram_tag
    )

    if shift_id is None:
        await callback.message.edit_text(
            "❌ Не удалось создать смену. Проверьте данные и повторите попытку.",
            reply_markup=back_to_main_kb()
        )
    else:
        await callback.message.edit_text(
            f"✅ Смена успешно создана!\nID смены: {shift_id}",
            reply_markup=back_to_main_kb()
        )

    await state.clear()
    await callback.answer()


@router.callback_query(CreateShift.confirm, F.data == "confirm_no")
async def cancel_shift_creation(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Создание смены отменено.", reply_markup=back_to_main_kb())
    await callback.answer()