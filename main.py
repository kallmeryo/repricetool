import logging
import os
from pathlib import Path

import requests

from src.logger import setup_logging
from src.market import MarketClient
from src.database import Database

setup_logging()

logger = logging.getLogger(__name__)
db_path = "data/database.db"  # Path to the SQLite database file
Path(db_path).parent.mkdir(parents=True, exist_ok=True)
USER_EMAIL = os.getenv("USER_EMAIL")
USER_PASSWORD = os.getenv("USER_PASSWORD")


def main():
    logger.info("Starting Warframe Market repricing bot")
    session = requests.Session()
    session.headers.update({"User-Agent": "Warframe Market Repricing Bot",
                            "Accept": "application/json",
                            "Content-Type": "application/json"})

    client = MarketClient(session)
    db = Database(db_path)

    items = client.get_items()
    logger.info("Fetched %d items from Warframe Market API", len(items))
    for item in items: # Filters items and saves them to the database
        db.insert_item(
            id=item.get("id"),
            name=item.get("i18n", {}).get("en", {}).get("name"),
            slug=item.get("slug"),
            max_rank=item.get("maxRank"),
        )
    logger.info("Stage complete: syncronized %d market items", len(items))

    logger.info("Fetching user orders")
    if client.login(USER_EMAIL, USER_PASSWORD):
        user_orders = client.get_my_order()
        for oders in user_orders:
            db.insert_order(**oders)

    logger.info("Bot finished execution")


if __name__ == "__main__":
    main()