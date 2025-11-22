# handlers/admin_change_role.py
"""
Хендлер изменения роли пользователя.
Доступен только HR.
Использует FSM.
"""

from aiogram import Router, F, types
from db import execute_query
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from services.user_service import is_hr, update_user_role
from states import ChangeUserRole
from keyboards import admin_main_kb, role_kb, back_to_main_kb
from callbacks import AdminCallback

router = Router()

@router.callback_query(F.data == AdminCallback.CHANGE_ROLE)
async def start_change_role(callback: types.CallbackQuery, state: FSMContext):
    """
    Начинает процесс изменения роли.
    Проверяет, что пользователь — HR.
    """
    telegram_tag = f"@{callback.from_user.username}" if callback.from_user.username else None
    if not telegram_tag or not is_hr(telegram_tag):
        await callback.answer("❌ Только HR может изменять роли.", show_alert=True)
        return

    await callback.message.answer("Введите Telegram-тег пользователя, чью роль нужно изменить:")
    await state.set_state(ChangeUserRole.waiting_for_user_tag)
    await callback.answer()

@router.message(ChangeUserRole.waiting_for_user_tag)
async def process_user_tag(message: types.Message, state: FSMContext):
    tag = message.text.strip()
    if not tag.startswith('@'):
        await message.answer("Тег должен начинаться с @. Попробуйте снова:")
        return

    # Сохраняем тег
    await state.update_data(target_tag=tag)

    # Проверяем, существует ли пользователь
    user = execute_query(
        "SELECT full_name, role FROM users WHERE telegram_tag = %s",
        (tag,),
        fetch=True
    )
    if not user:
        await message.answer("❌ Пользователь не найден.")
        await state.clear()
        return

    full_name, current_role = user[0]
    await message.answer(
        f"Пользователь: {full_name} ({tag})\n"
        f"Текущая роль: {current_role}\n\n"
        "Выберите новую роль:",
        reply_markup=role_kb()
    )
    await state.set_state(ChangeUserRole.waiting_for_new_role)

@router.callback_query(ChangeUserRole.waiting_for_new_role)
async def process_new_role(callback: types.CallbackQuery, state: FSMContext):
    if not callback.data.startswith("role:"):
        await callback.answer("Неверный выбор.", show_alert=True)
        return

    new_role = callback.data.split(":", 1)[1]
    if new_role not in {"employee", "supervisor", "hr"}:
        await callback.answer("Неверная роль.", show_alert=True)
        return

    data = await state.get_data()
    target_tag = data["target_tag"]

    success = update_user_role(target_tag, new_role)

    if success:
        text = f"✅ Роль пользователя {target_tag} успешно изменена на {new_role}."
    else:
        text = "❌ Произошла ошибка при изменении роли."

    await callback.message.edit_text(text, reply_markup=back_to_main_kb())
    await state.clear()
    await callback.answer()