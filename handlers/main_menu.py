# handlers/main_menu.py
"""
Хендлер главного меню Telegram-бота.
Отвечает за обработку команды /start и отображение персонализированного интерфейса
в зависимости от роли пользователя (сотрудник, начальник, HR).
"""

from aiogram import Router, types, F
from aiogram.filters import Command
from services.user_service import get_user_by_tag, update_user_telegram_id

# Импортируем функции для генерации клавиатур.
# В aiogram 3.x рекомендуется создавать клавиатуры через функции,
# чтобы избежать побочных эффектов и упростить тестирование.
from keyboards import (
    main_menu_employee,  # Клавиатура для обычного сотрудника
    main_menu_manager,  # Клавиатура для начальника (supervisor)
    admin_main_kb  # Клавиатура для отдела кадров (HR)
)

# Создаём роутер — контейнер для хендлеров.
# Все хендлеры в этом файле будут зарегистрированы под этим роутером.
router = Router()


@router.message(Command("start"))
async def cmd_start(message: types.Message):
    """
    Асинхронный хендлер, срабатывающий при получении команды /start.

    Логика:
    1. Проверяет, задан ли у пользователя username в Telegram.
    2. Формирует telegram_tag вида "@username".
    3. Ищет пользователя в БД по этому тегу.
    4. Если не найден — сообщает об ошибке.
    5. Если найден — отображает приветствие и соответствующее меню.
    """

    # Получаем username из объекта пользователя Telegram.
    # Если пользователь скрыл username — он будет None.
    username = message.from_user.username

    # Защита от случая, когда username не задан.
    if not username:
        await message.answer(
            "❌ У вас не задан username в Telegram.\n"
            "Пожалуйста, укажите его в настройках и попробуйте снова."
        )
        return  # Прерываем выполнение — дальше не идём

    # Формируем telegram_tag в том виде, как он хранится в БД (с символом @).
    # Например: "@ivan" → именно так он записан в users.telegram_tag.
    telegram_tag = f"@{username}"

    # Обращаемся к сервису (бизнес-логике), чтобы получить данные пользователя.
    # Сервис скрывает детали работы с БД и возвращает только нужное.
    user = get_user_by_tag(telegram_tag)

    # Если пользователь не зарегистрирован в системе — сообщаем об этом.
    # Это ключевое требование: чёткое сообщение для незарегистрированных.
    if not user:
        await message.answer("Обратитесь к отделу кадров, вас нет в системе.")
        return

    # ✅ Обновляем telegram_id, если он не задан (id = 0)
    telegram_id = message.from_user.id
    update_user_telegram_id(telegram_tag, telegram_id)

    # Распаковываем данные: full_name и внутренняя роль (employee/supervisor/hr)
    full_name, role = user

    # Преобразуем внутреннее название роли в человекочитаемый формат
    # для отображения в сообщении. Это не влияет на логику — только на UI.
    role_display = {
        "employee": "Сотрудник",
        "supervisor": "Начальник",
        "hr": "Кадровый отдел"
    }.get(role, "Неизвестная роль")  # fallback на случай некорректной роли

    # В зависимости от внутренней роли (не от отображаемой!)
    # выбираем нужную функцию клавиатуры и вызываем её.
    # Каждая функция возвращает готовый объект InlineKeyboardMarkup.
    if role == "supervisor":
        keyboard = main_menu_manager()  # Начальник → расширенное меню
    elif role == "hr":
        keyboard = admin_main_kb()  # HR → панель управления
    else:
        # По умолчанию — сотрудник (включая случай неизвестной роли)
        keyboard = main_menu_employee()

    # Отправляем приветственное сообщение с клавиатурой.
    # Используем f-строку для персонализации.
    await message.answer(
        f"Добрый день, {full_name}!\nВаша должность: {role_display}",
        reply_markup=keyboard  # Передаём сгенерированную клавиатуру
    )

@router.callback_query(F.data == "main_refresh")
async def handle_main_refresh(callback: types.CallbackQuery):
    """
    Обновляет главное меню (возвращается на главную).
    """
    telegram_tag = f"@{callback.from_user.username}" if callback.from_user.username else None
    if not telegram_tag:
        await callback.message.edit_text("❌ У вас не задан username.")
        await callback.answer()
        return

    user = get_user_by_tag(telegram_tag)
    if not user:
        await callback.message.edit_text("Обратитесь к отделу кадров, вас нет в системе.")
        await callback.answer()
        return

    full_name, role = user
    role_display = {
        "employee": "Сотрудник",
        "supervisor": "Начальник",
        "hr": "Кадровый отдел"
    }.get(role, "Неизвестная роль")

    if role == "supervisor":
        keyboard = main_menu_manager()
    elif role == "hr":
        keyboard = admin_main_kb()
    else:
        keyboard = main_menu_employee()

    await callback.message.edit_text(
        f"Добрый день, {full_name}!\nВаша должность: {role_display}",
        reply_markup=keyboard
    )
    await callback.answer()