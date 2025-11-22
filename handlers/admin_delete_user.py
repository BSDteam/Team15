# handlers/admin_delete_user.py
"""
Хендлер удаления пользователя.
Доступен только HR.
Использует FSM + подтверждение.
"""

from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from db import execute_query
from services.user_service import is_hr, delete_user_by_tag
from states import DeleteUser
from keyboards import confirm_kb
from callbacks import AdminCallback

router = Router()

@router.callback_query(F.data == AdminCallback.DELETE_USER)
async def start_delete_user(callback: types.CallbackQuery, state: FSMContext):
    """
    Начинает процесс удаления пользователя.
    Проверяет, что пользователь — HR.
    """
    telegram_tag = f"@{callback.from_user.username}" if callback.from_user.username else None
    if not telegram_tag or not is_hr(telegram_tag):
        await callback.answer("❌ Только HR может удалять пользователей.", show_alert=True)
        return

    await callback.message.answer("Введите Telegram-тег пользователя, которого нужно удалить:")
    await state.set_state(DeleteUser.waiting_for_user_tag)
    await callback.answer()

@router.message(DeleteUser.waiting_for_user_tag)
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

    full_name, role = user[0]
    await message.answer(
        f"Вы собираетесь удалить:\n"
        f"👤 {full_name} (@{tag})\n"
        f"Роль: {role}\n\n"
        "Вы уверены?",
        reply_markup=confirm_kb()
    )
    await state.set_state(DeleteUser.confirm)

@router.callback_query(DeleteUser.confirm, F.data == "confirm_yes")
async def confirm_delete(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    target_tag = data["target_tag"]

    success = delete_user_by_tag(target_tag)
    if success:
        await callback.message.edit_text(f"✅ Пользователь {target_tag} успешно удалён.")
    else:
        await callback.message.edit_text("❌ Пользователь не найден или уже удалён.")

    await state.clear()
    await callback.answer()

@router.callback_query(DeleteUser.confirm, F.data == "confirm_no")
async def cancel_delete(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Удаление отменено.")
    await callback.answer()