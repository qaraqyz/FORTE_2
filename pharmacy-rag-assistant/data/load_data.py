import sys
import os
import pandas as pd
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from database.connection import get_connection

def load_csv_to_db(csv_path):
    print(f"Загрузка данных из {csv_path}...")

    df = pd.read_csv(csv_path)
    print(f"Прочитано {len(df)} строк")

    conn = get_connection()
    cur = conn.cursor()

    try:
        print("Очистка таблицы sales...")
        cur.execute("TRUNCATE TABLE sales RESTART IDENTITY;")

        print("Загрузка данных в таблицу...")
        inserted = 0

        for idx, row in df.iterrows():
            cur.execute("""
                INSERT INTO sales (date, region, pharmacy, category, product,
                                   units_sold, price, cost_price, revenue, profit)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                row['date'], row['region'], row['pharmacy'], row['category'],
                row['product'], row['units_sold'], row['price'], row['cost_price'],
                row['revenue'], row['profit']
            ))
            inserted += 1

            if inserted % 1000 == 0:
                print(f"Загружено {inserted} строк...")

        conn.commit()
        print(f"Успешно загружено {inserted} строк!")

        cur.execute("SELECT COUNT(*) as count FROM sales;")
        count = cur.fetchone()[0]
        print(f"\nВсего записей в таблице: {count}")

        cur.execute("SELECT MIN(date) as min_date, MAX(date) as max_date FROM sales;")
        dates = cur.fetchone()
        print(f"Период данных: {dates[0]} - {dates[1]}")

        cur.execute("SELECT COUNT(DISTINCT region) as regions FROM sales;")
        regions = cur.fetchone()[0]
        print(f"Количество регионов: {regions}")

        cur.execute("SELECT COUNT(DISTINCT pharmacy) as pharmacies FROM sales;")
        pharmacies = cur.fetchone()[0]
        print(f"Количество аптек: {pharmacies}")

        cur.execute("SELECT COUNT(DISTINCT product) as products FROM sales;")
        products = cur.fetchone()[0]
        print(f"Количество продуктов: {products}")

    except Exception as e:
        conn.rollback()
        print(f"Ошибка при загрузке данных: {e}")
        raise
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    csv_file = "/Users/laurashamykhanova/Desktop/Forte/sales_data.csv" #здесь надо будет поменять вам на свой, если будете запускать

    if not os.path.exists(csv_file):
        print(f"Файл {csv_file} не найден!")
        sys.exit(1)

    load_csv_to_db(csv_file)
