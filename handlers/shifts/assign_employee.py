# handlers/shifts/assign_employee.py
"""
Назначение сотрудника на смену.
"""

from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext

from services.user_service import get_user_by_tag
from services.shift_service import assign_employee_to_shift
from states import AssignEmployee
from keyboards import back_to_main_kb

router = Router()


@router.message(AssignEmployee.waiting_for_employee_tag)
async def process_assign_employee(message: types.Message, state: FSMContext):
    employee_tag = message.text.strip()
    if not employee_tag.startswith('@'):
        await message.answer("Тег должен начинаться с @. Попробуйте снова:")
        return

    # Получаем shift_id из состояния
    data = await state.get_data()
    shift_id = data.get("shift_id")
    if not shift_id:
        await message.answer("❌ Ошибка: смена не выбрана.", reply_markup=back_to_main_kb())
        await state.clear()
        return

    telegram_tag = f"@{message.from_user.username}"
    user = get_user_by_tag(telegram_tag)
    if not user or user[1] != "supervisor":
        await message.answer("❌ Только начальники могут назначать сотрудников.", reply_markup=back_to_main_kb())
        await state.clear()
        return

    success = assign_employee_to_shift(shift_id, employee_tag, telegram_tag)
    if success:
        await message.answer(
            f"✅ Сотрудник {employee_tag} успешно добавлен в смену {shift_id}.",
            reply_markup=back_to_main_kb()
        )
    else:
        await message.answer(
            "❌ Не удалось добавить сотрудника. Возможные причины:\n"
            "• Сотрудник не подчинён вам\n"
            "• Сотрудник в отпуске в этот день\n"
            "• Сотрудник уже в смене\n"
            "• Пользователь не существует",
            reply_markup=back_to_main_kb()
        )

    await state.clear()