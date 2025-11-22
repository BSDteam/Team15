import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery
from config import bd_conn

# Создаём отдельный роутер для этого функционала
employee_status_router = Router()


@employee_status_router.callback_query(F.data == "search_employees")
async def view_employees_status(callback: CallbackQuery):
    supervisor_tag = "@" + (callback.from_user.username or str(callback.from_user.id))

    cur = bd_conn.cursor()
    try:
        # Проверяем роль
        cur.execute("SELECT role FROM users WHERE telegram_tag = %s", (supervisor_tag,))
        user = cur.fetchone()
        if not user or user[0] != 'supervisor':
            await callback.answer("❌ У вас нет прав на просмотр сотрудников.", show_alert=True)
            return

        # Получаем подчинённых
        cur.execute("""
            SELECT u.full_name, u.status, u.telegram_tag, u.id_telegram
            FROM employee_supervisor es
            JOIN users u ON u.telegram_tag = es.employee_telegram_tag
            WHERE es.supervisor_telegram_tag = %s
            ORDER BY u.full_name
        """, (supervisor_tag,))
        employees = cur.fetchall()

        if not employees:
            text = "У вас пока нет подчинённых сотрудников."
        else:
            status_icons = {
                'on_shift': '🟢 На смене',
                'on_vacation': '🏖️ В отпуске',
                'available': '🟡 Доступен'
            }
            text = "📋 Ваши сотрудники:\n\n"
            for full_name, status in employees:
                text += f"• {full_name} — {status_icons.get(status, status)}\n"

        await callback.answer()  # убираем "часики"
        await callback.message.answer(text)

    except Exception as e:
        logging.exception("Ошибка при просмотре статусов сотрудников")
        await callback.answer("❌ Произошла ошибка при загрузке данных.", show_alert=True)
    finally:
        cur.close()