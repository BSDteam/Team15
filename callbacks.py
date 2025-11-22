# callbacks.py
from enum import Enum

class MainMenuCallback(str, Enum):
    REFRESH = "main_refresh"
    HISTORY_SHIFTS = "main_history_shifts"
    CREATE_REPORT = "main_create_report"
    NEW_SHIFT = "main_new_shift"
    VIEW_VACATION = "main_view_vacation"
    SEARCH_EMPLOYEES = "search_employees"
    INCIDENT_LOG = "open_incident_log"
    VIEW_CALENDAR = "view_calendar"

class AdminCallback(str, Enum):
    SHOW_USERS = "admin_show_users"
    ADD_USER = "admin_add_user"
    CHANGE_ROLE = "admin_change_role"
    DELETE_USER = "admin_delete_user"
    MAKE_EMPLOYEE = "admin_make_employee"
    MAKE_MANAGER = "admin_make_manager"
    MAKE_HR = "admin_make_hr"

class IncidentCallback(str, Enum):
    CANCEL = "cancel_incident_creation"
    CONFIRM_YES = "confirm_yes"
    CONFIRM_NO = "confirm_no"

class ShiftCallback(str, Enum):
    CANCEL_NEW = "cancel_new_shift_creation"
    EDIT = "edit_shift"
    DETAILS = "get_shift_details"
    ADD_EMPLOYEE = "pick_employee_to_shift"
    REMOVE_EMPLOYEE = "remove_employee_from_shift"
    DELETE = "delete_shift"

class LeaveCallback(str, Enum):
    CREATE = "action:create_leave"
    CANCEL = "action:cancel_leave"
    BACK = "action:back"