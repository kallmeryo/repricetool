import requests
import logging
import threading
import time

API_URL = "https://api.warframe.market/"


class MarketClient:
    REQUEST_INTERVAL = 0.35  # 3 requests per second
    REQUEST_TIMEOUT = 15

    def __init__(self, session: requests.Session):
        """Initialize the MarketClient with a requests session."""
        self.logger = logging.getLogger(__name__)
        self.session = session
        self._last_request_time = 0.0
        self._request_lock = threading.Lock()

    def _request(self, method, url, **kwargs):
        with self._request_lock:
            now = time.monotonic()
            elapsed = now - self._last_request_time

            if elapsed < self.REQUEST_INTERVAL:
                time.sleep(self.REQUEST_INTERVAL - elapsed)

            self._last_request_time = time.monotonic()
            kwargs.setdefault("timeout", self.REQUEST_TIMEOUT)
            return self.session.request(method, url, **kwargs)

    def get_items(self):
        """
        Fetch the list of items from the Warframe Market API.
        """
        try:
            response = self._request("GET", f"{API_URL}v2/items")
            data = response.json().get("data", [])

            if not isinstance(data, list):
                self.logger.error("Unexpected items response")
                return []

            self.logger.info("Fetched %d items", len(data))
            return data

        except (requests.RequestException, ValueError) as e:
            self.logger.error("Error fetching items: %s", e)
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
            response = self._request(
                "PUT",
                f"{API_URL}v2/orders/{order_id}",
                json={"platinum": price},
            )
            response.raise_for_status()
            data = response.json()

            self.logger.info(
                "Updated order %s to %d platinum",
                order_id,
                price,
            )

            return data

        except (requests.RequestException, ValueError) as e:
            self.logger.error(
                "Error updating order %s: %s",
                order_id,
                e,
            )
            return None

    def get_my_order(self):
        """
        Fetch the user's orders from the Warframe Market API and store them in the database.

        Returns:
            list: A list of user orders.
        Requires:
            - The user must be logged in to the Warframe Market API.
        """
        try:
            response = self._request(
                "GET",
                f"{API_URL}v2/orders/my",
            )
            response.raise_for_status()

            data = response.json()

            if isinstance(data, list):
                orders = data
            elif isinstance(data, dict):
                orders = data.get("data", [])
            else:
                orders = []

            if not isinstance(orders, list):
                self.logger.error("Unexpected orders response")
                return []

            self.logger.info("Fetched %d orders", len(orders))
            return orders

        except (requests.RequestException, ValueError) as e:
            self.logger.error("Error fetching orders: %s", e)
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
            response = self._request(
                "GET",
                f"{API_URL}v2/items/{item_slug}/statistics",
            )
            response.raise_for_status()
            data = response.json()
            self.logger.info("Fetched statistics for item %s", item_slug)
            return data.get("data", [])
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

            response = self._request(
                "POST",
                f"{API_URL}v1/auth/signin",
                json=payload,
                headers=headers,
                timeout=15,
            )
            response.raise_for_status()

            data = response.json()
            user = data["payload"]["user"]

            ingame_name = user["ingame_name"]
            jwt_token = response.cookies.get("JWT")
            self.logger.info("Logged in as %s", ingame_name)

            if not jwt_token:
                self.logger.error(
                    "Login response did not include an Authorization header"
                )
                return False

            self.session.headers.update(
                {
                    "Authorization": f"Bearer {jwt_token}",
                    "platform": "pc",
                    "language": "en",
                }
            )
            return True

        except (requests.RequestException, ValueError, KeyError, TypeError) as e:
            self.logger.error("Error logging in to Warframe Market API: %s", e)
            return False
