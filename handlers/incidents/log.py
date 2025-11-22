# handlers/incidents/log.py
"""
Журнал инцидентов для мастера.
"""

from datetime import datetime
from typing import Optional
from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext

from services.user_service import get_user_by_tag
from services.incident_service import (
    get_recent_incidents_for_supervisor,
    get_incidents_by_date_for_supervisor
)
from services.report_service import generate_incident_report_pdf
from states import IncidentLog
from keyboards import back_to_main_kb, incident_log_kb
from callbacks import MainMenuCallback

router = Router()


def format_incidents(incidents: list[dict]) -> str:
    if not incidents:
        return "За указанный период инцидентов не зафиксировано."

    lines = ["📋 Инциденты:\n"]
    for inc in incidents:
        created_at = inc["created_at"]
        date_str = created_at.strftime("%d.%m.%Y %H:%M")
        lines.append(
            f"• {date_str}\n"
            f"  {inc['full_name']} ({inc['telegram_tag']})\n"
            f"  {inc['description']}"
        )
    return "\n\n".join(lines)


@router.callback_query(F.data == MainMenuCallback.INCIDENT_LOG)
async def view_incident_log(callback: types.CallbackQuery):
    telegram_tag = f"@{callback.from_user.username}"
    user = get_user_by_tag(telegram_tag)
    if not user or user[1] != "supervisor":
        await callback.message.edit_text("❌ Доступ запрещён.")
        await callback.answer()
        return

    incidents = get_recent_incidents_for_supervisor(telegram_tag, limit=6)
    text = format_incidents(incidents)
    await callback.message.edit_text(
        f"{text}\n\nВыберите действие:",
        reply_markup=incident_log_kb()
    )
    await callback.answer()


@router.callback_query(F.data == "incident_filter_date")
async def start_filter_by_date(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "Введите дату в формате ДД.ММ.ГГГГ (например, 23.11.2025):",
        reply_markup=back_to_main_kb()
    )
    await state.set_state(IncidentLog.waiting_for_date)
    await callback.answer()


@router.callback_query(F.data == "incident_download_pdf")
async def start_download_pdf(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "Введите дату для отчёта в формате ДД.ММ.ГГГГ:",
        reply_markup=back_to_main_kb()
    )
    await state.set_state(IncidentLog.waiting_for_date)
    await state.update_data(action="pdf")  # метка для обработки
    await callback.answer()


@router.message(IncidentLog.waiting_for_date)
async def process_date_for_incidents(message: types.Message, state: FSMContext):
    try:
        target_date = datetime.strptime(message.text.strip(), "%d.%m.%Y").date()
    except ValueError:
        await message.answer("Неверный формат. Используйте ДД.ММ.ГГГГ:")
        return

    telegram_tag = f"@{message.from_user.username}"
    user = get_user_by_tag(telegram_tag)
    if not user or user[1] != "supervisor":
        await message.answer("❌ Доступ запрещён.", reply_markup=back_to_main_kb())
        await state.clear()
        return

    data = await state.get_data()
    action = data.get("action")

    incidents = get_incidents_by_date_for_supervisor(telegram_tag, target_date)

    if action == "pdf":
        pdf_bytes = generate_incident_report_pdf(incidents, target_date)
        await message.answer_document(
            types.BufferedInputFile(pdf_bytes, filename=f"incidents_{target_date}.pdf")
        )
        await state.clear()
        return

    # Обычный просмотр
    text = format_incidents(incidents)
    await message.answer(
        f"{text}\n\nВыберите действие:",
        reply_markup=incident_log_kb()
    )
    await state.clear()