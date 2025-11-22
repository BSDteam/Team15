import logging

from aiogram.filters import StateFilter, Command
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardMarkup, Message, KeyboardButton, CallbackQuery
from aiogram import F, Router
from config import bd_conn
from datetime import datetime, timedelta


class CreateUser(StatesGroup):
    ChoosingWorkshop = State()
    ChoosingDate = State()
    ChoosingTime = State()
    ConfirmShift = State()


router = Router()
confirm = ['Да', 'да']



async def cmdCreateShift(message: Message, state: FSMContext) -> None:
    cur = bd_conn.cursor()
    SQL = 'SELECT extra_field FROM workshops'
    cur.execute(SQL)
    workshops = cur.fetchall()
    text = ''
    for i in workshops:
        text += ' '
        text += str(i[0])
    await message.answer(f"Доступные цеха:{text}, выберите доступный")
    await state.set_state(CreateUser.ChoosingWorkshop)

@router.message(StateFilter(None), Command("create_shift"))
async def cmdCreateShift1(message: Message, state: FSMContext) -> None:
    await cmdCreateShift(message, state)

@router.callback_query(StateFilter(None), F.data == "main_new_shift")
async def cmdCreateShift2(callback: CallbackQuery, state: FSMContext) -> None:
    await cmdCreateShift(callback.message, state)

@router.message(CreateUser.ChoosingWorkshop)
async def ChoosingWorkshop(message: Message, state: FSMContext) -> None:
    await state.update_data(ChoosingWorkshop=message.text)
    cur = bd_conn.cursor()
    workshop_id = message.text
    available_dates = []
    SQL = 'SELECT shift_date FROM shifts WHERE workshop = %s'
    cur.execute(SQL, (workshop_id,))
    print(cur.fetchall())
    dates = list(map(lambda x: x[2], cur.fetchall()))
    text = ''
    for i in range(7):
        if dates.count(datetime.now().date() + timedelta(days=i)) < 3:
            text += ' '
            text += (datetime.now().date() + timedelta(days=i)).strftime("%Y-%m-%d")
    await message.answer(f"Доступные даты в выбранном цеху:{text}")
    await state.set_state(CreateUser.ChoosingDate)


@router.message(CreateUser.ChoosingDate)
async def ChoosingDate(message: Message, state: FSMContext) -> None:
    await state.update_data(ChoosingDate=message.text)
    cur = bd_conn.cursor()
    user_data = await state.get_data()
    workshop_id = user_data["ChoosingWorkshop"]
    text = 'SELECT shift_time FROM shifts WHERE workshop = %s AND shift_date = %s'
    cur.execute(text, (workshop_id, message.text))
    times = cur.fetchall()
    available_time = ''
    for i in times:
        available_time += ' ' + str(i[0])
    if available_time:
        await message.answer(f'Занятое время:{available_time}, введите свободное время')
    else:
        await message.answer('В данный день смены не стоят, укажите начало смены')
    await state.set_state(CreateUser.ChoosingTime)

@router.message(CreateUser.ChoosingTime)
async def ChoosingTime(message: Message, state: FSMContext) -> None:
    await state.update_data(ChoosingTime=message.text)
    user_data = await state.get_data()
    await message.answer(f"Подтвердите указанные данные: {user_data['ChoosingWorkshop']}, {user_data['ChoosingDate']}, {user_data['ChoosingTime']}")
    await state.set_state(CreateUser.ConfirmShift)


@router.message(CreateUser.ConfirmShift)
async def cmdConfirm(message: Message, state: FSMContext) -> None:
    cur = bd_conn.cursor()
    user_data = await state.get_data()
    if message.text.lower() == 'да':
        print(user_data)
        text = f'INSERT INTO shifts (shift_date, shift_time, tag, workshop) VALUES (%s, %s, %s, %s)'
        cur.execute(text, (user_data["ChoosingDate"], user_data["ChoosingTime"], f'@{message.from_user.username}', user_data['ChoosingWorkshop']))
        logging.info('Created ' + text)
        bd_conn.commit()
        logging.info('Commit created')
        await message.answer("Смена добавленa")
    else:
        await state.clear()
        await message.answer("Отменено")
