import logging
from pathlib import Path

from src.logger import setup_logging
from src.market import MarketClient
from src.database import Database

setup_logging()

logger = logging.getLogger(__name__)
db_path = "data/database.db"  # Path to the SQLite database file
Path(db_path).parent.mkdir(parents=True, exist_ok=True)


def main():
    logger.info("Starting Warframe Market repricing bot")

    client = MarketClient()
    db = Database(db_path)

    items = client.get_items()
    logger.info("Fetched %d items from Warframe Market API", len(items))
    for item in items:
        db.insert_item(
            id=item.get("id"),
            name=item.get("i18n", {}).get("en", {}).get("name"),
            slug=item.get("slug"),
            max_rank=item.get("maxRank"),
        )
    logger.info("Stage complete: syncronized %d market items", len(items))

    logger.info("Bot finished execution")


if __name__ == "__main__":
    main()