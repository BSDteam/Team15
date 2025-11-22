# services/leave_service.py
"""
Сервис для управления отпусками и больничными.
"""

import datetime
from typing import List
from db import execute_query
from services.user_service import user_exists


def is_employee_subordinate(employee_tag: str, supervisor_tag: str) -> bool:
    """Проверяет подчинённость (дублируется из shift_service — позже вынесем, но сейчас ок)."""
    result = execute_query(
        """
        SELECT 1 FROM employee_supervisor
        WHERE employee_telegram_tag = %s AND supervisor_telegram_tag = %s
        """,
        (employee_tag, supervisor_tag),
        fetch=True
    )
    return bool(result)


def has_overlapping_leave(employee_tag: str, start_date: datetime.date, end_date: datetime.date) -> bool:
    """Проверяет, есть ли пересекающийся отпуск/больничный."""
    result = execute_query(
        """
        SELECT 1 FROM leave_records
        WHERE user_telegram_tag = %s
          AND NOT (end_date < %s OR start_date > %s)
        """,
        (employee_tag, start_date, end_date),
        fetch=True
    )
    return bool(result)


def create_leave(
    employee_tag: str,
    start_date: datetime.date,
    end_date: datetime.date,
    leave_type: str,
    supervisor_tag: str
) -> bool:
    """
    Создаёт запись об отсутствии.
    leave_type: 'vacation', 'sick', 'absent'
    """
    if start_date > end_date:
        return False

    if not user_exists(employee_tag):
        return False

    if not is_employee_subordinate(employee_tag, supervisor_tag):
        return False

    if has_overlapping_leave(employee_tag, start_date, end_date):
        return False

    if leave_type not in ('vacation', 'sick', 'absent'):
        return False

    try:
        execute_query(
            """
            INSERT INTO leave_records (user_telegram_tag, start_date, end_date, type)
            VALUES (%s, %s, %s, %s)
            """,
            (employee_tag, start_date, end_date, leave_type),
            fetch=False
        )
        return True
    except Exception:
        return False


def get_leaves_for_supervisor(supervisor_tag: str) -> List[dict]:
    """Возвращает список отпусков подчинённых."""
    result = execute_query(
        """
        SELECT lr.id, lr.user_telegram_tag, u.full_name, lr.start_date, lr.end_date, lr.type
        FROM leave_records lr
        JOIN users u ON lr.user_telegram_tag = u.telegram_tag
        JOIN employee_supervisor es ON lr.user_telegram_tag = es.employee_telegram_tag
        WHERE es.supervisor_telegram_tag = %s
        ORDER BY lr.start_date DESC
        """,
        (supervisor_tag,),
        fetch=True
    )
    return [
        {
            "id": row[0],
            "tag": row[1],
            "full_name": row[2],
            "start": row[3],
            "end": row[4],
            "type": row[5]
        }
        for row in result
    ]


def cancel_leave(leave_id: int, supervisor_tag: str) -> bool:
    """Отменяет отпуск, только если он принадлежит подчинённому."""
    # Проверяем, что отпуск принадлежит подчинённому
    result = execute_query(
        """
        SELECT es.employee_telegram_tag
        FROM leave_records lr
        JOIN employee_supervisor es ON lr.user_telegram_tag = es.employee_telegram_tag
        WHERE lr.id = %s AND es.supervisor_telegram_tag = %s
        """,
        (leave_id, supervisor_tag),
        fetch=True
    )
    if not result:
        return False

    try:
        execute_query(
            "DELETE FROM leave_records WHERE id = %s",
            (leave_id,),
            fetch=False
        )
        return True
    except Exception:
        return False