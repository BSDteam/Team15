"""
Вход в меню отпусков.
"""

from aiogram import Router, F, types

from callbacks import MainMenuCallback
from services.user_service import get_user_by_tag
from services.leave_service import get_leaves_for_supervisor
from keyboards import vacations_list_kb

router = Router()


@router.callback_query(F.data == MainMenuCallback.VIEW_VACATION)
async def view_vacation_menu(callback: types.CallbackQuery):
    telegram_tag = f"@{callback.from_user.username}"
    user = get_user_by_tag(telegram_tag)
    if not user or user[1] != "supervisor":
        await callback.message.edit_text("❌ Доступ запрещён.")
        await callback.answer()
        return

    leaves = get_leaves_for_supervisor(telegram_tag)
    if leaves:
        lines = ["📋 Текущие отпуска подчинённых:\n"]
        for leave in leaves:
            start = leave['start'].strftime("%d.%m.%Y")
            end = leave['end'].strftime("%d.%m.%Y")
            type_display = {
                "vacation": "отпуск",
                "sick": "больничный",
                "absent": "прочее отсутствие"
            }[leave['type']]
            lines.append(f"• {leave['full_name']} ({leave['tag']})\n  {start}–{end}, {type_display}")
        text = "\n\n".join(lines)
    else:
        text = "У ваших подчинённых нет запланированных отпусков."

    await callback.message.edit_text(
        f"{text}\n\nВыберите действие:",
        reply_markup=vacations_list_kb()
    )
    await callback.answer()