# states.py
from aiogram.fsm.state import State, StatesGroup

class CreateUser(StatesGroup):
    choosing_name = State()
    choosing_tag = State()
    choosing_role = State()
    confirm = State()

class ChangeUserRole(StatesGroup):
    waiting_for_user_tag = State()   # Ждём тег пользователя
    waiting_for_new_role = State()   # Ждём новую роль

class DeleteUser(StatesGroup):
    waiting_for_user_tag = State()   # Ждём тег для удаления
    confirm = State()                # Подтверждение

class AssignEmployee(StatesGroup):
    waiting_for_employee_tag = State()

class RemoveEmployee(StatesGroup):
    waiting_for_employee_tag = State()

class ReportIncident(StatesGroup):
    waiting_for_description = State()
    confirm = State()

class CreateShift(StatesGroup):
    waiting_for_date = State()
    waiting_for_time = State()
    waiting_for_workshop = State()
    confirm = State()

class ViewShift(StatesGroup):
    waiting_for_id = State()

class LeaveManagement(StatesGroup):
    choosing_employee = State()
    choosing_dates = State()
    choosing_type = State()
    confirm = State()
    canceling = State()  # ← новое состояние

class IncidentLog(StatesGroup):
    waiting_for_date = State()