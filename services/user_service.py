# services/user_service.py
"""
Универсальный сервис для работы с пользователями.
Содержит всю логику: получение данных, проверка ролей, существование и т.д.
"""

from db import execute_query


def get_user_by_tag(telegram_tag: str):
    """
    Возвращает (full_name, role) для существующего пользователя.
    Возвращает None, если не найден.
    """
    result = execute_query(
        "SELECT full_name, role FROM users WHERE telegram_tag = %s",
        (telegram_tag,),
        fetch=True
    )
    return result[0] if result else None


def get_user_full(telegram_tag: str):
    """
    Возвращает полные данные: (full_name, role, status, id).
    Возвращает None, если не найден.
    """
    result = execute_query(
        "SELECT full_name, role, status, id FROM users WHERE telegram_tag = %s",
        (telegram_tag,),
        fetch=True
    )
    return result[0] if result else None


def get_user_role(telegram_tag: str) -> str | None:
    """Возвращает роль пользователя или None, если не найден."""
    result = execute_query(
        "SELECT role FROM users WHERE telegram_tag = %s",
        (telegram_tag,),
        fetch=True
    )
    return result[0][0] if result else None


def get_telegram_id_by_tag(telegram_tag: str) -> int | None:
    """
    Возвращает telegram_user_id (id), если он задан (≠ 0).
    """
    result = execute_query(
        "SELECT id FROM users WHERE telegram_tag = %s AND id != 0",
        (telegram_tag,),
        fetch=True
    )
    return result[0][0] if result else None


def is_hr(telegram_tag: str) -> bool:
    """Проверяет, является ли пользователь HR."""
    role = get_user_role(telegram_tag)
    return role == "hr"


def user_exists(telegram_tag: str) -> bool:
    """Проверяет существование пользователя по тегу."""
    return get_user_role(telegram_tag) is not None


# === HR-специфичные функции (остаются здесь, так как это тоже про пользователей) ===

def create_user_in_db(telegram_tag: str, full_name: str, role: str, status: str = "available") -> bool:
    try:
        execute_query(
            """
            INSERT INTO users (telegram_tag, full_name, role, status)
            VALUES (%s, %s, %s, %s)
            """,
            (telegram_tag, full_name, role, status)
        )
        return True
    except Exception:
        return False


def get_all_users() -> list[dict]:
    result = execute_query(
        "SELECT telegram_tag, full_name, role, status FROM users ORDER BY full_name",
        fetch=True
    )
    return [
        {"telegram_tag": row[0], "full_name": row[1], "role": row[2], "status": row[3]}
        for row in result
    ]


def update_user_role(telegram_tag: str, new_role: str) -> bool:
    if not user_exists(telegram_tag):
        return False
    execute_query(
        "UPDATE users SET role = %s WHERE telegram_tag = %s",
        (new_role, telegram_tag),
        fetch=False
    )
    return True


def delete_user_by_tag(telegram_tag: str) -> bool:
    if not user_exists(telegram_tag):
        return False
    execute_query(
        "DELETE FROM users WHERE telegram_tag = %s",
        (telegram_tag,),
        fetch=False
    )
    return True

def update_user_telegram_id(telegram_tag: str, telegram_id: int) -> bool:
    """
    Обновляет telegram_user_id, если он был 0 (то есть не задан).
    Возвращает True, если обновление произошло.
    """
    # Проверяем, что текущий id == 0
    result = execute_query(
        "SELECT id FROM users WHERE telegram_tag = %s AND id = 0",
        (telegram_tag,),
        fetch=True
    )
    if not result:
        return False  # id уже задан или пользователя нет

    try:
        execute_query(
            "UPDATE users SET id = %s WHERE telegram_tag = %s",
            (telegram_id, telegram_tag),
            fetch=False
        )
        return True
    except Exception:
        return False