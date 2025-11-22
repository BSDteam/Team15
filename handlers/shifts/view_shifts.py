# handlers/shifts/view_shifts.py
"""
Просмотр списка смен, созданных текущим мастером.
"""

from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext

from services.user_service import get_user_by_tag
from services.shift_service import execute_query
from keyboards import shifts_list_manager, back_to_main_kb, shift_details_kb
from callbacks import MainMenuCallback, ShiftCallback
from states import ViewShift

router = Router()


def get_shifts_with_assignees(telegram_tag: str):
    """
    Возвращает список смен с назначенными сотрудниками.
    Формат: [
        (shift_id, shift_date, shift_time, workshop, [full_name1, full_name2, ...])
    ]
    """
    # Сначала получаем смены
    shifts = execute_query(
        """
        SELECT id, shift_date, shift_time, workshop
        FROM shifts
        WHERE tag = %s
        ORDER BY shift_date DESC, shift_time DESC
        """,
        (telegram_tag,),
        fetch=True
    )

    result = []
    for shift_id, shift_date, shift_time, workshop in shifts:
        # Получаем ФИО сотрудников, назначенных на эту смену
        assignees = execute_query(
            """
            SELECT u.full_name
            FROM shift_assignments sa
            JOIN users u ON sa.user_telegram_tag = u.telegram_tag
            WHERE sa.shift_id = %s
            ORDER BY u.full_name
            """,
            (shift_id,),
            fetch=True
        )
        assignee_names = [row[0] for row in assignees] if assignees else ["— никого"]
        result.append((shift_id, shift_date, shift_time, workshop, assignee_names))

    return result

@router.callback_query(F.data == MainMenuCallback.HISTORY_SHIFTS)
async def view_shifts(callback: types.CallbackQuery, state: FSMContext):
    username = callback.from_user.username
    if not username:
        await callback.message.edit_text("❌ У вас не задан username.")
        await callback.answer()
        return

    telegram_tag = f"@{username}"
    user = get_user_by_tag(telegram_tag)
    if not user or user[1] != "supervisor":
        await callback.message.edit_text("❌ Только начальники могут просматривать смены.")
        await callback.answer()
        return

    shifts = get_shifts_with_assignees(telegram_tag)
    if not shifts:
        await callback.message.edit_text(
            "У вас пока нет созданных смен.",
            reply_markup=back_to_main_kb()
        )
        await callback.answer()
        return

    lines = ["📋 Ваши смены:\n"]
    for shift_id, shift_date, shift_time, workshop, assignees in shifts:
        date_str = shift_date.strftime("%d.%m.%Y")
        time_str = shift_time.strftime("%H:%M")
        assignee_list = ", ".join(assignees)
        lines.append(
            f"ID: {shift_id} | {date_str} {time_str} | Цех {workshop}\n"
            f"Сотрудники: {assignee_list}"
        )

    text = "\n\n".join(lines)
    await callback.message.edit_text(
        f"{text}\n\nВведите ID смены для управления:",
        reply_markup=back_to_main_kb()
    )
    await state.set_state(ViewShift.waiting_for_id)
    await callback.answer()

@router.message(ViewShift.waiting_for_id)
async def handle_shift_id_input(message: types.Message, state: FSMContext):
    """Обрабатывает ввод ID смены после просмотра списка."""
    try:
        shift_id = int(message.text.strip())
    except ValueError:
        await message.answer("ID смены должен быть числом. Попробуйте снова:")
        return

    telegram_tag = f"@{message.from_user.username}"
    user = get_user_by_tag(telegram_tag)
    if not user or user[1] != "supervisor":
        await message.answer("❌ Доступ запрещён.", reply_markup=back_to_main_kb())
        return

    # Проверяем, что смена принадлежит мастеру
    result = execute_query(
        "SELECT 1 FROM shifts WHERE id = %s AND tag = %s",
        (shift_id, telegram_tag),
        fetch=True
    )
    if not result:
        await message.answer("❌ Смена не найдена или не принадлежит вам.", reply_markup=back_to_main_kb())
        return

    await state.update_data(shift_id=shift_id)
    await message.answer(
        f"Смена ID: {shift_id}\nВыберите действие:",
        reply_markup=shift_details_kb()
    )
