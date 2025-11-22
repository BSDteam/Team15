import logging

from aiogram.dispatcher import router
from aiogram.filters import StateFilter, Command
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardMarkup, Message, KeyboardButton
from aiogram import F, Router
from config import bd_conn



class CreateUser(StatesGroup):
    ChoosingName = State()
    ChoosingId = State()
    ChoosingRole = State()
    Confirm = State()


router = Router()
confirm = ['Да', 'да']

@router.message(StateFilter(None), Command("create_user"))
async def cmd_create_user(message: Message, state: FSMContext) -> None:
    await message.answer(text="Введите ФИО нового пользователя")
    await state.set_state(CreateUser.ChoosingName)


@router.message(CreateUser.ChoosingName)
async def ChoosingId(message: Message, state: FSMContext) -> None:
    await state.update_data(ChoosingName=message.text)
    await message.answer("Введите никнейм пользователя (@sample)")
    await state.set_state(CreateUser.ChoosingId)


@router.message(CreateUser.ChoosingId)
async def ChoosingRole(message: Message, state: FSMContext) -> None:
    await state.update_data(ChoosingId=message.text)
    await message.answer("Выберите роль пользователя")
    await state.set_state(CreateUser.ChoosingRole)


@router.message(CreateUser.ChoosingRole)
async def ChoosingRole(message: Message, state: FSMContext) -> None:
    await state.update_data(ChoosingRole=message.text)
    user_data = await state.get_data()
    await message.answer(f"Подтвердите указанные данные: {user_data["ChoosingId"]}, {user_data["ChoosingName"]}, {user_data["ChoosingRole"]}")
    await state.set_state(CreateUser.Confirm)


@router.message(CreateUser.Confirm)
async def cmd_confirm(message: Message, state: FSMContext) -> None:
    cur = bd_conn.cursor()
    user_data = await state.get_data()
    if message.text.lower() == 'да':
        print(user_data)
        text = f'INSERT INTO Users (telegram_tag, full_name, role, status) VALUES (%s, %s, %s, %s)'
        cur.execute(text, (user_data["ChoosingId"], user_data["ChoosingName"], user_data["ChoosingRole"], 'available'))
        logging.info('Created '+text)
        bd_conn.commit()
        logging.info('Commit created')
        await message.answer("Пользователь добавлен")
    else:
        await state.clear()
        await message.answer("Отменено")
