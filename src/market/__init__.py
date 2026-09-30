import requests
import logging

API_URL = "https://api.warframe.market/"
class MarketClient:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def get_items(self):
        try:
            request = requests.get(f"{API_URL}v2/items")
            response = request.json()
            self.logger.info("Fetched %d items from Warframe Market API", len(response["data"]))
            return response["data"]
        except requests.exceptions.RequestException as e:
            self.logger.error("Error fetching items from Warframe Market API: %s", e)
            return []

    def update_listing(self, order_id, price):
        """
        Update the price of a specific order on the Warframe Market API.

        Args:
            order_id (str): The ID of the order to update.
            price (int): The new price for the order.

        Returns:
            dict: A dictionary containing the response from the API.
        """
        try:
            payload = {"platinum": price}
            request = requests.put(f"{API_URL}v2/orders/{order_id}", json=payload)
            response = request.json()
            self.logger.info("Updated order %s with new price %d", order_id, price)
            return response
        except requests.exceptions.RequestException as e:
            self.logger.error("Error updating order %s: %s", order_id, e)
            return {"error": str(e)}

    def get_my_order(self):
        """
        Fetch the user's orders from the Warframe Market API and store them in the database.
        
        Returns:
            list: A list of user orders.
        Requires:
            - The user must be logged in to the Warframe Market API.
        """
        try:
            request = requests.get(f"{API_URL}v2/orders/my")
            response = request.json()
            self.logger.info("Fetched %d orders from Warframe Market API", len(response["data"]))
            return response.get("data", [])
        except requests.exceptions.RequestException as e:
            self.logger.error("Error fetching user orders: %s", e)
            return []

    def get_item_statistics(self, item_slug):
        """
        Fetch the statistics for a specific item from the Warframe Market API.

        Args:
            item_slug (str): The slug of the item for which to fetch statistics.

        Returns:
            dict: A dictionary containing the item's statistics.
        """
        try:
            request = requests.get(f"{API_URL}v2/items/{item_slug}/statistics")
            response = request.json()
            self.logger.info("Fetched statistics for item %s", item_slug)
            return response.get("data", [])
        except requests.exceptions.RequestException as e:
            self.logger.error("Error fetching statistics for item %s: %s", item_slug, e)
            return []