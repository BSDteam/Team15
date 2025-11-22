# handlers/__init__.py
from aiogram import Router

# Основные
from .main_menu import router as main_menu_router
from .incident import router as incident_router

# HR
from .create_user import router as create_user_router
from .admin_show_users import router as show_users_router
from .admin_delete_user import router as delete_user_router
from .admin_change_role import router as change_role_router

# Смены
from .shifts.create_shift import router as create_shift_router
from .shifts.view_shifts import router as view_shifts_router
from .shifts.shift_details import router as shift_details_router
from .shifts.assign_employee import router as assign_employee_router
from .shifts.remove_employee import router as remove_employee_router

# Отпуска — НОВОЕ
from .leaves.menu_of_leaves import router as leaves_main_router
from .leaves.manage_leave import router as manage_leave_router
from .leaves.cancel_leave import router as cancel_leave_router

from .incidents.log import router as incident_log_router

from .employees.search import router as employee_search_router
from .calendar.view import router as calendar_router

# Главный роутер
router = Router()
router.include_routers(
    main_menu_router,
    incident_router,
    create_user_router,
    show_users_router,
    delete_user_router,
    change_role_router,
    create_shift_router,
    view_shifts_router,
    shift_details_router,
    assign_employee_router,
    remove_employee_router,
    leaves_main_router,
    manage_leave_router,
    cancel_leave_router,
    incident_log_router,
    employee_search_router,
    calendar_router,
)