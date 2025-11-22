from aiogram.types import InlineKeyboardButton

#  для окна #1
MainMenuEmployee = [
    [InlineKeyboardButton(text="Обновить Информацию", callback_data='main_refresh')],
    [InlineKeyboardButton(text="Посмотреть историю смен", callback_data='main_history_shifts')],
    [InlineKeyboardButton(text="Сообщить об инциденте", callback_data='main_create_report')],
]
#1.2
MainMenuManager = [
    [InlineKeyboardButton(text="Обновить Информацию", callback_data='main_refresh')],
    [InlineKeyboardButton(text="Зарегистрировать новую смену", callback_data='main_new_shift')],
    [InlineKeyboardButton(text="Просмотр смен", callback_data='main_history_shifts')],
    [InlineKeyboardButton(text="Назначить отпуск", callback_data='main_create_vacation')],
    [InlineKeyboardButton(text="Отменить отпуск", callback_data='main_cancel_vacation')],
    [InlineKeyboardButton(text="Сообщить об инциденте", callback_data='main_create_report')],
]

# диалог создания инцидента
cancel_incident = [
    [InlineKeyboardButton(text="Отменить регистрацию", callback_data='cancel_incident_creation')]
]

#confirm
confirm = [
    [InlineKeyboardButton(text="Да", callback_data='confirm_yes')],
    [InlineKeyboardButton(text="Нет", callback_data='confirm_no')]
    ]

# На главную
to_main = [
    [InlineKeyboardButton(text="На Главную", callback_data='main_refresh')]
]


# Диалог 2 Регистрация смены
cancel_new_shift = [
    [InlineKeyboardButton(text="Отменить регистрацию", callback_data='cancel_new_shift_creation')]
]

# 3 Просмотр списка смен
shifts_list = [
    [InlineKeyboardButton(text="На Главную", callback_data='main_refresh')],
    [InlineKeyboardButton(text="Редактировать смену", callback_data='edit_shift')],
    [InlineKeyboardButton(text="Подробная информация по смене", callback_data='get_shift_details')]
]

shifts_list_employee = [
    [InlineKeyboardButton(text="На Главную", callback_data='main_refresh')],
    [InlineKeyboardButton(text="Подробная информация по смене", callback_data='get_shift_details')]
]

# 4 Информация по смене
shift_details = [
    [InlineKeyboardButton(text="Добавить Сотрудника", callback_data='pick_employee_to_shift')],
    [InlineKeyboardButton(text="Удалить Сотрудника", callback_data='remove_employee_from_shift')],
    [InlineKeyboardButton(text="Удалить Смену", callback_data='delete_shift')],
    [InlineKeyboardButton(text="На Главную", callback_data='main_refresh')],
]

# 5 нечего писать
#6 Просмотр истории отпусков
vacations_list = [
    [InlineKeyboardButton(text="Назначить отпуск", callback_data='create_vacantion')],
    [InlineKeyboardButton(text="Отменить отпуск", callback_data='cancel_vacantion')],
    [InlineKeyboardButton(text="Вернуться", callback_data='main_refresh')],
]
# 7 8 нечего делать
vacations_list_go_back = [
    [InlineKeyboardButton(text="Вернуться")],
]

# Панельки отдела кадров
admin_main = [
    [InlineKeyboardButton(text="Показать список учетных записей", callback_data='admin_show_users')],
    [InlineKeyboardButton(text="Добавить учетную запись", callback_data='admin_add_user')],
    [InlineKeyboardButton(text="Изменить должность сотрудника", callback_data='admin_change_role')],
    [InlineKeyboardButton(text="Удалить учетную запись", callback_data='admin_delete_user')],
]

# Изменение роли (три роли, имеющуюся нужно удалить)
admin_change_role = [
    [InlineKeyboardButton(text="Сделать Сотрудником", callback_data='admin_make_employee')],
    [InlineKeyboardButton(text="Сделать Начальником", callback_data='admin_make_manager')],
    [InlineKeyboardButton(text="Сделать Кадровиком", callback_data='admin_make_hr')],
]