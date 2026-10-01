import requests
import logging

API_URL = "https://api.warframe.market/"
class MarketClient:
    def __init__(self, session:requests.Session):
        self.logger = logging.getLogger(__name__)
        self.session = session

    def get_items(self):
        try:
            request = self.session.get(f"{API_URL}v2/items")
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
            request = self.session.put(f"{API_URL}v2/orders/{order_id}", json=payload)
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
            request = self.session.get(f"{API_URL}v2/orders/my")
            request.raise_for_status()
            response = request.json()
            orders = response if isinstance(response, list) else response.get("data", []) if isinstance(response, dict) else []
            if not isinstance(orders, list):
                self.logger.warning("Unexpected orders payload from Warframe Market API")
                return []
            self.logger.info("Fetched %d orders from Warframe Market API", len(orders))
            return orders
        except (requests.exceptions.RequestException, ValueError) as e:
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
            request = self.session.get(f"{API_URL}v2/items/{item_slug}/statistics")
            response = request.json()
            self.logger.info("Fetched statistics for item %s", item_slug)
            return response.get("data", [])
        except requests.exceptions.RequestException as e:
            self.logger.error("Error fetching statistics for item %s: %s", item_slug, e)
            return []

    def login(self, user_email, user_password):
        """
        Log in to the Warframe Market API using the provided user credentials.

        Args:
            user_email (str): The user's email address.
            user_password (str): The user's password.
        """
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": "JWT",
            "platform": "pc",
            "language": "en",
        }

        payload = {
            "email": user_email,
            "password": user_password,
        }

        try:
            self.logger.info("Attempting to log in to Warframe Market API")
            if not user_email or not user_password:
                self.logger.error("Warframe Market credentials are not configured")
                return False

            response = self.session.post(
                f"{API_URL}v1/auth/signin",
                json=payload,
                headers=headers,
                timeout=15,
            )
            response.raise_for_status()

            data = response.json()
            user = data["payload"]["user"]

            ingame_name = user["ingame_name"]
            jwt_token = response.cookies.get("JWT") or self.session.cookies.get("JWT")

            if not jwt_token:
                self.logger.error("Login response did not include a JWT cookie")
                return False

            self.session.headers.update({
                "Authorization": f"Bearer {jwt_token}",
                "platform": "pc",
                "language": "en",
                "auth_type": "header",
            })
            self.logger.info("Logged in as %s", ingame_name)
            return True

        except (requests.RequestException, ValueError, KeyError, TypeError) as e:
            self.logger.error("Error logging in to Warframe Market API: %s", e)
            return False