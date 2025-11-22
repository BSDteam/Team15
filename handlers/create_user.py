# handlers/create_user.py
"""
Хендлер создания пользователя.
Доступен только HR через кнопку "Добавить учетную запись".
Использует FSM для пошагового ввода.
"""

from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from services.user_service import is_hr, create_user_in_db
from states import CreateUser
from keyboards import confirm_kb, back_to_main_kb
from callbacks import AdminCallback

router = Router()

# --- Запуск процесса ---
@router.callback_query(F.data == AdminCallback.ADD_USER)
async def cmd_create_user(callback: types.CallbackQuery, state: FSMContext):
    """
    Начинает процесс создания пользователя.
    Доступен только HR (проверка через сервис).
    """
    telegram_tag = f"@{callback.from_user.username}" if callback.from_user.username else None
    if not telegram_tag or not is_hr(telegram_tag):
        await callback.answer("❌ Только HR может добавлять пользователей.", show_alert=True)
        return

    await callback.message.answer("Введите ФИО нового пользователя:")
    await state.set_state(CreateUser.choosing_name)
    await callback.answer()

# --- Ввод ФИО ---
@router.message(CreateUser.choosing_name)
async def process_name(message: types.Message, state: FSMContext):
    await state.update_data(full_name=message.text.strip())
    await message.answer("Введите Telegram-тег (например, @ivan):")
    await state.set_state(CreateUser.choosing_tag)

# --- Ввод тега ---
@router.message(CreateUser.choosing_tag)
async def process_tag(message: types.Message, state: FSMContext):
    tag = message.text.strip()
    if not tag.startswith('@'):
        await message.answer("Тег должен начинаться с @. Попробуйте снова:")
        return
    await state.update_data(telegram_tag=tag)

    # Устанавливаем состояние
    await state.set_state(CreateUser.choosing_role)

    await message.answer(
        "Выберите роль:\n• employee — Сотрудник\n• supervisor — Начальник\n• hr — Кадровик"
    )

# --- Ввод роли ---
@router.message(CreateUser.choosing_role)
async def process_role(message: types.Message, state: FSMContext):
    role = message.text.strip().lower()
    if role not in {"employee", "supervisor", "hr"}:
        await message.answer("Неверная роль. Выберите: employee, supervisor или hr")
        return
    await state.update_data(role=role)
    data = await state.get_data()
    await message.answer(
        f"Подтвердите данные:\nФИО: {data['full_name']}\nТег: {data['telegram_tag']}\nРоль: {role}",
        reply_markup=confirm_kb()
    )
    await state.set_state(CreateUser.confirm)

# --- Подтверждение ---
@router.callback_query(CreateUser.confirm, F.data == "confirm_yes")
async def confirm_yes(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    success = create_user_in_db(
        telegram_tag=data["telegram_tag"],
        full_name=data["full_name"],
        role=data["role"]
    )
    if success:
        text = "✅ Пользователь успешно добавлен!"
    else:
        text = "❌ Пользователь с таким тегом уже существует."

    await callback.message.edit_text(text, reply_markup=back_to_main_kb())
    await state.clear()
    await callback.answer()

@router.callback_query(CreateUser.confirm, F.data == "confirm_no")
async def confirm_no(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Создание отменено.", reply_markup=back_to_main_kb())
    await callback.answer()