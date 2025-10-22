import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from database.connection import execute_query


def execute_sql(sql_query: str) -> list:
    try:
        results = execute_query(sql_query, fetch=True)

        if results:
            return [dict(row) for row in results]
        return []

    except Exception as e:
        raise Exception(f"Ошибка выполнения SQL: {str(e)}")


def validate_sql(sql_query: str) -> bool:
    forbidden_keywords = [
        'DROP', 'DELETE', 'TRUNCATE', 'UPDATE',
        'INSERT', 'ALTER', 'CREATE', 'GRANT', 'REVOKE'
    ]

    sql_upper = sql_query.upper()

    for keyword in forbidden_keywords:
        if keyword in sql_upper:
            return False

    return True

def execute_safe_sql(sql_query: str) -> list:
    if not validate_sql(sql_query):
        raise Exception("Запрос содержит запрещенные операции. Разрешены только SELECT запросы.")

    return execute_sql(sql_query)
