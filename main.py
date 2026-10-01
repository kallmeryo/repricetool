import argparse
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
USER_AGENT = os.getenv("USER_AGENT")


def parse_args(args=None):
    parser = argparse.ArgumentParser(
        description="Run the Warframe Market repricing bot"
    )
    parser.add_argument(
        "command",
        nargs="?",
        choices=("update-items",),
        help="manually refresh the local item catalogue",
    )
    return parser.parse_args(args)


def update_items(client, db):
    items = client.get_items()

    # Save the fetched items to the database
    logger.info("Saving %d items to the database", len(items))
    for item in items:
        db.insert_item(
            id=item.get("id"),
            name=item.get("i18n", {}).get("en", {}).get("name"),
            slug=item.get("slug"),
            max_rank=item.get("maxRank"),
        )
    logger.info("Stage complete: syncronized %d market items", len(items))


def main(args=None):
    logger.info("Starting Warframe Market repricing bot")
    parsed_args = parse_args(args)
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": USER_AGENT,
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
    )

    client = MarketClient(session)
    db = Database(db_path)

    if parsed_args.command == "update-items":
        update_items(client, db)
    else:
        if client.login(USER_EMAIL, USER_PASSWORD):

            # Fetch user orders from the API and save them to the database
            logger.info("Fetching user orders")
            user_orders = client.get_my_order()
            for order in user_orders:
                db.insert_order(**order)

    logger.info("Bot finished execution")


if __name__ == "__main__":
    main()
