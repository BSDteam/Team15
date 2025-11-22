# handlers/incident.py
"""
Хендлер регистрации инцидента.
Доступен сотрудникам и начальникам.
Использует FSM ReportIncident.
"""

from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter

from services.user_service import get_user_by_tag
from services.incident_service import (
    create_incident,
    determine_recipients,
    get_telegram_id_by_tag,
    log_notification
)
from states import ReportIncident
from keyboards import cancel_incident_kb, confirm_kb, back_to_main_kb
from callbacks import MainMenuCallback

router = Router()


@router.callback_query(F.data == MainMenuCallback.CREATE_REPORT)
async def start_report_incident(callback: types.CallbackQuery, state: FSMContext):
    """
    Запуск создания инцидента.
    Доступен только зарегистрированным сотрудникам и начальникам.
    """
    username = callback.from_user.username
    if not username:
        await callback.message.edit_text("❌ У вас не задан username в Telegram.")
        await callback.answer()
        return

    telegram_tag = f"@{username}"
    user = get_user_by_tag(telegram_tag)
    if not user:
        await callback.message.edit_text("Обратитесь к отделу кадров, вас нет в системе.")
        await callback.answer()
        return

    full_name, role = user
    if role not in ("employee", "supervisor"):
        await callback.message.edit_text("❌ Только сотрудники и начальники могут сообщать об инцидентах.")
        await callback.answer()
        return

    await callback.message.answer(
        "Пожалуйста, опишите инцидент (например: «Остановка конвейера №3»):",
        reply_markup=cancel_incident_kb()
    )
    await state.set_state(ReportIncident.waiting_for_description)
    await callback.answer()


@router.message(ReportIncident.waiting_for_description)
async def process_incident_description(message: types.Message, state: FSMContext):
    if not message.text or not message.text.strip():
        await message.answer("Описание не может быть пустым. Попробуйте снова:")
        return

    await state.update_data(description=message.text.strip())
    await message.answer(
        f"Вы уверены, что хотите зарегистрировать следующий инцидент?\n\n"
        f"<b>{message.text.strip()}</b>",
        reply_markup=confirm_kb()
    )
    await state.set_state(ReportIncident.confirm)


@router.callback_query(ReportIncident.confirm, F.data == "confirm_yes")
async def confirm_incident_creation(callback: types.CallbackQuery, state: FSMContext):
    telegram_tag = f"@{callback.from_user.username}"
    data = await state.get_data()
    description = data["description"]

    # Создаём инцидент
    event_id = create_incident(description, telegram_tag)
    if event_id is None:
        await callback.message.edit_text(
            "❌ Не удалось зарегистрировать инцидент. Повторите попытку.",
            reply_markup=back_to_main_kb()
        )
        await state.clear()
        await callback.answer()
        return

    # Определяем получателей
    recipients = determine_recipients(telegram_tag)
    if not recipients:
        # Например, сотрудник без мастера
        await callback.message.edit_text(
            "✅ Инцидент зарегистрирован, но уведомление отправить некому.",
            reply_markup=back_to_main_kb()
        )
        await state.clear()
        await callback.answer()
        return

    # Отправляем уведомления
    sent_count = 0
    for recipient_tag in recipients:
        telegram_id = get_telegram_id_by_tag(recipient_tag)
        if telegram_id:
            try:
                await callback.bot.send_message(
                    chat_id=telegram_id,
                    text=f"🚨 <b>Новое уведомление об инциденте</b>\n\n"
                         f"<b>От:</b> {telegram_tag}\n"
                         f"<b>Описание:</b> {description}"
                )
                log_notification(telegram_tag, recipient_tag, description)
                sent_count += 1
            except Exception:
                # Пользователь заблокировал бота или недоступен
                pass

    if sent_count > 0:
        text = f"✅ Инцидент зарегистрирован и уведомление отправлено {sent_count} получателю(ям)."
    else:
        text = "✅ Инцидент зарегистрирован, но не удалось отправить уведомления (получатели неактивны)."

    await callback.message.edit_text(text, reply_markup=back_to_main_kb())
    await state.clear()
    await callback.answer()


@router.callback_query(ReportIncident.confirm, F.data == "confirm_no")
async def cancel_incident_creation(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Регистрация инцидента отменена.", reply_markup=back_to_main_kb())
    await callback.answer()


@router.callback_query(F.data == "cancel_incident_creation")
async def cancel_from_description(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Регистрация инцидента отменена.", reply_markup=back_to_main_kb())
    await callback.answer()