# services/notification_service.py
"""
Сервис отправки уведомлений.
Зависит от aiogram.Bot — специально для этого.
"""

from aiogram import Bot
from db import execute_query

def send_notification(sender_tag: str, recipient_tag: str, message: str) -> bool:
    """

    :param sender_tag:
    :param recipient_tag:
    :param message:
    :return:
    """
    # Сохраняет в таблицу `notifications`
    # Проверка: оба пользователя существуют

def get_last_notifications_for_user(user_tag: str, limit: int = 10) -> list[dict]:
    """

    :param user_tag:
    :param limit:
    :return:
    """
    # Не обязательно для MVP, но полезно