# keyboards.py
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from callbacks import (
    MainMenuCallback, AdminCallback, IncidentCallback,
    ShiftCallback, LeaveCallback
)

# === Главное меню ===

def main_menu_employee() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Обновить Информацию", callback_data=MainMenuCallback.REFRESH)],
        [InlineKeyboardButton(text="Посмотреть историю смен", callback_data=MainMenuCallback.HISTORY_SHIFTS)],
        [InlineKeyboardButton(text="Сообщить об инциденте", callback_data=MainMenuCallback.CREATE_REPORT)],
    ])

# keyboards.py
def main_menu_manager() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Обновить Информацию", callback_data=MainMenuCallback.REFRESH)],
        [InlineKeyboardButton(text="Зарегистрировать новую смену", callback_data=MainMenuCallback.NEW_SHIFT)],
        [InlineKeyboardButton(text="Просмотр смен", callback_data=MainMenuCallback.HISTORY_SHIFTS)],
        [InlineKeyboardButton(text="Меню отпусков", callback_data=MainMenuCallback.VIEW_VACATION)],
        [InlineKeyboardButton(text="Просмотр статуса сотрудников", callback_data=MainMenuCallback.SEARCH_EMPLOYEES)],
        [InlineKeyboardButton(text="Журнал инцидентов", callback_data=MainMenuCallback.INCIDENT_LOG)],
        [InlineKeyboardButton(text="Сообщить об инциденте", callback_data=MainMenuCallback.CREATE_REPORT)],
        [InlineKeyboardButton(text="Календарь смен", callback_data=MainMenuCallback.VIEW_CALENDAR)],  # ← новая строка
    ])

# === Инциденты ===

def cancel_incident_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Отменить регистрацию", callback_data=IncidentCallback.CANCEL)]
    ])

def confirm_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Да", callback_data=IncidentCallback.CONFIRM_YES)],
        [InlineKeyboardButton(text="Нет", callback_data=IncidentCallback.CONFIRM_NO)]
    ])

# === Смены ===

def cancel_new_shift_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Отменить регистрацию", callback_data=ShiftCallback.CANCEL_NEW)]
    ])

def shifts_list_manager() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="На Главную", callback_data=MainMenuCallback.REFRESH)],
        [InlineKeyboardButton(text="Редактировать смену", callback_data=ShiftCallback.EDIT)],
        [InlineKeyboardButton(text="Подробная информация по смене", callback_data=ShiftCallback.DETAILS)]
    ])

def shifts_list_employee() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="На Главную", callback_data=MainMenuCallback.REFRESH)],
        [InlineKeyboardButton(text="Подробная информация по смене", callback_data=ShiftCallback.DETAILS)]
    ])

def shift_details_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Добавить Сотрудника", callback_data=ShiftCallback.ADD_EMPLOYEE)],
        [InlineKeyboardButton(text="Удалить Сотрудника", callback_data=ShiftCallback.REMOVE_EMPLOYEE)],
        [InlineKeyboardButton(text="Удалить Смену", callback_data=ShiftCallback.DELETE)],
        [InlineKeyboardButton(text="На Главную", callback_data=MainMenuCallback.REFRESH)],
    ])

# === Отпуска ===

def vacations_list_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Назначить отпуск/больничный", callback_data=LeaveCallback.CREATE)],
        [InlineKeyboardButton(text="Отменить запись", callback_data=LeaveCallback.CANCEL)],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data=MainMenuCallback.REFRESH)]
    ])

# === Админка (HR) ===

def admin_main_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Показать список учетных записей", callback_data=AdminCallback.SHOW_USERS)],
        [InlineKeyboardButton(text="Добавить учетную запись", callback_data=AdminCallback.ADD_USER)],
        [InlineKeyboardButton(text="Изменить должность сотрудника", callback_data=AdminCallback.CHANGE_ROLE)],
        [InlineKeyboardButton(text="Удалить учетную запись", callback_data=AdminCallback.DELETE_USER)],
    ])

def admin_change_role_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Сделать Сотрудником", callback_data=AdminCallback.MAKE_EMPLOYEE)],
        [InlineKeyboardButton(text="Сделать Начальником", callback_data=AdminCallback.MAKE_MANAGER)],
        [InlineKeyboardButton(text="Сделать Кадровиком", callback_data=AdminCallback.MAKE_HR)],
    ])

# === Роли (для выбора) ===

def role_kb() -> InlineKeyboardMarkup:
    """
    Клавиатура для выбора роли: employee, supervisor, hr.
    Используется при создании и изменении пользователя.
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="employee", callback_data="role:employee")],
        [InlineKeyboardButton(text="supervisor", callback_data="role:supervisor")],
        [InlineKeyboardButton(text="hr", callback_data="role:hr")]
    ])

def back_to_main_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ На главную", callback_data="main_refresh")]
    ])

def leave_type_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Отпуск", callback_data="leave_type:vacation")],
        [InlineKeyboardButton(text="Больничный", callback_data="leave_type:sick")],
        [InlineKeyboardButton(text="Прочее отсутствие", callback_data="leave_type:absent")]
    ])

def incident_log_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Фильтр по дате", callback_data="incident_filter_date")],
        [InlineKeyboardButton(text="Скачать PDF за день", callback_data="incident_download_pdf")],
        [InlineKeyboardButton(text="⬅️ На главную", callback_data="main_refresh")]
    ])