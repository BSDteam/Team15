# handlers/admin_show_users.py
"""
Хендлер для отображения списка всех пользователей.
Доступен только HR.
"""

from aiogram import Router, F, types
from aiogram.filters import StateFilter

from keyboards import back_to_main_kb
from services.user_service import is_hr, get_all_users
from callbacks import AdminCallback

router = Router()

@router.callback_query(F.data == AdminCallback.SHOW_USERS)
async def show_all_users(callback: types.CallbackQuery):
    """
    Показывает список всех пользователей.
    Доступен только HR.
    """
    telegram_tag = f"@{callback.from_user.username}" if callback.from_user.username else None
    if not telegram_tag or not is_hr(telegram_tag):
        await callback.answer("❌ Только HR может просматривать список.", show_alert=True)
        return

    users = get_all_users()
    if not users:
        await callback.message.edit_text("Список пользователей пуст.")
        await callback.answer()
        return

    # Формируем текст
    lines = ["📋 Список всех пользователей:\n"]
    for user in users:
        lines.append(
            f"👤 {user['full_name']} ({user['telegram_tag']})\n"
            f"   Роль: {user['role']}\n"
            f"   Статус: {user['status']}"
        )

    text = "\n\n".join(lines)
    await callback.message.edit_text(text, reply_markup=back_to_main_kb())
    await callback.answer()