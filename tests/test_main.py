from contextlib import ExitStack
import unittest
from unittest.mock import patch

import main


class MainTests(unittest.TestCase):
    def _run_main_with_login(self, logged_in, orders=None):
        with ExitStack() as stack:
            market_client_class = stack.enter_context(patch("main.MarketClient"))
            stack.enter_context(patch("main.Database"))
            notifier_class = stack.enter_context(patch("main.DiscordNotifier"))
            stack.enter_context(patch("main.logger"))

            client = market_client_class.return_value
            client.login.return_value = logged_in
            client.get_my_order.return_value = orders
            notifier = notifier_class.return_value

            result = main.main([])

        return result, client, notifier

    def test_login_failure_notifies_and_aborts_before_fetching_orders(self):
        result, client, notifier = self._run_main_with_login(False)

        self.assertEqual(result, 1)
        client.get_my_order.assert_not_called()
        notifier.send.assert_called_once_with(
            "Warframe Market repricing aborted: login failed. "
            "Check service logs and API availability."
        )

    def test_successful_login_keeps_existing_empty_orders_summary(self):
        result, client, notifier = self._run_main_with_login(True, [])

        self.assertIsNone(result)
        client.get_my_order.assert_called_once_with()
        notifier.send.assert_called_once_with(
            "- Orders checked: 0\n"
            "- Orders queued: 0\n"
            "- Orders updated: 0\n"
            "No price changes needed.\n"
        )


if __name__ == "__main__":
    unittest.main()
