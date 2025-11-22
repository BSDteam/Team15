# handlers/calendar/view.py
"""
Календарь смен и отпусков.
"""

from datetime import datetime
from aiogram import Router, F, types

from services.user_service import get_user_by_tag
from services.employee_service import get_subordinates_with_status, get_calendar_data
from keyboards import back_to_main_kb
from callbacks import MainMenuCallback

router = Router()


def format_calendar(calendar_data: dict, year: int, month: int) -> str:
    """Форматирует календарь в текст."""
    if not calendar_data:
        return "В этом месяце нет смен и отпусков."

    lines = [f"🗓️ Календарь — {month}.{year}\n"]
    for day in sorted(calendar_data.keys()):
        events = calendar_data[day]
        day_str = f"• {day:02}.{month:02}: "
        parts = []
        for ev in events:
            if ev["type"] == "shift":
                parts.append(f"🔧 Смена #{ev['id']} (Цех {ev['workshop']})")
            elif ev["type"] == "leave":
                reason = "🏖️" if ev["reason"] == "vacation" else "🤒"
                parts.append(f"{reason} {ev['user']}")
        lines.append(day_str + ", ".join(parts))
    return "\n".join(lines)


@router.callback_query(F.data == MainMenuCallback.VIEW_CALENDAR)
async def view_calendar(callback: types.CallbackQuery):
    telegram_tag = f"@{callback.from_user.username}"
    user = get_user_by_tag(telegram_tag)
    if not user or user[1] != "supervisor":
        await callback.message.edit_text("❌ Доступ запрещён.")
        await callback.answer()
        return

    # Текущий месяц
    now = datetime.now()
    year, month = now.year, now.month

    # Подчинённые
    subordinates = get_subordinates_with_status(telegram_tag)
    if subordinates:
        subordinate_lines = ["👥 Ваши подчинённые:"]
        for sub in subordinates:
            subordinate_lines.append(f"• {sub['full_name']} — {sub['status']}")
        subordinate_text = "\n".join(subordinate_lines)
    else:
        subordinate_text = "👥 У вас нет подчинённых."

    # Календарь
    calendar_data = get_calendar_data(telegram_tag, year, month)
    calendar_text = format_calendar(calendar_data, year, month)

    full_text = f"{subordinate_text}\n\n{calendar_text}"
    await callback.message.edit_text(full_text, reply_markup=back_to_main_kb())
    await callback.answer()