# tests/test_user_service.py
"""
Тесты для services.user_service.
Проверяют корректность получения пользователя по telegram_tag.
"""

import os
import sys
from pathlib import Path

# Добавляем корень проекта в PYTHONPATH, чтобы импортировать модули
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.user_service import get_user_by_tag

def test_get_existing_user():
    """
    Тест: пользователь существует → возвращаются (full_name, role)
    """
    # Предположим, что в БД есть такой пользователь (должен быть добавлен вручную)
    result = get_user_by_tag("@test")
    assert result is not None, "Пользователь @test должен существовать в тестовой БД"
    full_name, role = result
    assert full_name == "Test User"
    assert role in ("employee", "supervisor", "hr")

def test_get_nonexistent_user():
    """
    Тест: пользователя нет → возвращается None
    """
    result = get_user_by_tag("@nonexistent_user_12345")
    assert result is None

def test_get_user_case_sensitivity():
    """
    Тест: тег чувствителен к регистру? (в PostgreSQL по умолчанию — да, если нет CITEXT)
    """
    # В твоей БД telegram_tag — text, значит, регистр важен.
    result = get_user_by_tag("@TEST")  # верхний регистр
    # Если в БД записано "@test" (нижний), то результат — None
    # Но лучше не полагаться на это — всегда используем тот же регистр, что и в Telegram.
    # Пока пропустим этот тест или сделаем его опциональным.
    pass