import logging
import os

from aiogram.dispatcher import router
from aiogram.filters import StateFilter, Command
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.methods import SendMessage
from aiogram.types import ReplyKeyboardMarkup, Message, KeyboardButton, CallbackQuery, ReplyKeyboardRemove, \
    InlineKeyboardMarkup
from aiogram import F, Router, Bot
from config import bd_conn
from datetime import datetime, timedelta
from inline_kbds import cancel_incident, confirm


class ReportStages(StatesGroup):
    GetShift = State()
    GetMessage = State()
    GetConfirm = State()

router = Router()

@router.callback_query(StateFilter(None) ,F.data  == 'main_create_report')
async def create_report(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    cur = bd_conn.cursor()
    cur.execute("select * from users where telegram_tag = %s", ("@" + callback.from_user.username,))
    answer = cur.fetchall()
    if not answer:
        return

    await callback.message.answer(text="Введите номер смены, на которой произошел инцидент",
                    reply_markup=InlineKeyboardMarkup(inline_keyboard=cancel_incident))
    await state.set_state(ReportStages.GetShift)


@router.message(ReportStages.GetShift)
async def getShift(message: Message, state: FSMContext):

    await state.update_data(GetShift=int(message.text))
    await message.answer(text="Что произошло там?")
    await state.set_state(ReportStages.GetMessage)

@router.message(ReportStages.GetMessage)
async def getMessage(message: Message, state: FSMContext):

    await state.update_data(GetMessage=message.text)
    answer = await state.get_data()
    text = f"Подтвердите, что\nна {'GetShift'} смене произошло\n{answer['GetMessage']}"

    await message.answer(text=text, reply_markup=InlineKeyboardMarkup(inline_keyboard=confirm))
    await state.set_state(ReportStages.GetConfirm)

@router.callback_query(ReportStages.GetConfirm)
async def getConfirm(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    if callback.data == 'confirm_yes':
        a = await state.get_data()
        print(f"ВЫЗВАТЬ СМЕНУ {a['GetShift']} ПО ПРИЧИНЕ {a['GetMessage']}")

        cur = bd_conn.cursor()
        cur.execute("INSERT INTO events(description, reporter_telegram_tag) VALUES(%s,%s)", (f"Смена {a['GetShift']} ОПИСАНИЕ: {a['GetMessage']}", "@"+callback.from_user.username))

        cur.execute("SELECT users.id FROM users JOIN shift_assignments sa ON sa.shift_id = %s", (a['GetShift'],))
        ans = cur.fetchall()
        cur.close()
        bd_conn.commit()
        # Пока ток теория
        #for i in ans:
        #    await SendMessage(text=f"Инцидент Смена {a['GetShift']} ОПИСАНИЕ: {a['GetMessage']}. Отправил @{callback.from_user.username}", chat_id=i[0]).as_(bot=Bot(token=os.getenv("BOT_TOKEN")))
        await state.clear()
    elif callback.data == 'confirm_no':
        await callback.message.answer("Отменено")
        await state.clear()

