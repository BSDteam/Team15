# handlers/leaves/cancel_leave.py
"""
Отмена отпуска.
"""

from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext

from services.user_service import get_user_by_tag
from services.leave_service import cancel_leave, get_leaves_for_supervisor
from keyboards import back_to_main_kb, confirm_kb
from callbacks import LeaveCallback
from states import LeaveManagement

router = Router()


@router.callback_query(F.data == LeaveCallback.CANCEL)
async def start_cancel_leave(callback: types.CallbackQuery, state: FSMContext):
    telegram_tag = f"@{callback.from_user.username}"
    user = get_user_by_tag(telegram_tag)
    if not user or user[1] != "supervisor":
        await callback.message.edit_text("❌ Доступ запрещён.")
        await callback.answer()
        return

    leaves = get_leaves_for_supervisor(telegram_tag)
    if not leaves:
        await callback.message.edit_text("У ваших подчинённых нет активных отпусков.", reply_markup=back_to_main_kb())
        await callback.answer()
        return

    lines = ["Выберите отпуск для отмены:\n"]
    for leave in leaves:
        start = leave['start'].strftime("%d.%m.%Y")
        end = leave['end'].strftime("%d.%m.%Y")
        type_display = {"vacation": "отпуск", "sick": "больничный", "absent": "отсутствие"}[leave['type']]
        lines.append(f"ID: {leave['id']} | {leave['full_name']} ({leave['tag']})\n   {start}–{end}, {type_display}")

    await callback.message.edit_text(
        "\n\n".join(lines) + "\n\nВведите ID отпуска:",
        reply_markup=back_to_main_kb()
    )
    await state.set_state(LeaveManagement.canceling)
    await callback.answer()


@router.message(LeaveManagement.canceling)
async def process_leave_id_to_cancel(message: types.Message, state: FSMContext):
    try:
        leave_id = int(message.text.strip())
    except ValueError:
        await message.answer("ID должен быть числом. Попробуйте снова:")
        return

    telegram_tag = f"@{message.from_user.username}"
    success = cancel_leave(leave_id, telegram_tag)

    if success:
        await message.answer("✅ Отпуск успешно отменён.", reply_markup=back_to_main_kb())
    else:
        await message.answer("❌ Не удалось отменить отпуск. Возможно, он не существует или не принадлежит вам.", reply_markup=back_to_main_kb())

    await state.clear()