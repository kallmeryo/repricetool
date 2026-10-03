import logging
import math
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class Repricer:
    def __init__(self, logger_instance=None):
        self.logger = logger_instance or logger

    def find_sma(self, statistics, mod_rank=None):
        now = datetime.now(timezone.utc)
        has_mod_rank = any("mod_rank" in stat for stat in statistics)

        candidates = []

        for stat in statistics:
            moving_avg = stat.get("moving_avg")

            if moving_avg is None:
                continue

            if has_mod_rank and stat.get("mod_rank") != mod_rank:
                continue

            stat_time = datetime.fromisoformat(stat["datetime"].replace("Z", "+00:00"))

            if stat_time > now:
                continue

            candidates.append((stat_time, moving_avg))

        if not candidates:
            return None

        _, moving_avg = max(candidates, key=lambda x: x[0])
        return moving_avg

    def get_sma(self, statistics, mod_rank=None):
        """Try 48h SMA first, then fall back to 90d."""
        sma = self.find_sma(statistics["48hours"], mod_rank)

        if sma is not None:
            return sma, "48h"

        sma = self.find_sma(statistics["90days"], mod_rank)

        if sma is not None:
            return sma, "90d"

        return None, None

    def calculate_reprice(self, listed_price, sma):
        target_price = math.ceil(sma)
        price_diff = round(abs(listed_price - target_price), 2)

        if price_diff <= 5:
            return None

        return target_price
