# db.py
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "shop.db"


def get_connection():
    return sqlite3.connect(DB_PATH)


def init_db():
    conn = get_connection()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS orders (
            order_id INTEGER PRIMARY KEY,
            product_id INTEGER NOT NULL,
            product_name TEXT NOT NULL,
            amount INTEGER NOT NULL,
            customer TEXT NOT NULL,
            phone TEXT NOT NULL,
            address TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
        )
        """
    )
    conn.commit()
    conn.close()


def insert_order(product_id: int, product_name: str, amount: int, customer: str, phone: str, address: str) -> int:
    """یک سفارش جدید در دیتابیس ثبت می‌کند و شماره پیگیری (order_id) را برمی‌گرداند."""
    conn = get_connection()
    cursor = conn.execute("SELECT COALESCE(MAX(order_id), 1000) + 1 FROM orders")
    order_id = cursor.fetchone()[0]
    conn.execute(
        """
        INSERT INTO orders (order_id, product_id, product_name, amount, customer, phone, address)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (order_id, product_id, product_name, amount, customer, phone, address),
    )
    conn.commit()
    conn.close()
    return order_id


def get_all_orders() -> list[dict]:
    """تمام سفارش‌ها را از دیتابیس برای نمایش در پنل ادمین می‌خواند."""
    conn = get_connection()
    cursor = conn.execute(
        "SELECT order_id, product_name, customer, phone, amount FROM orders ORDER BY order_id DESC"
    )
    rows = cursor.fetchall()
    conn.close()
    return [
        {"order_id": r[0], "product_name": r[1], "customer": r[2], "phone": r[3], "amount": r[4]}
        for r in rows
    ]


# جدول در همان لحظه ایمپورت شدن ماژول ساخته می‌شود (در صورت عدم وجود)
init_db()
