from aiogram import types, Router, F
from aiogram.filters import Command
from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardMarkup, CallbackQuery
from annotated_types.test_cases import cases
from inline_kbds import MainMenuEmployee, MainMenuManager, admin_main, shifts_list, shifts_list_employee
from config import bd_conn

router = Router()

@router.message(Command("menu"))
@router.message(Command("start"))
async def menu(message: types.Message):
    cur = bd_conn.cursor()
    tag = "@"+message.from_user.username
    cur.execute("SELECT * from users WHERE users.telegram_tag = %s LIMIT 1", (tag,))
    ans = cur.fetchone()
    name = ans[1]
    role = ans[2]
    if role == "hr": # employee supervisor
        role = "Кадровый отдел"
    elif role == "employee":
        role = "Сотрудник"
    elif role == "supervisor":
        role = "Начальник"

    if role == "Начальник":
        kbrd = InlineKeyboardMarkup(inline_keyboard=MainMenuManager)
    elif role == "Кадровый отдел":
        kbrd = InlineKeyboardMarkup(inline_keyboard=admin_main)
    else:
        kbrd = InlineKeyboardMarkup(inline_keyboard=MainMenuEmployee)

    await message.answer(text=f"Добрый день, {name}\n Ваша должность:\n{role}\n", reply_markup=kbrd)




@router.callback_query(F.data == "main_refresh")
async def handle_main_refresh(callback: CallbackQuery):
    await callback.answer()
    cur = bd_conn.cursor()
    tag = "@" + callback.from_user.username
    cur.execute("SELECT * from users WHERE users.telegram_tag = %s LIMIT 1", (tag,))
    ans = cur.fetchone()
    name = ans[1]
    role = ans[2]
    if role == "hr":  # employee supervisor
        role = "Кадровый отдел"
    elif role == "employee":
        role = "Сотрудник"
    elif role == "supervisor":
        role = "Начальник"

    if role == "Начальник":
        kbrd = InlineKeyboardMarkup(inline_keyboard=MainMenuManager)
    elif role == "Кадровый отдел":
        kbrd = InlineKeyboardMarkup(inline_keyboard=admin_main)
    else:
        kbrd = InlineKeyboardMarkup(inline_keyboard=MainMenuEmployee)

    await callback.message.edit_text(text=f"Добрый день, {name}\n Ваша должность:\n{role}\n", reply_markup=kbrd)

# main_history_shifts
@router.callback_query(F.data == "main_history_shifts")
async def handle_main_history_shifts(callback: CallbackQuery):
    await callback.answer()
    cur = bd_conn.cursor()
    tag = "@" + callback.from_user.username
    cur.execute("SELECT * from users WHERE users.telegram_tag = %s LIMIT 1", (tag,))
    ans = cur.fetchone()
    if ans is None:
        print("no users found")
        return
    role = ans[2]

    part1 = """Просмотр смен:\n"""
    part2 = ""
    part3 = ""

    if role == "supervisor":
        part2 = "\nВы начальник а сменах:"
        cur.execute("SELECT shifts.id, shifts.workshop, shifts.shift_date, shifts.shift_time from shifts WHERE shifts.tag = %s", (tag,))
        ans = cur.fetchall()
        for x in ans:
            part2 += f"\nСмена №{ans[0]}, цех {x[1]},начало {x[2]} в {x[3]}:"

    part3 = "\n\nВы работник в сменах"
    cur.execute("SELECT s.shift_id, shifts.workshop, shifts.shift_date, shifts.shift_time, users.full_name, users.telegram_tag\
                 from shift_assignments s JOIN shifts ON shifts.id = \
            s.shift_id JOIN users ON users.telegram_tag = shifts.tag WHERE s.user_telegram_tag = %s", (tag,))
    ans = cur.fetchall()
    for x in ans:
        part3 += f"\nСмена №{ans[0][0]}, цех {x[1]},начало в {x[2]} в {x[3]}, начальник {x[4]} ({x[5]}):"

    total = part1 + part2 + part3
    if role == "supervisor":
        knbd = InlineKeyboardMarkup(inline_keyboard=shifts_list)
    else:
        knbd = InlineKeyboardMarkup(inline_keyboard=shifts_list_employee)
    await callback.message.edit_text(total, reply_markup= knbd)