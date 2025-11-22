# services/shift_service.py
"""
Сервис для управления сменами.
Поддерживает создание смены и назначение/удаление сотрудников.
"""

import datetime
from typing import Optional

from db import execute_query
from services.user_service import user_exists


def workshop_exists(workshop_id: int) -> bool:
    """Проверяет существование цеха."""
    result = execute_query(
        "SELECT 1 FROM workshops WHERE id = %s",
        (workshop_id,),
        fetch=True
    )
    return bool(result)


def is_employee_subordinate(employee_tag: str, supervisor_tag: str) -> bool:
    """Проверяет, подчиняется ли сотрудник мастеру."""
    result = execute_query(
        """
        SELECT 1 FROM employee_supervisor
        WHERE employee_telegram_tag = %s AND supervisor_telegram_tag = %s
        """,
        (employee_tag, supervisor_tag),
        fetch=True
    )
    return bool(result)


def is_user_on_leave_on_date(user_tag: str, check_date: datetime.date) -> bool:
    """Проверяет, находится ли пользователь в отпуске/больничном в указанную дату."""
    result = execute_query(
        """
        SELECT 1 FROM leave_records
        WHERE user_telegram_tag = %s
          AND start_date <= %s
          AND end_date >= %s
        """,
        (user_tag, check_date, check_date),
        fetch=True
    )
    return bool(result)

def create_shift(shift_date: datetime.date, shift_time: datetime.time, workshop_id: int, supervisor_tag: str) -> Optional[int]:
    """
    Функция создаёт смену в базе данных с переданными обязательными атрибутами с фронта
    :param shift_date:
    :param shift_time:
    :param workshop_id:
    :param supervisor_tag:
    :return:
    """
    if not workshop_exists(workshop_id):
        return None

    try:
        result = execute_query("SELECT nextval('shifts_id_seq')", fetch=True)
        if not result:
            return None
        shift_id = result[0][0]

        execute_query(
            """
            INSERT INTO shifts (id, shift_date, shift_time, tag, workshop)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (shift_id, shift_date, shift_time, supervisor_tag, workshop_id),
            fetch=False
        )
        return shift_id
    except Exception:
        return None


def assign_employee_to_shift(shift_id: int, employee_tag: str, supervisor_tag: str) -> bool:
    """
    Назначает сотрудника на смену.
    Проверяет:
    - существует ли смена
    - подчинён ли сотрудник
    - не в отпуске ли он в день смены
    """
    # Проверка существования смены
    shift = execute_query(
        "SELECT shift_date FROM shifts WHERE id = %s",
        (shift_id,),
        fetch=True
    )
    if not shift:
        return False
    shift_date = shift[0][0]

    # Проверка подчинённости
    if not is_employee_subordinate(employee_tag, supervisor_tag):
        return False

    # Проверка отпуска
    if is_user_on_leave_on_date(employee_tag, shift_date):
        return False

    # Проверка, не назначен ли уже
    existing = execute_query(
        """
        SELECT 1 FROM shift_assignments
        WHERE user_telegram_tag = %s AND shift_id = %s
        """,
        (employee_tag, shift_id),
        fetch=True
    )
    if existing:
        return False  # уже назначен

    try:
        execute_query(
            """
            INSERT INTO shift_assignments (user_telegram_tag, shift_id)
            VALUES (%s, %s)
            """,
            (employee_tag, shift_id),
            fetch=False
        )
        return True
    except Exception:
        return False


def remove_employee_from_shift(shift_id: int, employee_tag: str) -> bool:
    """Удаляет сотрудника из смены."""
    # Проверка существования связи
    exists = execute_query(
        """
        SELECT 1 FROM shift_assignments
        WHERE user_telegram_tag = %s AND shift_id = %s
        """,
        (employee_tag, shift_id),
        fetch=True
    )
    if not exists:
        return False

    try:
        execute_query(
            "DELETE FROM shift_assignments WHERE user_telegram_tag = %s AND shift_id = %s",
            (employee_tag, shift_id),
            fetch=False
        )
        return True
    except Exception:
        return False