from aiogram.dispatcher import router
from aiogram.filters import StateFilter, Command
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardMarkup, Message, KeyboardButton
from aiogram import F, Router
from config import bd_conn
# Не понадобится



class CreateShift(StatesGroup):
    ChoosingWorkshop = State()
    ChoosingId = State()
    ChoosingRole = State()
    Confirm = State()


router = Router()
confirm = ['Да', 'да']

@router.message(StateFilter(None), Command("create_user"))
async def cmd_create_user(message: Message, state: FSMContext) -> None:
    await message.answer(text="Введите ФИО нового пользователя")
    await state.set_state(CreateUser.ChoosingName)
