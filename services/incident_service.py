# services/incident_service.py
"""
Сервис для работы с инцидентами.
Использует user_service для получения данных о пользователях.
"""

from datetime import datetime, timezone
from db import execute_query
from services.user_service import (
    get_user_role,
    get_telegram_id_by_tag,
    user_exists
)


def get_supervisor_for_employee(employee_tag: str) -> str | None:
    """
    Возвращает telegram_tag мастера для сотрудника.
    """
    result = execute_query(
        """
        SELECT supervisor_telegram_tag
        FROM employee_supervisor
        WHERE employee_telegram_tag = %s
        """,
        (employee_tag,),
        fetch=True
    )
    return result[0][0] if result else None


def get_employees_of_supervisor(supervisor_tag: str) -> list[str]:
    """
    Возвращает список telegram_tag подчинённых.
    """
    result = execute_query(
        """
        SELECT employee_telegram_tag
        FROM employee_supervisor
        WHERE supervisor_telegram_tag = %s
        """,
        (supervisor_tag,),
        fetch=True
    )
    return [row[0] for row in result] if result else []

def create_incident(description: str, reporter_tag: str) -> bool:
    """
    Создаёт инцидент в таблице events.
    Возвращает True при успехе, False при ошибке.
    """
    if not user_exists(reporter_tag):
        return False

    try:
        execute_query(
            """
            INSERT INTO events (description, reporter_telegram_tag, created_at)
            VALUES (%s, %s, %s)
            """,
            (description.strip(), reporter_tag, datetime.now(timezone.utc)),
            fetch=False  # ← не пытаемся читать результат
        )
        return True
    except Exception:
        return False

def log_notification(sender_tag: str, recipient_tag: str, message: str) -> bool:
    """
    Сохраняет уведомление в таблицу notifications.
    """
    try:
        execute_query(
            """
            INSERT INTO notifications (sender_telegram_tag, recipient_telegram_tag, message)
            VALUES (%s, %s, %s)
            """,
            (sender_tag, recipient_tag, message)
        )
        return True
    except Exception:
        return False


def determine_recipients(reporter_tag: str) -> list[str]:
    """
    Определяет получателей уведомления:
    - сотрудник → мастер
    - мастер → подчинённые
    """
    role = get_user_role(reporter_tag)
    if not role:
        return []

    if role == "employee":
        supervisor = get_supervisor_for_employee(reporter_tag)
        return [supervisor] if supervisor else []
    elif role == "supervisor":
        return get_employees_of_supervisor(reporter_tag)
    else:
        return []  # HR и др. — не рассылаем

def get_recent_incidents_for_supervisor(supervisor_tag: str, limit: int = 6) -> list[dict]:
    """
    Возвращает последние инциденты от мастера и его подчинённых.
    """
    # Получаем теги подчинённых
    subordinate_tags = get_employees_of_supervisor(supervisor_tag)
    all_tags = [supervisor_tag] + subordinate_tags

    if not all_tags:
        return []

    # Формируем placeholders для SQL
    placeholders = ','.join(['%s'] * len(all_tags))
    query = f"""
        SELECT e.description, e.created_at, u.full_name, u.telegram_tag
        FROM events e
        JOIN users u ON e.reporter_telegram_tag = u.telegram_tag
        WHERE e.reporter_telegram_tag IN ({placeholders})
        ORDER BY e.created_at DESC
        LIMIT %s
    """
    result = execute_query(query, (*all_tags, limit), fetch=True)
    return [
        {
            "description": row[0],
            "created_at": row[1],
            "full_name": row[2],
            "telegram_tag": row[3]
        }
        for row in result
    ]


def get_incidents_by_date_for_supervisor(supervisor_tag: str, target_date: datetime.date) -> list[dict]:
    """
    Возвращает инциденты за конкретную дату от мастера и подчинённых.
    """
    subordinate_tags = get_employees_of_supervisor(supervisor_tag)
    all_tags = [supervisor_tag] + subordinate_tags

    if not all_tags:
        return []

    placeholders = ','.join(['%s'] * len(all_tags))
    query = f"""
        SELECT e.description, e.created_at, u.full_name, u.telegram_tag
        FROM events e
        JOIN users u ON e.reporter_telegram_tag = u.telegram_tag
        WHERE e.reporter_telegram_tag IN ({placeholders})
          AND e.created_at::date = %s
        ORDER BY e.created_at DESC
    """
    result = execute_query(query, (*all_tags, target_date), fetch=True)
    return [
        {
            "description": row[0],
            "created_at": row[1],
            "full_name": row[2],
            "telegram_tag": row[3]
        }
        for row in result
    ]