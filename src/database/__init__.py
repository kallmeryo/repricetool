import logging
from pathlib import Path
import sqlite3

logger = logging.getLogger(__name__)


class Database:
    def __init__(self, path):
        """Initialize the Database class and set up the database connection."""
        self.logger = logger
        self.path = path
        self.create_tables()

    def create_tables(self):
        """
        Create the necessary tables in the database if they don't exist.
        """
        with sqlite3.connect(self.path) as con:
            self.logger.info("Creating database tables if needed")
            con.execute("""
                CREATE TABLE IF NOT EXISTS items (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    slug TEXT NOT NULL,
                    max_rank INTEGER DEFAULT NULL
                )
            """)
            con.execute("""
                CREATE TABLE IF NOT EXISTS user_orders (
                    id TEXT PRIMARY KEY,
                    type TEXT NOT NULL,
                    platinum INTEGER NOT NULL,
                    quantity INTEGER NOT NULL,
                    perTrade INTEGER NOT NULL,
                    rank INTEGER,
                    visible INTEGER DEFAULT 0,
                    createdAt TEXT,
                    updatedAt TEXT,
                    itemId TEXT,
                    FOREIGN KEY (itemId) REFERENCES items(id))
                """)
            self.logger.info("Database tables are ready")

    def insert_item(self, id, name, slug, max_rank=None):
        """
        Insert or update an item in the database.
        """
        with sqlite3.connect(self.path) as con:
            self.logger.debug("Saving item %s (%s)", id, name)
            con.execute(
                """
            INSERT INTO items (id, name, slug, max_rank)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                name = excluded.name,
                slug = excluded.slug,
                max_rank = excluded.max_rank
        """,
                (id, name, slug, max_rank),
            )
            self.logger.info("Item %s saved to database", name)

    def insert_order(self, **order):
        """
        Insert or update a user order in the database."""
        with sqlite3.connect(self.path) as con:
            self.logger.debug("Saving order %s", order["id"])
            con.execute(
                """
            INSERT INTO user_orders (
                id,
                type,
                platinum,
                quantity,
                perTrade,
                rank,
                visible,
                createdAt,
                updatedAt,
                itemId
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)

            ON CONFLICT(id) DO UPDATE SET
                type = excluded.type,
                platinum = excluded.platinum,
                quantity = excluded.quantity,
                perTrade = excluded.perTrade,
                rank = excluded.rank,
                visible = excluded.visible,
                createdAt = excluded.createdAt,
                updatedAt = excluded.updatedAt,
                itemId = excluded.itemId
            """,
                (
                    order["id"],
                    order["type"],
                    order["platinum"],
                    order["quantity"],
                    order["perTrade"],
                    order.get("rank"),
                    order["visible"],
                    order["createdAt"],
                    order["updatedAt"],
                    order["itemId"],
                ),
            )

    def get_item_name(self, item_id):
        """
        Get the name of an item by its ID from the database."""
        with sqlite3.connect(self.path) as con:
            row = con.execute(
                """
            SELECT name
            FROM items
            WHERE id = ?
        """,
                (item_id,),
            ).fetchone()

            return row[0] if row else None

    def get_item_slug(self, item_id):
        """
        Get the slug of an item by its ID from the database.
        """
        with sqlite3.connect(self.path) as con:
            self.logger.debug("Looking up slug for item %s", item_id)
            row = con.execute(
                """SELECT slug FROM items WHERE id = ?""",
                (item_id,),
            ).fetchone()

            return row[0] if row else None

    def my_orders(self):
        """
        Load all visible user orders from the database.
        """
        with sqlite3.connect(self.path) as con:
            self.logger.info("Loading saved user orders")
            con.row_factory = sqlite3.Row
            orders = [
                dict(row)
                for row in con.execute(
                    "SELECT * FROM user_orders WHERE visible = 1"
                ).fetchall()
            ]
            self.logger.info("Loaded %d saved user orders", len(orders))
            return orders