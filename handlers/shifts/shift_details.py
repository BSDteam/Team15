# handlers/shifts/shift_details.py
"""
Просмотр деталей смены и управление составом.
"""

from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from states import AssignEmployee, RemoveEmployee
from keyboards import shift_details_kb, back_to_main_kb
from callbacks import ShiftCallback

router = Router()


@router.callback_query(F.data == ShiftCallback.ADD_EMPLOYEE)
async def start_assign_employee(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "Введите Telegram-тег сотрудника (например, @ivan):",
        reply_markup=back_to_main_kb()
    )
    await state.set_state(AssignEmployee.waiting_for_employee_tag)
    await callback.answer()


@router.callback_query(F.data == ShiftCallback.REMOVE_EMPLOYEE)
async def start_remove_employee(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "Введите Telegram-тег сотрудника для удаления:",
        reply_markup=back_to_main_kb()
    )
    await state.set_state(RemoveEmployee.waiting_for_employee_tag)
    await callback.answer()