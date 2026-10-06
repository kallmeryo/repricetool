import argparse
import logging
import os
from pathlib import Path

import requests

from src.notifier import DiscordNotifier
from src.database import Database
from src.logger import setup_logging
from src.market import MarketClient
from src.priceEngine import Repricer

setup_logging()

logger = logging.getLogger(__name__)
db_path = "data/database.db"  # Path to the SQLite database file
Path(db_path).parent.mkdir(parents=True, exist_ok=True)
USER_EMAIL = os.getenv("USER_EMAIL")
USER_PASSWORD = os.getenv("USER_PASSWORD")
USER_AGENT = os.getenv("USER_AGENT")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
repricer = Repricer(logger)


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
    logger.info("Starting Warframe Market repricing")
    discord = DiscordNotifier(WEBHOOK_URL)
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
        logger.info("update complete.")
    else:
        if client.login(USER_EMAIL, USER_PASSWORD):
            logger.info("Fetching user orders")
            user_orders = client.get_my_order()

            if user_orders is None:
                logger.error("Could not fetch user orders; aborting repricing")
                return

            repricing_queue = []
            updated_orders = 0

            for order in user_orders:
                order_id = order.get("id")
                item_id = order.get("itemId")
                listed_rank = order.get("rank")
                listed_price = order.get("platinum")
                item = db.get_item(item_id)
                item_name, item_slug = item
                stat = client.get_item_statistics(item_slug, item_name)

                if stat is None:
                    logger.info("%s: statistics unavailable, skipping", item_name)
                    continue

                latest_sma, sma_source = repricer.get_sma(stat, listed_rank)

                if latest_sma is None:
                    logger.info("%s: no valid SMA found for %s", item_name, item_slug)
                    continue

                logger.info(
                    "%s: Listed price: %s, SMA: %s (%s)",
                    item_name,
                    listed_price,
                    latest_sma,
                    sma_source,
                )

                new_price = repricer.calculate_reprice(listed_price, latest_sma)
                if new_price is None:
                    continue

                logger.info(
                    "%s: %dp -> %dp | SMA %.2f | diff %.2f",
                    item_name,
                    listed_price,
                    new_price,
                    latest_sma,
                    round(abs(listed_price - latest_sma), 2),
                )

                repricing_queue.append(
                    {
                        "order_id": order_id,
                        "item_name": item_name,
                        "old_price": listed_price,
                        "price": new_price,
                    }
                )
                logger.info("%s added to queue for update", item_name)

            if repricing_queue:
                logger.info("Processing repricing queue")
                for order in repricing_queue:
                    success = client.update_listing(
                        order_id=order["order_id"],
                        price=order["price"],
                        item_name=order["item_name"],
                    )

                    if success:
                        updated_orders += 1
            else:
                logger.info("Repricing queue is empty")

        message = (
            f"```- Orders checked: {len(user_orders)}\n"
            f"- Orders queued: {len(repricing_queue)}\n"
            f"- Orders updated: {updated_orders}```\n\n"
        )

        if repricing_queue:
            message += "**Price changes:**\n"

            for order in repricing_queue:
                message += f"```{order['item_name']}: {order['old_price']}p → {order['price']}p\n```"
        else:
            message += "No price changes needed.\n"

        discord.send(message)

        logger.info("Repricing complete")


if __name__ == "__main__":
    main()
