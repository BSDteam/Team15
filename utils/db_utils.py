# utils/db_utils.py
from config import bd_conn

def execute_query(query, params=None):
    """Выполняет SQL-запрос и возвращает результат"""
    cur = bd_conn.cursor()
    try:
        if params:
            cur.execute(query, params)
        else:
            cur.execute(query)

        if query.strip().upper().startswith("SELECT"):
            result = cur.fetchall()
        else:
            result = cur.rowcount
            bd_conn.commit()
        return result
    except Exception as e:
        bd_conn.rollback()
        raise e
    finally:
        cur.close()

def fetch_user_by_tag(tag):
    """Получает данные сотрудника по @tag"""
    query = "SELECT full_name FROM users WHERE telegram_tag = %s"
    result = execute_query(query, (tag,))
    return result[0] if result else None

def fetch_leaves_by_tag(tag):
    """Получает список отпусков сотрудника"""
    query = """
        SELECT id, start_date, end_date, type
        FROM leave_records
        WHERE user_telegram_tag = %s
        ORDER BY start_date DESC
    """
    return execute_query(query, (tag,))

def create_leave_record(tag, start_date, end_date):
    """Создаёт запись об отпуске и обновляет статус сотрудника"""
    cur = bd_conn.cursor()
    try:
        cur.execute("""
            INSERT INTO leave_records (user_telegram_tag, start_date, end_date, type)
            VALUES (%s, %s, %s, 'vacation')
        """, (tag, start_date, end_date))

        cur.execute("""
            UPDATE users SET status = 'on_vacation'
            WHERE telegram_tag = %s
        """, (tag,))
        bd_conn.commit()
        return True
    except Exception as e:
        bd_conn.rollback()
        raise e
    finally:
        cur.close()

def cancel_leave_record(leave_id, tag):
    """Удаляет запись об отпуске и обновляет статус сотрудника"""
    cur = bd_conn.cursor()
    try:
        cur.execute("""
            DELETE FROM leave_records
            WHERE id = %s AND user_telegram_tag = %s
        """, (leave_id, tag))
        deleted = cur.rowcount

        if deleted > 0:
            cur.execute("""
                UPDATE users SET status = 'available'
                WHERE telegram_tag = %s
            """, (tag,))
            bd_conn.commit()
            return True
        return False
    except Exception as e:
        bd_conn.rollback()
        raise e
    finally:
        cur.close()