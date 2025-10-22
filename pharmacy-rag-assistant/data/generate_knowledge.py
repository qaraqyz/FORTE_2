import sys
import os
from pathlib import Path
import json

sys.path.append(str(Path(__file__).parent.parent))

from openai import OpenAI
from database.connection import get_connection
from dotenv import load_dotenv

load_dotenv()


def generate_knowledge_from_sales():
    conn = get_connection()
    cur = conn.cursor()

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    try:
        print("Очистка таблицы knowledge_base...")
        cur.execute("TRUNCATE TABLE knowledge_base RESTART IDENTITY;")

        print(" Генерация знаний о продуктах...")
        cur.execute("""
            SELECT
                product,
                category,
                COUNT(*) as total_sales,
                SUM(units_sold) as total_units,
                SUM(revenue) as total_revenue,
                AVG(price) as avg_price
            FROM sales
            GROUP BY product, category
            ORDER BY total_revenue DESC
        """)

        products = cur.fetchall()
        for product in products:
            content = f"""Продукт: {product[0]}
Категория: {product[1]}
Всего продаж: {product[2]}
Продано единиц: {product[3]}
Общая выручка: {product[4]:.2f} тг
Средняя цена: {product[5]:.2f} тг"""

            metadata = {
                "type": "product",
                "product": product[0],
                "category": product[1],
                "total_revenue": float(product[4])
            }

            embedding = create_embedding(client, content)

            cur.execute("""
                INSERT INTO knowledge_base (content, content_type, metadata, embedding)
                VALUES (%s, %s, %s, %s)
            """, (content, "product", json.dumps(metadata), embedding))

        print(f"Добавлено {len(products)} продуктов")

        print("Генерация знаний о регионах...")
        cur.execute("""
            SELECT
                region,
                COUNT(DISTINCT pharmacy) as num_pharmacies,
                COUNT(*) as total_sales,
                SUM(revenue) as total_revenue,
                SUM(profit) as total_profit
            FROM sales
            GROUP BY region
            ORDER BY total_revenue DESC
        """)

        regions = cur.fetchall()
        for region in regions:
            content = f"""Регион: {region[0]}
Количество аптек: {region[1]}
Всего продаж: {region[2]}
Общая выручка: {region[3]:.2f} тг
Общая прибыль: {region[4]:.2f} тг"""

            metadata = {
                "type": "region",
                "region": region[0],
                "num_pharmacies": region[1],
                "total_revenue": float(region[3])
            }

            embedding = create_embedding(client, content)

            cur.execute("""
                INSERT INTO knowledge_base (content, content_type, metadata, embedding)
                VALUES (%s, %s, %s, %s)
            """, (content, "region", json.dumps(metadata), embedding))

        print(f"Добавлено {len(regions)} регионов")

        print("\nГенерация знаний о категориях...")
        cur.execute("""
            SELECT
                category,
                COUNT(DISTINCT product) as num_products,
                SUM(units_sold) as total_units,
                SUM(revenue) as total_revenue,
                AVG(price) as avg_price
            FROM sales
            GROUP BY category
            ORDER BY total_revenue DESC
        """)

        categories = cur.fetchall()
        for category in categories:
            content = f"""Категория: {category[0]}
Количество продуктов: {category[1]}
Продано единиц: {category[2]}
Общая выручка: {category[3]:.2f} тг
Средняя цена: {category[4]:.2f} тг"""

            metadata = {
                "type": "category",
                "category": category[0],
                "num_products": category[1],
                "total_revenue": float(category[3])
            }

            embedding = create_embedding(client, content)

            cur.execute("""
                INSERT INTO knowledge_base (content, content_type, metadata, embedding)
                VALUES (%s, %s, %s, %s)
            """, (content, "category", json.dumps(metadata), embedding))

        print(f" Добавлено {len(categories)} категорий")

        cur.execute("""
            SELECT
                pharmacy,
                region,
                COUNT(*) as total_sales,
                SUM(revenue) as total_revenue,
                SUM(profit) as total_profit
            FROM sales
            GROUP BY pharmacy, region
            ORDER BY total_revenue DESC
        """)

        pharmacies = cur.fetchall()
        for pharmacy in pharmacies:
            content = f"""Аптека: {pharmacy[0]}
Регион: {pharmacy[1]}
Всего продаж: {pharmacy[2]}
Общая выручка: {pharmacy[3]:.2f} тг
Общая прибыль: {pharmacy[4]:.2f} тг"""

            metadata = {
                "type": "pharmacy",
                "pharmacy": pharmacy[0],
                "region": pharmacy[1],
                "total_revenue": float(pharmacy[3])
            }

            embedding = create_embedding(client, content)

            cur.execute("""
                INSERT INTO knowledge_base (content, content_type, metadata, embedding)
                VALUES (%s, %s, %s, %s)
            """, (content, "pharmacy", json.dumps(metadata), embedding))

        print(f"Добавлено {len(pharmacies)} аптек")

        conn.commit()

        # Статистика
        cur.execute("SELECT COUNT(*) FROM knowledge_base")
        total = cur.fetchone()[0]

        print(f" База знаний успешно создана!")
        print(f" Всего записей: {total}")

    except Exception as e:
        conn.rollback()
        print(f" Ошибка: {e}")
        raise
    finally:
        cur.close()
        conn.close()


def create_embedding(client, text):
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return response.data[0].embedding


if __name__ == "__main__":
    print("Генерация базы знаний для RAG системы\n")
    generate_knowledge_from_sales()
