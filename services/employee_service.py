# services/employee_service.py
"""
Сервис для работы с сотрудниками: поиск, статусы.
"""

from datetime import date
from db import execute_query


def search_employees_by_full_name(query: str) -> list[dict]:
    """
    Ищет сотрудников по частичному совпадению ФИО (регистронезависимо).
    """
    result = execute_query(
        """
        SELECT telegram_tag, full_name, status
        FROM users
        WHERE role = 'employee'
          AND full_name ILIKE %s
        ORDER BY full_name
        """,
        (f"%{query}%",),
        fetch=True
    )
    return [
        {"telegram_tag": row[0], "full_name": row[1], "status": row[2]}
        for row in result
    ]


def get_employee_detailed_status(telegram_tag: str) -> str:
    """
    Возвращает расширенный статус сотрудника:
    - 'В отпуске' / 'На больничном'
    - 'На смене'
    - 'Доступен'
    """
    # Проверяем отпуск/больничный на сегодня
    today = date.today()
    leave = execute_query(
        """
        SELECT type FROM leave_records
        WHERE user_telegram_tag = %s
          AND start_date <= %s
          AND end_date >= %s
        """,
        (telegram_tag, today, today),
        fetch=True
    )
    if leave:
        leave_type = leave[0][0]
        if leave_type == "vacation":
            return "🏖️ В отпуске"
        elif leave_type == "sick":
            return "🤒 На больничном"
        else:
            return "🚫 Отсутствует"

    # Проверяем, назначен ли на смену сегодня
    shift = execute_query(
        """
        SELECT 1 FROM shift_assignments sa
        JOIN shifts s ON sa.shift_id = s.id
        WHERE sa.user_telegram_tag = %s
          AND s.shift_date = %s
        """,
        (telegram_tag, today),
        fetch=True
    )
    if shift:
        return "🔧 На смене"

    return "✅ Доступен"


def get_subordinates_with_status(supervisor_tag: str) -> list[dict]:
    """
    Возвращает список подчинённых с их текущим статусом.
    """
    result = execute_query(
        """
        SELECT u.telegram_tag, u.full_name
        FROM users u
        JOIN employee_supervisor es ON u.telegram_tag = es.employee_telegram_tag
        WHERE es.supervisor_telegram_tag = %s
        ORDER BY u.full_name
        """,
        (supervisor_tag,),
        fetch=True
    )
    subordinates = []
    for row in result:
        tag, name = row
        status = get_employee_detailed_status(tag)
        subordinates.append({"full_name": name, "telegram_tag": tag, "status": status})
    return subordinates


def get_calendar_data(supervisor_tag: str, year: int, month: int) -> dict:
    """
    Возвращает данные для календаря:
    {day: [{"type": "shift", "id": 5, "workshop": 2}, {"type": "leave", "user": "@tag", "reason": "vacation"}]}
    """
    from calendar import monthrange
    _, last_day = monthrange(year, month)

    # Получаем смены мастера в этом месяце
    shifts = execute_query(
        """
        SELECT id, shift_date, workshop
        FROM shifts
        WHERE tag = %s
          AND EXTRACT(YEAR FROM shift_date) = %s
          AND EXTRACT(MONTH FROM shift_date) = %s
        """,
        (supervisor_tag, year, month),
        fetch=True
    )

    # Получаем отпуска подчинённых в этом месяце
    leaves = execute_query(
        """
        SELECT lr.user_telegram_tag, lr.start_date, lr.end_date, lr.type
        FROM leave_records lr
        JOIN employee_supervisor es ON lr.user_telegram_tag = es.employee_telegram_tag
        WHERE es.supervisor_telegram_tag = %s
          AND lr.end_date >= (%s || '-' || %s || '-01')::date
          AND lr.start_date <= (%s || '-' || %s || '-' || %s)::date
        """,
        (supervisor_tag, year, month, year, month, last_day),
        fetch=True
    )

    # Инициализируем словарь
    calendar = {day: [] for day in range(1, last_day + 1)}

    # Добавляем смены
    for shift_id, shift_date, workshop in shifts:
        day = shift_date.day
        calendar[day].append({
            "type": "shift",
            "id": shift_id,
            "workshop": workshop
        })

    # Добавляем отпуска
    for user_tag, start, end, leave_type in leaves:
        start_day = max(start.day, 1)
        end_day = min(end.day, last_day)
        for day in range(start_day, end_day + 1):
            calendar[day].append({
                "type": "leave",
                "user": user_tag,
                "reason": leave_type
            })

    # Убираем пустые дни
    return {day: events for day, events in calendar.items() if events}