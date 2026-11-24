"""SQLite storage for products, receipt selections and orders."""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "shop.db"


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with get_conn() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                price INTEGER NOT NULL,
                file_id TEXT NOT NULL,
                active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );
            CREATE TABLE IF NOT EXISTS selections (
                user_id INTEGER PRIMARY KEY,
                product_id INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                username TEXT,
                product_id INTEGER NOT NULL,
                receipt_file_id TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );
            """
        )


def add_product(name: str, price: int, file_id: str) -> int:
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO products (name, price, file_id) VALUES (?, ?, ?)",
            (name, price, file_id),
        )
        return cur.lastrowid


def list_products(active_only: bool = True) -> list:
    sql = "SELECT * FROM products"
    if active_only:
        sql += " WHERE active = 1"
    sql += " ORDER BY id"
    with get_conn() as conn:
        return conn.execute(sql).fetchall()


def get_product(product_id: int):
    with get_conn() as conn:
        return conn.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()


def deactivate_product(product_id: int) -> bool:
    with get_conn() as conn:
        cur = conn.execute("UPDATE products SET active = 0 WHERE id = ?", (product_id,))
        return cur.rowcount > 0


def set_selection(user_id: int, product_id: int) -> None:
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO selections (user_id, product_id) VALUES (?, ?) "
            "ON CONFLICT(user_id) DO UPDATE SET product_id = excluded.product_id",
            (user_id, product_id),
        )


def get_selection(user_id: int):
    with get_conn() as conn:
        row = conn.execute(
            "SELECT product_id FROM selections WHERE user_id = ?", (user_id,)
        ).fetchone()
        return row["product_id"] if row else None


def clear_selection(user_id: int) -> None:
    with get_conn() as conn:
        conn.execute("DELETE FROM selections WHERE user_id = ?", (user_id,))


def create_order(user_id: int, username: str, product_id: int, receipt_file_id: str) -> int:
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO orders (user_id, username, product_id, receipt_file_id) "
            "VALUES (?, ?, ?, ?)",
            (user_id, username, product_id, receipt_file_id),
        )
        return cur.lastrowid


def get_order(order_id: int):
    with get_conn() as conn:
        return conn.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()


def set_order_status(order_id: int, status: str) -> None:
    with get_conn() as conn:
        conn.execute("UPDATE orders SET status = ? WHERE id = ?", (status, order_id))


def pending_orders() -> list:
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM orders WHERE status = 'pending' ORDER BY id"
        ).fetchall()


def stats() -> dict:
    with get_conn() as conn:
        row = conn.execute(
            """
            SELECT
                COUNT(*) AS total,
                SUM(CASE WHEN status = 'approved' THEN 1 ELSE 0 END) AS approved,
                SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) AS pending
            FROM orders
            """
        ).fetchone()
        revenue = conn.execute(
            "SELECT COALESCE(SUM(p.price), 0) AS revenue "
            "FROM orders o JOIN products p ON p.id = o.product_id "
            "WHERE o.status = 'approved'"
        ).fetchone()["revenue"]
        return {
            "total": row["total"] or 0,
            "approved": row["approved"] or 0,
            "pending": row["pending"] or 0,
            "revenue": revenue or 0,
        }
