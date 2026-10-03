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

    def get_item(self, item_id):
        """
        Get an item's name and slug by its ID.

        Args:
            item_id (str): The ID of the item.

        Returns:
            tuple[str, str] | None:
                (name, slug), or None if the item doesn't exist.
        """
        with sqlite3.connect(self.path) as con:
            self.logger.debug("Looking up item %s", item_id)

            row = con.execute(
                """
                SELECT name, slug
                FROM items
                WHERE id = ?
                """,
                (item_id,),
            ).fetchone()

            return row if row else None

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
