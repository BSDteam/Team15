from aiogram.dispatcher import router
from aiogram.filters import StateFilter, Command
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardMarkup, Message, KeyboardButton
from aiogram import F, Router
from config import cur, bd_conn



class CreateUser(StatesGroup):
    ChoosingName = State()
    ChoosingId = State()
    ChoosingRole = State()


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


@router.message(CreateUser.ChoosingRole, F.text.in_(confirm))
async def cmd_confirm(message: Message, state: FSMContext) -> None:
    user_data = await state.get_data()
    print(user_data)
    text = f'INSERT INTO Users (id, name, role) VALUES ({user_data["ChoosingId"]}, {user_data["ChoosingName"]}, {user_data["ChoosingRole"]})'
    cur.execute(text)
    bd_conn.commit()
    await message.answer("Пользователь добавлен")
