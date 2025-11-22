# handlers/shifts/remove_employee.py
"""
Удаление сотрудника из смены.
"""

from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext

from services.user_service import get_user_by_tag
from services.shift_service import remove_employee_from_shift
from states import RemoveEmployee
from keyboards import back_to_main_kb

router = Router()


@router.message(RemoveEmployee.waiting_for_employee_tag)
async def process_remove_employee(message: types.Message, state: FSMContext):
    employee_tag = message.text.strip()
    if not employee_tag.startswith('@'):
        await message.answer("Тег должен начинаться с @. Попробуйте снова:")
        return

    data = await state.get_data()
    shift_id = data.get("shift_id")
    if not shift_id:
        await message.answer("❌ Ошибка: смена не выбрана.", reply_markup=back_to_main_kb())
        await state.clear()
        return

    telegram_tag = f"@{message.from_user.username}"
    user = get_user_by_tag(telegram_tag)
    if not user or user[1] != "supervisor":
        await message.answer("❌ Только начальники могут управлять сменами.", reply_markup=back_to_main_kb())
        await state.clear()
        return

    success = remove_employee_from_shift(shift_id, employee_tag)
    if success:
        await message.answer(
            f"✅ Сотрудник {employee_tag} удалён из смены {shift_id}.",
            reply_markup=back_to_main_kb()
        )
    else:
        await message.answer(
            "❌ Не удалось удалить сотрудника. Возможно, он не состоит в смене.",
            reply_markup=back_to_main_kb()
        )

    await state.clear()