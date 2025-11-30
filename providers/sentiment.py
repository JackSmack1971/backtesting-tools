import requests
from typing import Tuple

class SentimentProvider:
    def __init__(self):
        self.fng_url = "https://api.alternative.me/fng/?limit=1"

    def fetch_fear_greed(self) -> Tuple[int, str]:
        """
        Returns (value, label). e.g. (25, "Extreme Fear").
        Defaults to (50, "Neutral") on error.
        """
        try:
            data = requests.get(self.fng_url, timeout=5).json()
            value = int(data["data"][0]["value"])
            label = data["data"][0]["value_classification"]
            return value, label
        except Exception:
            return 50, "Neutral"
